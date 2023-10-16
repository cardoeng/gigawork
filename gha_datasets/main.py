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
    pass


@main.command()
@click.option(
    "--ref",
    "--branch",
    "-r",
    default="HEAD",
    help="The reference to start from.",
    type=str,
)
@click.option(
    "--save-repository",
    "-s",
    help="Save the repository to the given path.",
    type=click.Path(exists=False, file_okay=False, dir_okay=True, writable=True),
)
@click.option(
    "--update", "-u", help="Update the repository at the given path.", is_flag=True
)
@click.option(
    "--after",
    "-a",
    help="Only consider commits between the reference and the given commit.",
    type=str,
)
@click.option(
    "--workflows",
    "-w",
    help="The directory where the workflows will be saved.",
    default="workflows",
    type=click.Path(exists=False, file_okay=False, dir_okay=True, writable=True),
)
@click.option(
    "--output",
    "-o",
    help="The file where the information related to the dataset will be saved.",
    type=click.Path(exists=False, file_okay=True, dir_okay=False, writable=True),
)
@click.option(
    "--repository-name",
    "-n",
    help="Add a column repository_name to the resulting table with the given value.",
    type=str,
)
@click.option(
    "--headers",
    "-h",
    help="Add a header row to the resulting file.",
    is_flag=True,
)
@click.argument(
    "repository",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True),
)
def workflows(
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
    """Extract the workflows from the given repository."""
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
    except (git.exc.GitCommandError, ValueError) as e:
        logger.error("Could not read repository at '%s'", repository)
        logger.debug(e)
        sys.exit(1)

    # update it if requested
    if update:
        try:
            update_repository(repo)
        except git.exc.GitCommandError as e:
            logger.error(
                "Could not update repository at '%s'. Keeping the current version...",
                repository,
            )
            logger.debug(e)

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
    help="The directory where the repositories are stored.",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True),
    required=True,
)
@click.option(
    "--error-directory",
    "-e",
    help="The directory where the errors for directory that could not "
    "be processed are stored.",
    type=click.Path(exists=False, file_okay=False, dir_okay=True, writable=True),
)
@click.option(
    "--output-directory",
    "-o",
    help="The directory where the resulting files will be stored.",
    default="outputs",
    type=click.Path(exists=False, file_okay=False, dir_okay=True, writable=True),
)
@click.argument("options", nargs=-1, type=click.UNPROCESSED)
def batch_workflows(directory, error_directory, output_directory, options):
    """Execute the workflows command on multiple repositories."""
    for d in (error_directory, output_directory):
        if d is not None:
            os.makedirs(d, exist_ok=True)
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
        )
        args = (*default_args, *options, repo)
        p = subprocess.Popen(
            ["gha-datasets", "workflows", *args],
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