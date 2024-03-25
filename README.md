# gigawork

An automated tool for extracting GitHub Actions' workflows from Git repositories written in Python.
`gigawork` (**Gi**ve me **G**itHub **A**ctions **Work**flows) is primarily designed to be used as a command-line tool.
Given a Git repository, it extracts the different workflows and their versions from the Git history. 
The extraction is done by traversing the Git history of the repository and going back in time respecting the first-parent rule until the first commit (or the given reference) is reached.
The workflows are saved in a given directory along with relevant metadata (see [Usage](#usage)) in a given CSV file.

## Installation

The easiest way to install `gigawork` is to install from Pypi
```
pip install gigawork
```

Another easy way to install `gigawork` is via `pip` from this GitHub repository
```
pip install git+https://github.com/cardoeng/gigawork
```

Alternatively, you can clone this repository and install it locally
```
git clone https://github.com/cardoeng/gigawork
cd gigawork
pip install .
```

You may wish to use this tool in a virtual environment. You can use the following commands.
```
virtualenv gigawork_venv
source gigawork_venv/bin/activate
pip install gigawork
```

## Usage

After installation, the `gigawork` command-line tool should be available in your shell. Otherwise, please replace `gigawork` by `python -m gigawork`. The explanations in the following stays valid in both cases.

You can use `gigawork` with the following arguments:

```
Usage: gigawork [OPTIONS] REPOSITORY

  Extract the GitHub Actions workflow files from a single Git repository
  `REPOSITORY`. The extraction is done by traversing the Git history of the
  repository starting from the reference given to `-r` and going back in time
  respecting the first-parent rule until the first commit (or the reference
  given to `-a`) is reached. The Git repository can be local or distant. In
  the latter case, it will be pulled locally and deleted unless specified
  otherwise. Every extracted workflow file will be stored in the directory
  given to `-w` (or the directory `workflows` if not specified). The metadata
  related to the extracted workflows will be written in the CSV file given to
  `-o`, or in the standard output if not specified. The metadata related to
  the renaming of workflows will be stored in the CSV file given to `-ro`, or
  not stored if not specified.

  Example of usage: gigawork myRepository -n myRepositoryName -s directory -o
  output.csv --no-headers

Options:
  -r, --ref, --branch REF         The most recent commit reference (i.e.,
                                  commit SHA or TAG) to be considered for the
                                  extraction.
  -s, --save-repository DIRECTORY
                                  Save the repository to the given directory
                                  in case `REPOSITORY` was distant.
  -u, --update                    Fetch the repository at the given path.
  -a, --after REF                 Only consider commits after the given commit
                                  reference (i.e., commit SHA or TAG).
  -w, --workflows DIRECTORY       The directory where the extracted GitHub
                                  Actions workflow files will be stored.
  -o, --output FILE               The output CSV file where information
                                  related to the dataset will be stored. By
                                  default, the information will written to the
                                  standard output.
  -ao, --auxiliary-output FILE    The output CSV file where information
                                  related to the auxiliary files will be
                                  stored. By default, the information will not
                                  be stored.
  -n, --repository-name TEXT      Add a column `repository` to the output file
                                  where each value will be equal to the
                                  provided parameter.
  --no-headers                    Remove the header row from the CSV output
                                  file.
  -h, --help                      Show this message and exit.
```

The CSV file given to `-o` (or that will be written to the standard output by default) will contain the following columns:
- `repository`: the name of the repository if `-n` was specified
- `commit_hash`: the commit SHA of the commit where the workflow file was extracted
- `author_name`: the name of the author of the commit
- `author_email`: the email of the author of the commit
- `committer_name`: the name of the committer of the commit
- `committer_email`: the email of the committer of the commit
- `committed_date`: the committed date of the commit
- `authored_date`: the authored date of the commit
- `file_path`: the path of the workflow file in the repository
- `previous_file_path`: The path to this file before it has been touched
- `file_hash`: the SHA of the workflow file (and so, its name in the output directory)
- `previous_file_hash`: The name of the related workflow file in the dataset, before it has been touched
- `change_type`: the type of change (A for added, M for modified, D for deleted). Note that a renamed file will be seen as a modification.
- `valid_yaml`: a boolean indicating if the file is a valid YAML file.
- `probably_workflow`: a boolean representing if the file contains the YAML key `on` and `jobs`. (Note that a file can be an invalid YAML file while having this value set to true).
- `valid_workflow`: a boolean indicating if the file respect the syntax of GitHub Actions workflow. A freely available JSON Schema was used in this goal. This schema is neither made nor maintained by the authors of this repository. It was originally found on [https://json.schemastore.org/github-workflow.json](https://json.schemastore.org/github-workflow.json)

`-ao` will create a similar file containing every auxiliary files (i.e., files in a subdirectory or not having at least `probably_workflow` set to true).

### Examples

As an example, the following command extracts every workflow files from the repository `example_repository`, add the name `my-example-name` in the output. It also saves various information (such as commit SHA, author name, ...) in `output.csv` (with the headers as `--no-headers` is not specified). Each workflow file will be saved in the directory `workflows` (which is also the default save directory).

```bash
gigawork example_repository -n my-example-name -o output.csv -w workflows
```

Note that the repository does not have to be already cloned. The tool can fetch it for you and clean up (unless told otherwise) when the work is done. An example is shown below. The GitHub repository `https://github.com/cardoeng/gigawork` will be fetched, saved under the `gigawork` directory and the `repository` column will be `gigawork_name` in the resulting CSV file. Note that, if `-s gigawork` was not specified, the tool will create a temporary directory and clean up when it finishes.

```bash
gigawork https://github.com/cardoeng/gigawork -n gigawork_name -s gigawork -o output.csv
```

## License

Distributed under [GNU Lesser General Public License v3](https://github.com/cardoeng/gigawork/blob/master/LICENSE.txt).