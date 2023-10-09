from abc import ABC, abstractmethod
import hashlib
from os import PathLike, makedirs
import os
from typing import List, NamedTuple
import git

from change_types import ChangeTypes

class Entry(NamedTuple):
    """A single entry in the dataset.
    """
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
    """A single entry in the dataset with the repository name.
    """
    repository: str

class Extractor(ABC):
    
    def __init__(self, repository: git.Repo) -> None:
        self.repository = repository
    
    @abstractmethod
    def extract(self, *args, **kwargs) -> List[Entry]:
        pass
    
class WorkflowExtractor(Extractor):
    WORKFLOWS_DIRECTORY = ".github/workflows"
    
    def __init__(self, repository: git.Repo) -> None:
        super().__init__(repository)
    
    def extract(self, workflows_save: PathLike,
                ref="HEAD", after=None) -> List[Entry]:
        entries = []
        if after is not None:
            ref = f"{ref}..{after}"
        # iter parents until `after` if given
        for commit in self.repository.iter_commits(ref, self.WORKFLOWS_DIRECTORY, 
                                                   **{"first-parent": True}):
            entries.extend(self._extract_files(commit, self.WORKFLOWS_DIRECTORY, workflows_save))
        return entries

    @staticmethod
    def _extract_files(commit: git.Commit, directory: PathLike,
                       save_directory: PathLike) -> List[Entry]:
        makedirs(save_directory, exist_ok=True)
        entries = []
        for diff in commit.diff(commit.parents[0]):
            if not diff.a_path.startswith(directory) and not diff.b_path.startswith(directory):
                continue
            
            blob = None
            ct = ChangeTypes(diff.change_type)
            if ct in [ChangeTypes.MODIFIED, ChangeTypes.ADDED]:
                blob = diff.b_blob
            elif ct in [ChangeTypes.DELETED]:
                blob = diff.a_blob
            if blob:
                file = blob.data_stream.read()
                h = hashlib.sha256(file).hexdigest()
                print(h)
                with open(os.path.join(save_directory, h + ".yaml"), "wb") as f:
                    f.write(file)
                entry = Entry(commit.hexsha,
                            commit.author.name,
                            commit.author.email,
                            commit.committer.name,
                            commit.committer.email,
                            commit.committed_date,
                            diff.a_path,
                            h,
                            diff.change_type)
                entries.append(entry)
        return entries
        
        
        
        