"""
Module for every extractors defined in the project.
"""

from abc import ABC, abstractmethod
from collections import namedtuple
from functools import lru_cache
import hashlib
import logging
from os import PathLike
import os
import sys
from typing import List, NamedTuple, Tuple
import git

from .change_types import ChangeTypes
from .workflow_recognition import is_valid_workflow, is_workflow_directory

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
    previous_file_path: str
    file_hash: str
    previous_file_hash: str
    change_type: str
    valid_yaml: bool
    probably_workflow: bool
    valid_workflow: bool


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
        """Init

        Args:
            repository (git.Repo): The Git repository.
            directory (PathLike): The directory in the Git repository to consider.
            save_directory (PathLike): The directory under which the extracted files will be saved.
            None if the files should not be saved.
        """
        super().__init__(repository)
        self.save_directory = save_directory
        self.directory = directory
        if self.save_directory is not None and self.save_directory != "":
            os.makedirs(self.save_directory, exist_ok=True)
        self.entries = []

    def extract(self, ref="HEAD", after=None, *args, **kwargs) -> None:
        if after is not None:
            ref = f"{after}..{ref}"
        # iter parents until `after` if given
        for commit in self.repository.iter_commits(
            ref, self.directory, **{"first-parent": True}
        ):
            self._extract_files(commit)

    def _should_process_diff(self, diff: git.Diff) -> bool:
        """Returns True if the diff should be processed, False otherwise.

        Args:
            diff (git.Diff): The diff to process.

        Returns:
            bool: True if the diff should be processed, False otherwise.
        """
        return diff.a_path.startswith(self.directory) or diff.b_path.startswith(
            self.directory
        )

    def _extract_files(
        self,
        commit: git.Commit,
    ):
        """Extract the workflows from the given commit.

        Args:
            commit (git.Commit): The commit to extract the workflows from.
            previous (Union[None, git.Commit]): The previous commit to compare to.
            If None, compare to the first commit of the repository.
            directory (PathLike): The directory to consider.
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
            if not self._should_process_diff(diff):
                continue  # a commit might contains diffs for files we do not care about
            try:
                self._process_diff(diff, commit, parent)
            except ValueError as e:
                logger.error(
                    "Could not process diff %s (commit=%s)",
                    str(diff),
                    commit,
                    exc_info=True,
                )
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
        # separated as both path is not None in case of deletion and addition
        if change_type == ChangeTypes.DELETED:
            blob, old_blob, path, previous_path = None, diff.a_blob, None, diff.a_path
        elif change_type == ChangeTypes.ADDED:
            blob, old_blob, path, previous_path = diff.b_blob, None, diff.b_path, None
        else:
            blob, old_blob, path, previous_path = (
                diff.b_blob,
                diff.a_blob,
                diff.b_path,
                diff.a_path,
            )
        if len(commit.parents) == 0:
            change_type = ChangeTypes.ADDED
        return ((blob, old_blob, commit, path, previous_path, change_type),)

    def _save_entry(self, entry: Entry):
        self.entries.append(entry)

    def _process_diff(
        self,
        diff: git.Diff,
        commit: git.Commit,
        parent: git.Commit = None,
    ):
        """Process a diff to extract the files and data.

        Args:
            diff (git.Diff): The diff to process.
            entries (List[Entry]): The list of entries representing the dataset.
            commit (git.Commit): The commit to which the diff belongs.
            parent (git.Commit, optional): The parent of the commit (if None, will try
            to get it automatically). Defaults to None.
        """
        if parent is None:
            parent = commit.parents[0] if len(commit.parents) > 0 else None
        try:
            change_type = ChangeTypes(diff.change_type)
        except ValueError as e:
            logger.error(
                "Could not process diff %s (commit=%s, change_type=%s)",
                str(diff),
                commit,
                diff.change_type,
            )
            return  # we do not care about this diff

        for params in self._get_blob_parameters(diff, change_type, commit):
            self._save_entry(self._process_blob(*params))

    def _get_blob_content(self, blob: git.Blob) -> Tuple[str, str]:
        """
        Save the content of a git blob to a file.

        Args:
            blob (git.Blob): The git blob object.

        Returns:
            str: The name under which the file was saved.
        """
        if blob is None:
            return None, None
        data = blob.data_stream.read()
        _hash = hashlib.sha256(data).hexdigest()
        return data, _hash

    def _save_content(self, data: bytes, old_data: bytes, entry: Entry) -> str:
        """
        Save the content of a git blob to a file.

        Args:
            data (bytes): The data to save.
            path (PathLike): The directory where the file will be saved.

        Returns:
            str: The name under which the file was saved.
        """
        if self.save_directory is None:
            return
        for (d, h) in [(data, entry.file_hash), (old_data, entry.previous_file_hash)]:
            if d is None:
                continue
            path = os.path.join(self.save_directory, h)
            if not os.path.exists(path):
                # if it exists, we already have the workflow
                # (well, we might have a collision, but it is unlikely)
                with open(path, "wb") as file:
                    file.write(d)

    def _process_blob(
        self,
        blob: git.Blob,
        old_blob: git.Blob,
        commit: git.Commit,
        workflow_path: PathLike,
        previous_workflow_path: PathLike,
        change_type: ChangeTypes,
    ) -> Entry:
        """Process a blob to extract the workflow content.

        Args:
            blob (git.Blob): The blob to process.

        Returns:
            str: The hash of the workflow content. (Its name in the save_directory)
        """
        data, _hash = self._get_blob_content(blob)
        old_data, _old_hash = self._get_blob_content(old_blob)
        try:
            if data is None:  # deleted file
                s = old_data.decode()
            else:
                s = data.decode()
            is_yaml, is_probable, is_workflow = is_valid_workflow(s)
        except Exception as e:
            logger.warning(
                "Could not decode or validate workflow for %s (commit=%s, change_type=%s)",
                workflow_path,
                commit,
                change_type,
                exc_info=True,
            )
            is_yaml, is_probable, is_workflow = False, False, False
        if change_type == ChangeTypes.RENAMED and _hash != _old_hash:
            change_type = ChangeTypes.MODIFIED
        entry = Entry(
            commit.hexsha,
            commit.author.name,
            commit.author.email,
            commit.committer.name,
            commit.committer.email,
            commit.committed_date,
            commit.authored_date,
            workflow_path,
            previous_workflow_path,
            _hash,
            _old_hash,
            change_type.value,
            is_yaml,
            is_probable,
            is_workflow,
        )
        self._save_content(data, old_data, entry)
        return entry


class PathSeparatorFilesExtractor(FilesExtractor):
    def __init__(
        self,
        repository: git.Repo,
        directory: PathLike,
        save_directories: List[PathLike],
        separators: List[callable],
    ) -> None:
        """
        Init

        Args:
            repository (git.Repo): The Git repository.
            directory (PathLike): The directory in the Git repository to consider.
            save_directories (PathLike): The directory under which the extracted files will be saved.
            separators (List[callable]): A list of callables representing the separators.
            The separators should be ordered by priority. The separators should represent
            every possible case. Otherwise, the file will be extracted, but not entry will
            be saved.
        """
        # the file should be saved, but we decide where
        super().__init__(repository, directory, None)
        self.save_directories = save_directories
        for sd in self.save_directories:
            if sd is not None:
                os.makedirs(sd, exist_ok=True)
        self.separators = separators
        self.entries = [[] for _ in range(len(self.separators))]

    @lru_cache(maxsize=10)
    def _get_save_index(self, entry: Entry) -> int:
        """
        Returns the index of the separator that matches the given path.

        Args:
            entry (Entry): The entry to match.

        Returns:
            int: The index of the matching separator, or None if no separator matches.
        """
        for i, sep in enumerate(self.separators):
            if sep(entry):
                return i
        return None

    def _save_entry(self, entry: Entry):
        """
        Saves the entry based on the separator index.

        Args:
            entry (Entry): The entry to save.
        """
        index = self._get_save_index(entry)
        if index is not None:
            self.entries[index].append(entry)

    def _save_content(self, data: bytes, old_data: bytes, entry: Entry) -> str:
        i = self._get_save_index(entry)
        if i is None:
            return
        sd = self.save_directories[i]
        if sd is None:
            return

        for (d, h) in [(data, entry.file_hash), (old_data, entry.previous_file_hash)]:
            if d is None:
                continue
            path = os.path.join(sd, h)
            if not os.path.exists(path):
                # if it exists, we already have the workflow
                # (well, we might have a collision, but it is unlikely)
                with open(path, "wb") as file:
                    file.write(d)


class WorkflowsExtractor(PathSeparatorFilesExtractor):
    """Extract workflows and related Entry from a repository."""

    WORKFLOWS_DIRECTORY = ".github/workflows"

    def __init__(
        self,
        repository: git.Repo,
        save_directory: PathLike,
        save_auxiliaries: bool = False,
        auxiliary_save_directory: PathLike = None,
    ) -> None:
        if auxiliary_save_directory is None:
            auxiliary_save_directory = save_directory
        separators = [
            lambda x: not self._is_auxiliary(x),
        ]
        save_directories = [save_directory]
        if save_auxiliaries:
            separators.append(lambda _: True)  # save everything
            # that does not match the first separator
            save_directories.append(auxiliary_save_directory)
        PathSeparatorFilesExtractor.__init__(
            self,
            repository,
            self.WORKFLOWS_DIRECTORY,
            save_directories,
            separators,
        )

    def _is_auxiliary(self, entry: Entry) -> bool:
        """Returns True if the path is an auxiliary file, False otherwise.

        Args:
            entry (Entry): The entry to check.

        Returns:
            bool: True if the path is an auxiliary file, False otherwise.
        """
        p = entry.file_path if entry.file_path is not None else entry.previous_file_path
        return not (
            is_workflow_directory(p)
            and (entry.valid_workflow or entry.probably_workflow)
        )

    def get_entries(self) -> List[Entry]:
        """Returns the entries.

        Returns:
            List[Entry]: The entries.
        """
        return self.entries[0]

    def get_auxiliary_entries(self) -> List[Entry]:
        """Returns the auxiliary entries.

        Returns:
            List[Entry]: The auxiliary entries.
        """
        if len(self.entries) > 1:
            return self.entries[1]
        else:
            return None
