import os
import sys
import click
from extractors import WorkflowExtractor
from repository import clone_repository, read_repository, update_repository
import logging
import tempfile
import utils

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--ref", "-r", default="HEAD", help="The reference to start from.", type=str
)
@click.option(
    "--save-repository", "-s", help="Save the repository to the given path.", type=str
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
    type=str,
)
@click.option(
    "--output",
    "-o",
    help="The file where the information related to the dataset will be saved.",
    type=str,
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
@click.argument("repository", type=str)
def main(
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
    tmp_directory = None  # the temporary directory if one is created
    r = None  # the repository

    # clone the repository if it does not exist
    if not os.path.exists(repository):
        if not save_repository:
            tmp_directory = tempfile.TemporaryDirectory(dir=".")
            save_repository = tmp_directory.name
        r = clone_repository(repository, save_repository)
    else:
        r = read_repository(repository)
    if not r:
        logger.error(f"Could not read repository at '{repository}'")
        sys.exit(1)

    # update it if requested
    if update:
        update_repository(r)

    extractor = WorkflowExtractor(r, workflows)
    entries = extractor.extract(ref, after)

    if output:
        with open(output, "w") as f:
            utils.write_csv(entries, f, headers, repository_name)
    else:
        utils.write_csv(entries, sys.stdout, headers, repository_name)

    # print(ref, save_repository, update, after, workflows, output, repository_name, headers, repository, sep="\n")

    # cleanup
    if tmp_directory:
        tmp_directory.cleanup()


if __name__ == "__main__":
    main()
