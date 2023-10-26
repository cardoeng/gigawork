# GHA datasets

An automated tool for extracting GitHub Actions' workflows from Git repositories written in Python.
`gha_datasets` is primarily designed to be used as a command-line tool.
Given a Git repository (or a folder containing multiple Git repositories), it extracts the different workflows and their versions from the Git history. The workflows and its related information (such as the author name, the commit date, ...) are saved in a given directory and a given CSV file.

## Installation

<!-- The easiest way to install `gha_datasets` is to install from Pypi
```pip install TODO``` -->

An easy way to install `gha_datasets` is via `pip` from this GitHub repository
```
pip install git+https://github.com/cardoeng/msr2024_guillaume
```

You may wish to use this tool in a virtual environment. You can use the following commands.
```
virtualenv gha_datasets_venv
source gha_datasets_venv/bin/activate
pip install git+https://github.com/cardoeng/msr2024_guillaume
```

## Usage

After installation, the `gha-datasets` command-line tool should be available in your shell. Otherwise, please replace `gha-datasets` by `python -m gha-datasets`. The explanations in the following stays valid in both cases.

You can use `gha_datasets` in two ways :

* The first one is for only one repository.
* The second way is for processing multiple repositories.

```
Usage: gha-datasets [OPTIONS] COMMAND [ARGS]...

  A tool for extracting GitHub Actions workflows.

Options:
  --help  Show this message and exit.

Commands:
  batch   Extract the GitHub Actions workflows from multiple Git...
  single  Extract the GitHub Actions workflows from a single Git repository.
```

The `single` command extracts the GHA workflows from a single Git repository that is locally stored or remotely stored.

```
Usage: gha-datasets single [OPTIONS] REPOSITORY

  Extract the GitHub Actions workflows from a single Git repository. The Git
  repository can be local or distant. In the latter, it will be pulled locally
  and deleted if not told otherwise.

  Example of usage:  gha_datasets single myRepository -n myRepositoryName -s
  saveRepositoryName -o output.csv --headers

Options:
  -r, --ref, --branch TEXT        The commit reference (i.e., commit SHA or
                                  TAG) to start from.
  -s, --save-repository DIRECTORY
                                  Save the repository to the given path in
                                  case it was distant.
  -u, --update                    Update the repository at the given path.
  -a, --after TEXT                Only consider commits that are after the
                                  given commit reference (i.e., commit SHA or
                                  TAG).
  -w, --workflows DIRECTORY       The directory where the extracted GHA
                                  workflow files will be saved.
  -o, --output FILE               The file where the information related to
                                  the dataset will be saved. In case it is not
                                  given, the collected information will be
                                  sent to the standard output.
  -n, --repository-name TEXT      Add a column `repository_name` to the
                                  resulting table that will be equal the given
                                  value.
  -h, --headers                   Add a header row to the resulting file.
  --help                          Show this message and exit.
```

The `batch` command allows to iteratively extracts the GHA workflows from multiple Git repositories that are locally stored. Note that it is a helper command to launch the `single` command explained above multiple times.

```
Usage: gha-datasets batch [OPTIONS] [OPTIONS]...

  Extract the GitHub Actions workflows from multiple Git repositories. This
  command assumes every Git repositories are under a folder. This command is
  equivalent to launching multiple times the "single" command for processing a
  single repository.

  Example of usage:  gha_datasets batch -d repositories -e errors -o csv --
  --workflows myWorkflowsResultsDirectory --headers

Options:
  -d, --directory DIRECTORY       The directory where the Git repositories are
                                  stored.  [required]
  -e, --error-directory DIRECTORY
                                  The directory where the standard and error
                                  outputs for Git repositories that could not
                                  be processed will be stored.
  -o, --output-directory DIRECTORY
                                  The directory where the extracted GHA
                                  workflow files will be stored.
  --help                          Show this message and exit.
```

### Examples

As an example, the following command extracts every workflow files from the repository `example_repository`, add the name `my-example-name` in the output, saves the output in `output.csv` and add the CSV headers to `output.csv`. Each workflow file will be saved in the directory `workflows` (which is also the default save directory).

```bash
gha_datasets single example_repository -n my-example-name -o output.csv -w workflows --headers
```

Note that the repository do not have to be already cloned. The tool can fetch it for you and clean up (unless told otherwise) when the work is done. An example is shown below. The GitHub repository `https://github.com/cardoeng/msr2024_guillaume` will be fetched, saved under the `gha_datasets` directory and the `repository_name` will be `gha_datasets_name` in the resulting CSV file. Note that, in the case `-s gha_datasets` was not specified, the tool will create a temporary directory and clean up when it finishes.

```bash
gha_datasets single https://github.com/cardoeng/msr2024_guillaume -n gha_datasets_name -s gha_datasets -o output.csv --headers
```

The following command extracts the workflows from each repository in the folder `repositories`, store the standard and error output in the directory `errors` for repositories that could not be processed and store every CSV file into the `csv` directory. Note that, behind the scenes, it will launch, for each repository, a process executing the `single` command explained above with the repository name equals to the name of the folder.

```bash
gha_datasets batch -d repositories -e errors -o csv
```

You can also give arguments to the single command by giving them after `--`. The following command is the same as above, except we tell the `single` command to store each workflows in the `myWorkflowsResultsDirectory` and add headers to the resulting CSV file.

```bash
gha_datasets batch -d repositories -e errors -o csv -- --workflows myWorkflowsResultsDirectory --headers
```

## License

Distributed under [GNU Lesser General Public License v3](https://github.com/cardoeng/msr2024_guillaume/blob/master/LICENSE.txt).