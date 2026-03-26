from huggingface_hub import hf_hub_download
import tarfile

def check_dataset():
    print("Downloading audio.tar.gz...")
    path = hf_hub_download(repo_id='yfyeung/medical', filename='audio.tar.gz', repo_type='dataset')
    print(f"Downloaded to {path}")
    
    with tarfile.open(path, 'r:gz') as tar:
        names = tar.getnames()
        print('Total files:', len(names))
        print('First 20 files:', names[:20])
        gas = [n for n in names if 'GAS' in n or 'gas' in n.lower()]
        print(f'Found {len(gas)} GAS files')
        if gas:
            print('Sample GAS files:', gas[:20])

if __name__ == '__main__':
    check_dataset()
