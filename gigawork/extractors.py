"""
Module for every extractors defined in the project.
"""

from abc import ABC, abstractmethod
from collections import namedtuple
import hashlib
import logging
from os import PathLike
import os
import sys
from typing import List, NamedTuple
import git

from .change_types import ChangeTypes

logger = logging.getLogger(__name__)


class Entry(NamedTuple):
    """A single entry in the dataset."""

    commit_hash: str
    author_name: str
    author_email: str
    committer_name: str
    committer_email: str
    committed_date: str
    authored_date: str
    file_path: str
    file_hash: str
    previous_file_hash: str
    change_type: str


class RenameEntry(NamedTuple):
    """A single entry in the rename dataset."""

    commit: str
    old_name: str
    new_name: str


RepositoryEntry = namedtuple("RepositoryEntry", ("repository",) + Entry._fields)
RepositoryRenameEntry = namedtuple(
    "RepositoryRenameEntry", ("repository",) + RenameEntry._fields
)


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
        if self.save_directory != "":
            os.makedirs(self.save_directory, exist_ok=True)

    def extract(
        self, ref="HEAD", after=None, *args, **kwargs
    ) -> tuple[List[Entry], List[RenameEntry]]:
        entries = []
        rename_entries = []
        if after is not None:
            ref = f"{after}..{ref}"
        # iter parents until `after` if given
        for commit in self.repository.iter_commits(
            ref, self.directory, **{"first-parent": True}
        ):
            self._extract_files(commit, entries, rename_entries)
        return entries, rename_entries

    def _extract_files(
        self,
        commit: git.Commit,
        entries: List[Entry],
        rename_entries: List[RenameEntry],
    ):
        """Extract the workflows from the given commit.

        Args:
            commit (git.Commit): The commit to extract the workflows from.
            previous (Union[None, git.Commit]): The previous commit to compare to.
            If None, compare to the first commit of the repository.
            directory (PathLike): The directory to consider.
            entries (List[Entry]): The list of entries representing the dataset.
            rename_entries (List[RenameEntry]): The list of rename entries representing the
            renaming entries of the dataset.
        """
        # we compare the parent commit to the current commit
        # The order of the diff is important, because we want to know
        # if a file was added or deleted (it might be reversed if we are not cautious)
        # If there is no parent, we check for diff since the beginning
        # of the repository (we are at a initial commit)
        # we only compare with the first parent
        # as we iter_commits with first-parent=True
        parent = commit.parents[0] if len(commit.parents) > 0 else None
        diffs = parent.diff(commit) if parent else commit.diff(git.NULL_TREE)
        for diff in diffs:
            if not diff.a_path.startswith(
                self.directory
            ) and not diff.b_path.startswith(self.directory):
                continue  # a commit might contains diffs for files we do not care about
            try:
                self._process_diff(diff, entries, rename_entries, commit, parent)
            except ValueError:
                logger.error("Could not process diff %s (commit=%s)", str(diff), commit)
                sys.exit(1)

    def _get_blob_parameters(
        self, diff: git.Diff, change_type: ChangeTypes, commit
    ) -> List[tuple]:
        """Returns the parameters to process a blob.

        Args:
            diff (git.Diff): The diff to process.
            change_type (ChangeTypes): The type of change.
            commit (_type_): The commit to which the diff belongs.

        Returns:
            List[tuple]: The parameters to process a blob.
        """
        if change_type == ChangeTypes.RENAMED:
            return (
                *self._get_blob_parameters(diff, ChangeTypes.DELETED, commit),
                *self._get_blob_parameters(diff, ChangeTypes.ADDED, commit),
            )
        if change_type == ChangeTypes.DELETED:
            blob, old_blob, path = diff.a_blob, None, diff.a_path
        elif change_type == ChangeTypes.ADDED:
            blob, old_blob, path = diff.b_blob, None, diff.b_path
        else:
            blob, old_blob, path = diff.b_blob, diff.a_blob, diff.b_path
        if len(commit.parents) == 0:
            change_type = ChangeTypes.ADDED
        return ((blob, old_blob, commit, path, change_type),)

    def _process_diff(
        self,
        diff: git.Diff,
        entries: List[Entry],
        rename_entries: List[RenameEntry],
        commit: git.Commit,
        parent: git.Commit = None,
    ):
        """Process a diff to extract the files and data.

        Args:
            diff (git.Diff): The diff to process.
            entries (List[Entry]): The list of entries representing the dataset.
            rename_entries (List[RenameEntry]): The list of rename entries representing the
            renaming entries of the dataset.
            commit (git.Commit): The commit to which the diff belongs.
            parent (git.Commit, optional): The parent of the commit (if None, will try
            to get it automatically). Defaults to None.
        """
        if parent is None:
            parent = commit.parents[0] if len(commit.parents) > 0 else None
        try:
            change_type = ChangeTypes(diff.change_type)
        except ValueError:
            logger.debug(
                "Could not process diff %s (commit=%s, change_type=%s)",
                str(diff),
                commit,
                diff.change_type,
            )
            return  # we do not care about this diff

        if change_type == ChangeTypes.RENAMED:
            rename_entry = RenameEntry(commit, diff.a_path, diff.b_path)
            rename_entries.append(rename_entry)
        for params in self._get_blob_parameters(diff, change_type, commit):
            entries.append(self._process_blob(*params))

    def _process_blob(
        self,
        blob: git.Blob,
        old_blob: git.Blob,
        commit: git.Commit,
        workflow_path: PathLike,
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
        old_data = old_blob.data_stream.read() if old_blob else None
        _old_hash = hashlib.sha256(old_data).hexdigest() if old_data else ""
        for d, h in ((data, _hash), (old_data, _old_hash)):
            if d is None:
                continue
            path = os.path.join(self.save_directory, h)
            if not os.path.exists(path):
                # if it exists, we already have the workflow
                # (well, we might have a collision, but it is unlikely)
                with open(path, "wb") as file:
                    file.write(d)
        entry = Entry(
            commit.hexsha,
            commit.author.name,
            commit.author.email,
            commit.committer.name,
            commit.committer.email,
            commit.committed_date,
            commit.authored_date,
            workflow_path,
            _hash,
            _old_hash,
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
