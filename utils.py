import csv
from io import TextIOWrapper
from typing import Iterable, List
from extractors import Entry, RepositoryEntry


def write_csv(
    entries: Iterable[Entry],
    file: TextIOWrapper,
    headers: bool = False,
    repository_name: str = None,
):
    """Write the given entries to the given file.

    Args:
        entries (List[Entry]): The entries to write.
        file (TextIOWrapper): The file to write to.
        headers (bool, optional): Whether to write a header row.
        Defaults to False.
        repository_name (str, optional): The name of the repository to add to the entries.
        Defaults to None.
    """
    if repository_name:
        entries = map(lambda e: RepositoryEntry(repository_name, *e), entries)
    writer = csv.writer(file)
    if headers:
        writer.writerow(
            Entry._fields if not repository_name else RepositoryEntry._fields
        )
    writer.writerows(entries)
