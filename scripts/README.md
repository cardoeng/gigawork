The following example, using the script `batch.py`, extracts the workflows from each repository in the folder `repositories`, store the standard and error output for each repository in the directory `errors`. 
That only applies for repositories that could not be processed due to an error. 
The command also store every CSV file into the `csv` directory. 
Note that, behind the scenes, it will launch, for each repository, a process executing the `gigawork` program explained before with the repository name equals to the name of the folder.

```bash
batch.py -d repositories -e errors -o csv
```

When using the `batch.py` script, you can also give arguments to `gigawork` by giving them after `--`. The following command is the same as above, except we tell `gigawork` command to store each workflow files in the `myWorkflowsResultsDirectory` and add headers to the resulting CSV file (for each repository).

```bash
batch.py -d repositories -e errors -o csv -- --workflows myWorkflowsResultsDirectory --headers
```