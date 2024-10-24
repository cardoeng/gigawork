import logging
import os
import subprocess
import click
import pandas as pd
from tqdm import tqdm
import gzip

HEADERS = "repository,commit_hash,author_name,author_email,committer_name,committer_email,committed_date,authored_date,file_path,previous_file_path,file_hash,previous_file_hash,git_change_type,valid_yaml,probably_workflow,valid_workflow"

# log into a file
logging.basicConfig(level=logging.INFO, filename="batch.log")
logger = logging.getLogger(__name__)


@click.command()
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
    help="The directory where the extracted metadata will be stored.",
    default="outputs",
    type=click.Path(exists=False, file_okay=False, dir_okay=True, writable=True),
)
@click.option(
    "--repositories-list",
    "-r",
    help="A file containing the list of repositories to process.",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
)
@click.argument("options", nargs=-1, type=click.UNPROCESSED)
def batch(directory, error_directory, output_directory, repositories_list, options):
    """Extract the GitHub Actions workflows from multiple Git repos.
    This command assumes every Git repositories are under a folder.
    This command is equivalent to launching multiple times the "single" command
    for processing a single repository. Arguments given after '--' will be passed
    to each 'single' command. '--output' and '--repository-name' cannot be passed
    after '--' as they are used by default.

    Example of usage:
    batch.py -d repositories -e errors -o csv -- --workflows myWorkflowsResultsDirectory --headers
    """
    for folder in (error_directory, output_directory):
        if folder is not None:
            os.makedirs(folder, exist_ok=True)
    df = pd.read_csv(repositories_list)
    to_process = df["name"].tolist()
    to_process = (
        os.path.join(directory, repo.replace("/", ":")) for repo in to_process
    )
    # there might be memory leaks here and there
    # starting a new process for each repository might be better
    # in the long run
    # we could even multiprocess it (but might be problematic with git?)
    errors_count = 0
    for repo in tqdm(to_process, total=len(df), desc="Processing repositories"):
        if not os.path.isdir(repo):
            logger.warning("'%s' is not a directory. Skipping...", repo)
            continue
        default_args = (
            "--no-headers",
            "--output",
            os.path.join(output_directory, os.path.basename(repo) + ".csv"),
            "--repository-name",
            os.path.basename(repo),
            "--save-auxiliaries",
        )
        args = (*default_args, *options, repo)
        sproc = subprocess.Popen(
            ["gigawork", *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        out, err = sproc.communicate()
        if sproc.returncode != 0:
            logger.error(
                "(Error %d) Could not process repository '%s'", errors_count, repo
            )
            errors_count += 1
            if error_directory is not None:
                base = os.path.join(error_directory, os.path.basename(repo))
                with open(base + ".out.txt", "w", encoding="utf-8") as file:
                    file.write(out.decode("utf-8"))
                with open(base + ".err.txt", "w", encoding="utf-8") as file:
                    file.write(err.decode("utf-8"))
            continue
    print(f"There was {errors_count} errors (including not found repositories)")
    outfile = os.path.join(output_directory, "merged.csv.gz")
    with gzip.open(outfile, "wt", encoding="utf-8") as file:
        file.write(HEADERS + "\n")
        for f in tqdm(os.listdir(output_directory), desc="Merging CSV files"):
            with open(os.path.join(output_directory, f), "r", encoding="utf-8") as f:
                file.write(f.read())


if __name__ == "__main__":
    batch()
