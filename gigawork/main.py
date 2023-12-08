import os
import subprocess
import sys
import logging
import tempfile
import click
import git
from .extractors import WorkflowsExtractor
from .repository import clone_repository, read_repository, update_repository
from . import utils

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--ref",
    "--branch",
    "-r",
    default="HEAD",
    help="The most recent commit reference (i.e., commit SHA or TAG) to be considered for the extraction",
    type=str,
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
    type=str,
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
    "--rename-output",
    "-ro",
    help="The output CSV file where information related to the renaming of workflows will be stored. "
    "By default, this informations will not be stored.",
    type=click.Path(exists=False, file_okay=True, dir_okay=False, writable=True),
)
@click.option(
    "--repository-name",
    "-n",
    help="Add a column `repository_name` to the output file where each value will be equal to the provided parameter.",
    type=str,
)
@click.option(
    "--headers",
    "-h",
    help="Create a header row for the CSV output file.",
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
    rename_output,
    repository_name,
    headers,
    repository,
):
    """Extract the GitHub Actions workflows from a single Git repo.
    The Git repository can be local or distant. In the latter case, it will be pulled
    locally and deleted unless specified otherwise.

    Example of usage:
    gha_datasets myRepository -n myRepositoryName -s directory -o output.csv --headers
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
    entries, rename_entries = extractor.extract(ref, after)

    if len(entries) > 0:
        if output:
            parent = os.path.dirname(output)
            if parent != "":
                os.makedirs(parent, exist_ok=True)
            with open(output, "a", encoding="utf-8") as file:
                utils.write_csv(
                    entries, file, entries[0].__class__, headers, repository_name
                )
        else:
            utils.write_csv(
                entries, sys.stdout, entries[0].__class__, headers, repository_name
            )

    if rename_output and len(rename_entries) > 0:
        parent = os.path.dirname(rename_output)
        if parent != "":
            os.makedirs(parent, exist_ok=True)
        with open(rename_output, "a", encoding="utf-8") as file:
            utils.write_csv(
                rename_entries,
                file,
                rename_entries[0].__class__,
                headers,
                repository_name,
            )

    # print(ref, save_repository, update, after, workflows, output, repository_name, headers, repository, sep="\n")

    # cleanup
    if tmp_directory:
        tmp_directory.cleanup()


if __name__ == "__main__":
    main()
