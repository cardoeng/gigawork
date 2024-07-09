import pandas as pd
from tqdm import tqdm
import click

generated_ids = {}

def gen_id(c):
    key = (c['repository'], c['file_path'])
    rkey = (c['repository'], c['previous_file_path'])
    # ct = c["change_type"]
    existing = key in generated_ids
    if pd.isnull(c["file_hash"]):
        if rkey not in generated_ids:
            raise ValueError(f'Key {str(rkey)} does not exist (commit: {c["commit_hash"]})')
        return generated_ids.pop(rkey)
    elif pd.isnull(c["previous_file_hash"]):
        if existing:
            raise ValueError(f'Key {key} already exists, (commit: {c["commit_hash"]})')
            # Somehow, the file is added two times in the git history
        generated_ids[key] = '/'.join(
            (c['repository'], c['file_path'], str(c['commit_hash'])))
    elif key != rkey:
        # rename
        # at this point, we are sure that the previous file exists
        # as file_hash and previous_file_hash are not null (see before)
        if rkey not in generated_ids:
            raise ValueError(f'Key {str(rkey)} does not exist (commit: {c["commit_hash"]})')
        if existing:
            raise ValueError(f'Key {key} already exists (commit: {c["commit_hash"]})')
        generated_ids[key] = generated_ids[rkey]
        del generated_ids[rkey]
    elif not existing:
        raise ValueError(f'Key {key} does not exist')
        
    return generated_ids[key]

@click.command()
@click.argument('input_file', 
    type=click.Path(exists=True),
)
@click.argument('output_file', 
    type=click.Path(),
)
def main(input_file, output_file):
    tqdm.pandas()
    data = pd.read_csv(input_file)
    # apply in reverse order
    data['uid'] = data.iloc[::-1].progress_apply(gen_id, axis=1).iloc[::-1]
    data.to_csv(output_file, index=False)
    
    
if __name__ == '__main__':
    main()