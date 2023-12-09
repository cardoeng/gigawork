# gigawork

An automated tool for extracting GitHub Actions' workflows from Git repositories written in Python.
`gigawork` (**Gi**ve me **G**itHub **A**ctions **Work**flows) is primarily designed to be used as a command-line tool.
Given a Git repository (or a folder containing multiple Git repositories), it extracts the different workflows and their versions from the Git history. The workflows and its related information (such as the author name, the commit date, ...) are saved in a given directory and a given CSV file.

## Installation

The easiest way to install `gigawork` is to install from Pypi
```
pip install gigawork
```

An easy way to install `gigawork` is via `pip` from this GitHub repository
```
pip install git+https://github.com/cardoeng/gigawork
```

You may wish to use this tool in a virtual environment. You can use the following commands.
```
virtualenv gigawork_venv
source gigawork_venv/bin/activate
pip install git+https://github.com/cardoeng/gigawork
```

## Usage

After installation, the `gigawork` command-line tool should be available in your shell. Otherwise, please replace `gigawork` by `python -m gigawork`. The explanations in the following stays valid in both cases.

You can use `gigawork` with the following arguments:

```
Usage: gigawork [OPTIONS] REPOSITORY

  Extract the GitHub Actions workflows from a single Git repository. The Git
  repository can be local or distant. In the latter, it will be pulled locally
  and deleted if not told otherwise.

  Example of usage:  gigawork single myRepository -n myRepositoryName -s
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

### Examples

As an example, the following command extracts every workflow files from the repository `example_repository`, add the name `my-example-name` in the output. It also saves various information (such as commit SHA, author name, ...) in `output.csv` and add the CSV headers to `output.csv`. Each workflow file will be saved in the directory `workflows` (which is also the default save directory).

```bash
gigawork example_repository -n my-example-name -o output.csv -w workflows --headers
```

Note that the repository does not have to be already cloned. The tool can fetch it for you and clean up (unless told otherwise) when the work is done. An example is shown below. The GitHub repository `https://github.com/cardoeng/gigawork` will be fetched, saved under the `gigawork` directory and the `repository_name` will be `gigawork_name` in the resulting CSV file. Note that, if `-s gigawork` was not specified, the tool will create a temporary directory and clean up when it finishes.

```bash
gigawork https://github.com/cardoeng/gigawork -n gigawork_name -s gigawork -o output.csv --headers
```

## License

Distributed under [GNU Lesser General Public License v3](https://github.com/cardoeng/gigawork/blob/master/LICENSE.txt).