from typing import Union
import git
import logging
import os

logger = logging.getLogger(__name__)

def read_repository(path: str) -> Union[git.Repo, None]:
    """Read a repository at the given path.

    Args:
        path (str): The path to the repository.

    Returns:
        git.Repo: The repository if it exists, None otherwise.
    """
    logger.debug(f"Reading repository at '{path}'")
    if os.path.exists(path):
        return git.Repo(path)
    else:
        return None
        
def clone_repository(url: str, d: os.PathLike = None) -> Union[git.Repo, None]:
    """Clone a repository at the given url in the given directory.

    Args:
        url (str): The url of the repository.
        d (os.PathLike, optional): The directory in which the repository should be clones. 
        Defaults to None.

    Returns:
        git.Repo: The repository if it was cloned successfully, None otherwise.
    """
    logger.debug(f"Cloning repository at '{url}'")
    try:
        r = git.Repo.clone_from(url, d, **{"no-checkout": True})
    except git.exc.GitCommandError:
        logger.error(f"Could not clone repository at '{url}'")
        return None
    return r

def update_repository(r: git.Repo):
    """Update the given repository.

    Args:
        r (git.Repo): The repository to update.
    """
    logger.debug(f"Updating repository at '{r.working_dir}'")
    r.git.fetch()
    # try:
    #     origin = r.remote(name="origin")
    # except ValueError:
    #     logger.error("No remote named 'origin' found for the repository at '{r.working_dir}'")
    #     return None
    # origin.fetch()
    