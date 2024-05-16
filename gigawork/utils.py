import csv
import json
from io import TextIOWrapper
from typing import Iterable

from typing import Union
from ruamel.yaml import YAML


def write_csv(
    entries: Iterable,
    file: TextIOWrapper,
    entry_class,
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
        entries = map(lambda e: (repository_name, *e), entries)
    writer = csv.writer(file)
    if headers:
        h = list(entry_class._fields)
        if repository_name:
            h.insert(0, "repository")
        writer.writerow(h)
    writer.writerows(entries)


def write_json(entries: Iterable, file: TextIOWrapper, repository_name: str = None):
    """Write the given entries to the given file.

    Args:
        entries (List[Entry]): The entries to write.
        file (TextIOWrapper): The file to write to.
        repository_name (str, optional): The name of the repository to add to the entries.
        Defaults to None.
    """
    # map each entry to a dictionary
    entries = map(lambda e: e._asdict(), entries)
    if repository_name:
        entries = map(lambda e: {"repository": repository_name, **e}, entries)
    # write the entries to the file
    json.dump(list(entries), file, indent=4)


def get_yaml_object() -> YAML:
    """Get a yaml object for reading.

    Returns:
        YAML: The yaml object.
    """
    return YAML(typ="safe", pure=True)


def read_yaml(data) -> Union[dict, list, str, int]:
    """
    Read a yaml file and return the corresponding object.

    Args:
        data (str): The yaml data.

    Returns:
        Union[dict, list, str, int]: The corresponding object.
    """
    yaml = get_yaml_object()
    data_dict = yaml.load(data)
    return data_dict
