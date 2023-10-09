import csv
from typing import List
from extractors import Entry


def write_csv(entries: List[Entry], file: str,
              headers: bool = False):
    with open(file, "w") as f:
        writer = csv.writer(f)
        if headers:
            writer.writerow(Entry._fields)
        writer.writerows(entries)
    