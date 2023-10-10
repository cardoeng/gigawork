"""
Module for every extractors defined in the project.
"""

from abc import ABC, abstractmethod
from collections import namedtuple
import hashlib
import logging
from os import PathLike
import os
from typing import List, NamedTuple
import git

from change_types import ChangeTypes

logger = logging.getLogger(__name__)


class Entry(NamedTuple):
    """A single entry in the dataset."""

    commit: str
    author_name: str
    author_email: str
    commiter_name: str
    commiter_email: str
    date: str
    workflow: str
    workflow_content: str
    change_type: str


RepositoryEntry = namedtuple("RepositoryEntry", ("repository",) + Entry._fields)


class Extractor(ABC):
    """An extractor is used to extract information from a repository."""

    def __init__(self, repository: git.Repo) -> None:
        self.repository = repository

    @abstractmethod
    def extract(self, *args, **kwargs) -> List[Entry]:
        """Extract the information from the repository.

        Returns:
            List[Entry]: The list of entries extracted from the repository.
        """


class FilesExtractor(Extractor):
    """Extract files and Entry from a repository."""

    def __init__(
        self, repository: git.Repo, directory: PathLike, save_directory: PathLike
    ) -> None:
        super().__init__(repository)
        self.save_directory = save_directory
        self.directory = directory
        os.makedirs(self.save_directory, exist_ok=True)

    def extract(self, ref="HEAD", after=None, *args, **kwargs) -> List[Entry]:
        entries = []
        if after is not None:
            ref = f"{after}..{ref}"
        # iter parents until `after` if given
        for commit in self.repository.iter_commits(
            ref, self.directory, **{"first-parent": True}
        ):
            self._extract_files(commit, entries)
        return entries

    def _extract_files(self, commit: git.Commit, entries: List[Entry]):
        """Extract the workflows from the given commit.

        Args:
            commit (git.Commit): The commit to extract the workflows from.
            previous (Union[None, git.Commit]): The previous commit to compare to.
            If None, compare to the first commit of the repository.
            directory (PathLike): The directory to consider.

        Returns:
            List[Entry]: The list of entries extracted from the commit.
        """
        # we compare the parent commit to the current commit
        # The order of the diff is important, because we want to know
        # if a file was added or deleted (it might be reversed if we are not cautious)
        # If there is no parent, we check for diff since the beginning
        # of the repository (we are at a initial commit)
        # we only compare with the first parent
        # as we iter_commits with first-parent=True
        parent = commit.parents[0] if len(commit.parents) > 0 else None
        diffs = parent.diff(commit) if parent else commit.diff(None)
        for diff in diffs:
            if not diff.a_path.startswith(
                self.directory
            ) and not diff.b_path.startswith(self.directory):
                continue
            try:
                self._process_diff(diff, entries, commit, parent)
            except ValueError:
                logger.error("Could not process diff %s (commit=%s)", str(diff), commit)

    def _process_diff(
        self,
        diff: git.Diff,
        entries: List[Entry],
        commit: git.Commit,
        parent: git.Commit = None,
    ):
        """Process a diff to extract the files and data.

        Args:
            diff (git.Diff): The diff to process.
            entries (List[Entry]): The list of entries to add to / the results.
            commit (git.Commit): The commit to which the diff belongs.
            parent (git.Commit, optional): The parent of the commit (if None, will try
            to get it automatically). Defaults to None.
        """
        if parent is None:
            parent = commit.parents[0] if len(commit.parents) > 0 else None
        change_type = ChangeTypes(diff.change_type)
        if change_type in [ChangeTypes.MODIFIED, ChangeTypes.ADDED]:
            entries.append(
                self._process_blob(diff.b_blob, commit, diff.b_path, change_type)
            )
        elif change_type == ChangeTypes.DELETED:
            if parent is None:
                change_type = ChangeTypes.ADDED  # if there is no parent, it was added
                # as we are at the initial commit (we can only add at an initial commit)
            entries.append(
                self._process_blob(diff.a_blob, commit, diff.a_path, change_type)
            )
        elif change_type == ChangeTypes.RENAMED:
            entries.append(
                self._process_blob(
                    diff.a_blob, commit, diff.a_path, ChangeTypes.DELETED
                )
            )
            entries.append(
                self._process_blob(diff.b_blob, commit, diff.b_path, ChangeTypes.ADDED)
            )

    def _process_blob(
        self,
        blob: git.Blob,
        commit: git.Commit,
        path: PathLike,
        change_type: ChangeTypes,
    ) -> Entry:
        """Process a blob to extract the workflow content.

        Args:
            blob (git.Blob): The blob to process.

        Returns:
            str: The hash of the workflow content. (Its name in the save_directory)
        """
        if blob is None:
            raise ValueError("Blob cannot be None")
        data = blob.data_stream.read()
        _hash = hashlib.sha256(data).hexdigest()
        path = os.path.join(self.save_directory, _hash + ".yaml")
        if not os.path.exists(path):
            # if it exists, we already have the workflow
            # (well, we might have a collision, but it is unlikely)
            with open(path, "wb") as file:
                file.write(data)
        entry = Entry(
            commit.hexsha,
            commit.author.name,
            commit.author.email,
            commit.committer.name,
            commit.committer.email,
            commit.committed_date,
            path,
            _hash,
            change_type.value,
        )
        return entry


class WorkflowsExtractor(FilesExtractor):
    """Extract workflows and related Entry from a repository."""

    WORKFLOWS_DIRECTORY = ".github/workflows"

    def __init__(self, repository: git.Repo, save_directory: PathLike) -> None:
        FilesExtractor.__init__(
            self, repository, self.WORKFLOWS_DIRECTORY, save_directory
        )
