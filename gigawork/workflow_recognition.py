import re
from typing import Tuple
from jsonschema import validate
from .utils import read_yaml

WORKFLOW_REGEX = re.compile(r"^\.github/workflows/[^/]*\.(yml|yaml)$")
with open("github-workflow.json", "r") as f:
    SCHEMA = read_yaml(f.read())


def _is_probable_workflow(content):
    ON_KEY_PRESENT = r"^on:"
    JOBS_KEY_PRESENT = r"^jobs:\s*(#.*)?$"
    for key in [ON_KEY_PRESENT, JOBS_KEY_PRESENT]:
        if not re.search(key, content, re.MULTILINE):
            return False
    return True


def _is_valid_workflow(content) -> Tuple[bool, bool]:
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
    try:
        is_probable = _is_probable_workflow(content)
    except Exception:
        is_probable = False
    try:
        is_yaml, is_workflow = _is_valid_workflow(content)
    except Exception:
        is_yaml, is_workflow = False, False
    return is_yaml, is_probable, is_workflow


def is_workflow_directory(path):
    return True if WORKFLOW_REGEX.match(path) else False
