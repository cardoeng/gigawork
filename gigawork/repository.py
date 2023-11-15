from pathlib import Path
from typing import Union
import logging
import os
import git

logger = logging.getLogger(__name__)


def read_repository(path: str) -> Union[git.Repo, None]:
    """Read a repository at the given path.

    Args:
        path (str): The path to the repository.

    Returns:
        git.Repo: The repository if it exists, None otherwise.
    """
    logger.debug("Reading repository at '%s'", path)
    if os.path.exists(path):
        return git.Repo(path)


def clone_repository(url: str, directory: os.PathLike = None) -> Union[git.Repo, None]:
    """Clone a repository at the given url in the given directory.

    Args:
        url (str): The url of the repository.
        directory (os.PathLike, optional): The directory in which the repository should be clones.
        If None, a directory will be created with the base name of the given url.
        Defaults to None.

    Returns:
        git.Repo: The repository if it was cloned successfully, None otherwise.
    """
    logger.info("Cloning repository at '%s'", url)
    if directory is None:
        directory = os.path.basename(url)
        os.makedirs(directory, exist_ok=True)
    if os.path.exists(directory) and any(Path(directory).iterdir()):
        logger.error("Directory '%s' is not empty. Stopping...", directory)
        raise ValueError(f"Directory '{directory}' is not empty.")

    try:
        repo = git.Repo.clone_from(url, directory, **{"no-checkout": True})
    except git.exc.GitCommandError:
        logger.error("Could not clone repository at '%s'", url)
        raise
    return repo


def update_repository(repo: git.Repo):
    """Update the given repository.

    Args:
        r (git.Repo): The repository to update.
    """
    logger.info("Updating repository at '%s'", repo.working_dir)
    repo.git.fetch()
