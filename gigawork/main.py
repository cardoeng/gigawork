import os
import sys
import logging
import tempfile
import click
import git
from .param_types import GitReference
from .extractors import WorkflowsExtractor
from .repository import clone_repository, read_repository, update_repository
from . import utils

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# See https://click.palletsprojects.com/en/8.1.x/documentation/#help-texts
CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option(
    "--ref",
    "--branch",
    "-r",
    default="HEAD",
    help="The most recent commit reference (i.e., commit SHA or TAG) to be considered for the extraction.",
    type=GitReference(),
)
@click.option(
    "--save-repository",
    "-s",
    help="Save the repository to the given directory in case `REPOSITORY` was distant.",
    type=click.Path(exists=False, file_okay=False, dir_okay=True, writable=True),
)
@click.option(
    "--update", "-u", help="Fetch the repository at the given path.", is_flag=True
)
@click.option(
    "--after",
    "-a",
    help="Only consider commits after the given commit reference (i.e., commit SHA or TAG).",
    type=GitReference(),
)
@click.option(
    "--workflows",
    "-w",
    help="The directory where the extracted GitHub Actions workflow files will be stored.",
    default="workflows",
    type=click.Path(exists=False, file_okay=False, dir_okay=True, writable=True),
)
@click.option(
    "--output",
    "-o",
    help="The output CSV file where information related to the dataset will be stored. "
    "By default, the information will written to the standard output.",
    type=click.Path(exists=False, file_okay=True, dir_okay=False, writable=True),
)
@click.option(
    "--repository-name",
    "-n",
    help="Add a column `repository` to the output file where each value will be equal to the provided parameter.",
    type=str,
)
@click.option(
    "--no-headers",
    help="Remove the header row from the CSV output file.",
    is_flag=True,
)
@click.argument(
    "repository",
    type=str,
)
def main(
    ref,
    save_repository,
    update,
    after,
    workflows,
    output,
    repository_name,
    no_headers,
    repository,
):
    """Extract the GitHub Actions workflow files from a single Git repository `REPOSITORY`.
    The extraction is done by traversing the Git history of the repository starting
    from the reference given to `-r` and going back in time respecting the first-parent rule until
    the first commit (or the reference given to `-a`) is reached.
    The Git repository can be local or distant. In the latter case, it will be pulled
    locally and deleted unless specified otherwise.
    Every extracted workflow file will be stored in the directory given to `-w` (or the
    directory `workflows` if not specified).
    The metadata related to the extracted workflows will be written in the CSV file given to `-o`,
    or in the standard output if not specified. The metadata related to the renaming of workflows
    will be stored in the CSV file given to `-ro`, or not stored if not specified.

    Example of usage:
    gigawork myRepository -n myRepositoryName -s directory -o output.csv --no-headers
    """
    tmp_directory = None  # the temporary directory if one is created
    repo = None  # the repository

    # clone the repository if it does not exist
    try:
        if not os.path.exists(repository):
            if not save_repository:
                tmp_directory = tempfile.TemporaryDirectory(dir=".")
                save_repository = tmp_directory.name
            repo = clone_repository(repository, save_repository)
        else:
            repo = read_repository(repository)
    except (git.exc.GitCommandError, ValueError) as exception:
        logger.error("Could not read repository at '%s'", repository)
        logger.debug(exception)
        sys.exit(1)

    # update it if requested
    if update is True:
        try:
            update_repository(repo)
        except git.exc.GitCommandError as exception:
            logger.error(
                "Could not update repository at '%s'. Keeping the current version...",
                repository,
            )
            logger.debug(exception)

    extractor = WorkflowsExtractor(repo, workflows)
    entries = extractor.extract(ref, after)

    if len(entries) > 0:
        if output:
            parent = os.path.dirname(output)
            if parent != "":
                os.makedirs(parent, exist_ok=True)
            with open(output, "a", encoding="utf-8") as file:
                utils.write_csv(
                    entries, file, entries[0].__class__, not no_headers, repository_name
                )
        else:
            utils.write_csv(
                entries,
                sys.stdout,
                entries[0].__class__,
                not no_headers,
                repository_name,
            )

    # cleanup
    if tmp_directory:
        tmp_directory.cleanup()


if __name__ == "__main__":
    main()
