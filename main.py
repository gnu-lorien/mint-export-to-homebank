from collections import defaultdict

import click
import csv
from dataclasses import dataclass, field
import datetime

from slugify import slugify


@dataclass
class HomebankRow:
    date: datetime.date = field(default_factory=datetime.date.today)
    payment: int = 0
    info: str = ""
    payee: str = ""
    memo: str = ""
    amount: float = 0.0
    category: str = ""
    tags: [] = field(default_factory=list)

    def for_csv(self):
        return [self.date.strftime("%Y-%m-%d"),
                str(self.payment),
                self.info,
                self.payee,
                self.memo,
                str(self.amount),
                self.category,
                " ".join(self.tags)
                ]


class Converter:
    def __init__(self, source, destination):
        self._src = source
        self._dst = destination

    def decide_payment(self, row):
        return 0

    def convert(self):
        with open(self._src, 'r') as mintfile:
            homebank_rows = defaultdict(list)
            homebank_accounts = set()
            homebank_payees = set()
            mintreader = csv.reader(mintfile, delimiter=',', quotechar="\"")
            first = True
            for mintrow in mintreader:
                if first:
                    first = False
                    continue
                homebank_row = HomebankRow()
                homebank_row.date = datetime.datetime.strptime(mintrow[0], "%m/%d/%Y").date()
                homebank_row.payment = self.decide_payment(mintrow)
                homebank_row.info = mintrow[2]
                homebank_row.memo = mintrow[-1]
                homebank_row.payee = mintrow[1]
                homebank_payees.add(homebank_row.payee)
                homebank_row.category = mintrow[5]
                homebank_row.tags = mintrow[-2]
                if mintrow[4] == "debit":
                    homebank_row.amount = float(mintrow[3]) * -1
                else:
                    homebank_row.amount = float(mintrow[3])
                homebank_rows[mintrow[-3]].append(homebank_row)
        for account_name in homebank_rows:
            slugged_account = slugify(account_name)
            homebank_account_name_file = self._dst + f"_homebank_{slugged_account}.csv"
            with open(homebank_account_name_file, 'w') as homebankfile:
                homebankwriter = csv.writer(homebankfile, delimiter=";", quotechar='\"')
                for row in homebank_rows[account_name]:
                    homebankwriter.writerow(row.for_csv())


@click.command()
@click.argument('source')
@click.argument("destinationbasename")
def main(source, destinationbasename):
    """Convert source Mint CSV file to a destination Homebank base name to be used for generating csv files"""
    Converter(source, destinationbasename).convert()


if __name__ == "__main__":
    main()