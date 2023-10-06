import click

@click.command()
@click.option('--ref',
              default="HEAD",
              help="The reference to start from.",
              type=str)
@click.option('--save-repository',
              help="Save the repository to the given path.",
              type=str)
@click.option('--update',
              help="Update the repository at the given path.",
              is_flag=True)
@click.option('--after',
              help="Only consider commits between the reference and the given commit.",
              type=str)
@click.option('--workflows',
              help="The directory where the workflows will be saved.",
              default="workflows",
              type=str)
@click.option('--output',
              help="The file where the information related to the dataset will be saved.",
              type=str)
@click.option('--repository-name',
              help="Add a column repository_name to the resulting table with the given value.",
              type=str)
@click.option('--headers',
              help="Add a header row to the resulting file.",
              is_flag=True,)
@click.argument('repository',                
                type=str)
def main(ref, save_repository, update, after, workflows, output, repository_name, headers, repository):
    print(ref, save_repository, update, after, workflows, output, repository_name, headers, repository, sep="\n")
    
if __name__ == "__main__":
    main()