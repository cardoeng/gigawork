import re
from typing import Tuple
from importlib.resources import files
from jsonschema import validate
from .utils import read_yaml

WORKFLOW_REGEX = re.compile(r"^\.github/workflows/[^/]*\.(yml|yaml)$")
KEY_PRESENT = r"[\"']?%s[\"']?\s*:"

schema_text = files("gigawork").joinpath("github-workflow.json").read_text()
SCHEMA = read_yaml(schema_text)


def _is_probable_workflow(content):
    """Check if the content is probably a workflow file
    (i.e. it contains the `on` and `jobs` keys.)

    Args:
        content (str): The content of the file

    Returns:
        bool: Whether the file is probably a workflow file
    """
    # there are a lot of things allowed by the workflow syntax
    # spaces, comments, quotes, etc.
    for key in ["on", "jobs"]:
        if re.search(KEY_PRESENT % key, content, re.MULTILINE) is None:
            return False
    return True


def _is_valid_workflow(content) -> Tuple[bool, bool]:
    """Check if the content is a valid workflow file

    Args:
        content (str): The content of the file

    Returns:
        Tuple[bool, bool]: Whether the file is valid YAML and a valid workflow file
    """
    try:
        data = read_yaml(content)
        try:
            validate(data, SCHEMA)
            return True, True
        except Exception:
            return True, False
    except Exception:
        return False, False


def is_valid_workflow(content) -> Tuple[bool, bool, bool]:
    """Check if the content is a valid workflow file.

    Args:
        content (str): The content of the file

    Returns:
        Tuple[bool, bool, bool]: Whether the file is valid YAML,
        probably a workflow file, and a valid workflow files
    """
    try:
        is_probable = _is_probable_workflow(content)
    except Exception:
        is_probable = False
    try:
        is_yaml, is_workflow = _is_valid_workflow(content)
    except Exception:
        is_yaml, is_workflow = False, False
    return is_yaml, is_probable, is_workflow


def is_workflow_path(path):
    if path is None:
        return False
    return bool(WORKFLOW_REGEX.match(path))


def is_workflow_directory(path):
    if type(path) != str:
        return False
    return path.startswith(".github/workflows/")
