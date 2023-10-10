from abc import ABC, abstractmethod
import hashlib
from os import PathLike
import os
from typing import List, NamedTuple
import git

from change_types import ChangeTypes


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


class RepositoryEntry(Entry):
    """A single entry in the dataset with the repository name."""

    repository: str


class Extractor(ABC):
    def __init__(self, repository: git.Repo) -> None:
        self.repository = repository

    @abstractmethod
    def extract(self, *args, **kwargs) -> List[Entry]:
        pass


class WorkflowExtractor(Extractor):
    WORKFLOWS_DIRECTORY = ".github/workflows"

    def __init__(self, repository: git.Repo, save_directory: PathLike) -> None:
        super().__init__(repository)
        self.save_directory = save_directory
        os.makedirs(self.save_directory, exist_ok=True)

    def extract(self, ref="HEAD", after=None) -> List[Entry]:
        entries = []
        if after is not None:
            ref = f"{ref}..{after}"
        # iter parents until `after` if given
        for commit in self.repository.iter_commits(
            ref, self.WORKFLOWS_DIRECTORY, **{"first-parent": True}
        ):
            self._extract_files(commit, self.WORKFLOWS_DIRECTORY, entries)
        return entries

    def _extract_files(
        self, commit: git.Commit, directory: PathLike, entries: List[Entry]
    ):
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
        if len(commit.parents) > 1:
            print(commit)
        # we only compare with the first parent
        # as we iter_commits with first-parent=True
        parent = commit.parents[0] if len(commit.parents) > 0 else None
        diffs = parent.diff(commit) if parent else commit.diff(None)
        for diff in diffs:
            if not diff.a_path.startswith(directory) and not diff.b_path.startswith(
                directory
            ):
                continue

            ct = ChangeTypes(diff.change_type)
            if ct in [ChangeTypes.MODIFIED, ChangeTypes.ADDED]:
                entries.append(self._process_blob(diff.b_blob, commit, diff.b_path, ct))
            elif ct == ChangeTypes.DELETED:
                if parent is None:
                    ct = ChangeTypes.ADDED  # if there is no parent, it was added
                    # as we are at the initial commit (we can only add at an initial commit)
                entries.append(self._process_blob(diff.a_blob, commit, diff.a_path, ct))
            elif ct == ChangeTypes.RENAMED:
                entries.append(
                    self._process_blob(
                        diff.a_blob, commit, diff.a_path, ChangeTypes.DELETED
                    )
                )
                entries.append(
                    self._process_blob(
                        diff.b_blob, commit, diff.b_path, ChangeTypes.ADDED
                    )
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
            return None
        file = blob.data_stream.read()
        h = hashlib.sha256(file).hexdigest()
        with open(os.path.join(self.save_directory, h + ".yaml"), "wb") as f:
            f.write(file)
        entry = Entry(
            commit.hexsha,
            commit.author.name,
            commit.author.email,
            commit.committer.name,
            commit.committer.email,
            commit.committed_date,
            path,
            h,
            change_type.value,
        )
        return entry


if __name__ == "__main__":
    r = git.Repo("./calculator-cucumber")
    extractor = WorkflowExtractor(r, "workflows")
    extractor.extract()
