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


@click.group()
def main():
    """A tool for extracting GitHub Actions workflows."""
    pass


@main.command()
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
def single(
    ref,
    save_repository,
    update,
    after,
    workflows,
    output,
    repository_name,
    headers,
    repository,
):
    """Extract the GitHub Actions workflows from a single Git repo.
    The Git repository can be local or distant. In the latter case, it will be pulled
    locally and deleted unless specified otherwise.

    Example of usage:
    gha_datasets single myRepository -n myRepositoryName -s directory -o output.csv --headers
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
    if update == True:
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

    if output:
        with open(output, "a", encoding="utf-8") as file:
            utils.write_csv(entries, file, headers, repository_name)
    else:
        utils.write_csv(entries, sys.stdout, headers, repository_name)

    # print(ref, save_repository, update, after, workflows, output, repository_name, headers, repository, sep="\n")

    # cleanup
    if tmp_directory:
        tmp_directory.cleanup()


@main.command()
@click.option(
    "--directory",
    "-d",
    help="The directory where the Git repositories that will be extracted will be stored.",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True),
    required=True,
)
@click.option(
    "--error-directory",
    "-e",
    help="The directory where the standard and error outputs for "
    "Git repositories that could not be processed will be stored.",
    type=click.Path(exists=False, file_okay=False, dir_okay=True, writable=True),
)
@click.option(
    "--output-directory",
    "-o",
    help="The directory where the extracted GitHub Actions workflow files will be stored.",
    default="outputs",
    type=click.Path(exists=False, file_okay=False, dir_okay=True, writable=True),
)
@click.argument("options", nargs=-1, type=click.UNPROCESSED)
def batch(directory, error_directory, output_directory, options):
    """Extract the GitHub Actions workflows from multiple Git repos.
    This command assumes every Git repositories are under a folder.
    This command is equivalent to launching multiple times the "single" command
    for processing a single repository. Arguments given after '--' will be passed
    to each 'single' command. '--output' and '--repository-name' cannot be passed
    after '--' as they are used by default.

    Example of usage:
    gha_datasets batch -d repositories -e errors -o csv -- --workflows myWorkflowsResultsDirectory --headers
    """
    for folder in (error_directory, output_directory):
        if folder is not None:
            os.makedirs(folder, exist_ok=True)
    to_process = os.listdir(directory)
    to_process = [os.path.join(directory, f) for f in to_process]
    # there might be memory leaks here and there
    # starting a new process for each repository might be better
    # in the long run
    # we could even multiprocess it (bit might be problematic with git?)
    errors_count = 0
    for i, repo in enumerate(to_process):
        logger.info(
            "(%d/%d (%.2f%%) | %d error(s)) Processing repository '%s'",
            i,
            len(to_process),
            float(i) / len(to_process) * 100,
            errors_count,
            repo,
        )
        if not os.path.isdir(repo):
            logger.warning("'%s' is not a directory. Skipping...", repo)
            continue
        default_args = (
            "--output",
            os.path.join(output_directory, os.path.basename(repo) + ".csv"),
            "--repository-name",
            os.path.basename(repo),
        )
        args = (*default_args, *options, repo)
        p = subprocess.Popen(
            ["gha-datasets", "single", *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        out, err = p.communicate()
        if p.returncode != 0:
            logger.error(
                "(Error %d) Could not process repository '%s'", errors_count, repo
            )
            errors_count += 1
            if error_directory is not None:
                base = os.path.join(error_directory, os.path.basename(repo))
                with open(base + ".out.txt", "w") as file:
                    file.write(out.decode("utf-8"))
                with open(base + ".err.txt", "w") as file:
                    file.write(err.decode("utf-8"))
            continue


if __name__ == "__main__":
    main()
