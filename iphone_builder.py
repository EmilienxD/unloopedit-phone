from sys import platform
if platform != 'darwin':
    raise RuntimeError('This code is only dedicated for an iphone darwin virtuel machine')

try:
    import argparse
    import os
    import subprocess
    import shutil
    import requests


    def main(repo: str, folder: str | None = None, username: str = 'EmilienxD', branch: str = 'main'):
        if folder is None:
            folder = repo
    
        ZIP_URL = f"https://github.com/{username}/{repo}/archive/refs/heads/{branch}.zip"
        ZIP = os.path.join(folder, 'temp_github.zip')
        UNZIPPED_FOLDER = ZIP.removesuffix('.zip')
        GITHUB_FOLDER = os.path.join(UNZIPPED_FOLDER, f'{repo}-{branch}')

        if os.path.exists(folder):
            shutil.rmtree(folder)
        
        os.makedirs(folder)

        try:
            r = requests.get(ZIP_URL)
            if r.status_code != 200:
                if r.status_code == 404:
                    raise RuntimeError(f'(404) Unable to curl repository: {repo} is currently in private mode.')
                raise RuntimeError(f'({r.status_code}) Unable to curl repository')

            with open(ZIP, 'wb') as f:
                f.write(r.content)

            shutil.unpack_archive(ZIP, UNZIPPED_FOLDER, 'zip')

            for p in os.listdir(GITHUB_FOLDER):
                shutil.move(os.path.join(GITHUB_FOLDER, p), os.path.join(folder, p))

            shutil.rmtree(UNZIPPED_FOLDER)
            os.remove(ZIP)
            
            requirements_path = os.path.join(folder, 'requirements.txt')
            if os.path.exists(requirements_path):
                # Use --use-deprecated=legacy-resolver to avoid dependency conflicts with unstable module mega.py
                subprocess.run(['pip', 'install', '--use-deprecated=legacy-resolver', '-r', requirements_path])
            print('Project built successfully.')

        except Exception as e:
            shutil.rmtree(folder)
            raise

    if __name__ == '__main__':
        parser = argparse.ArgumentParser(description='Build a phone project from a github repository.')
        parser.add_argument('repo', help='The repository to build')
        parser.add_argument('folder', help='The folder to build the project in', nargs='?', default=None)
        parser.add_argument('--username', '-u', help='The username of the repository', default='EmilienxD')
        parser.add_argument('--branch', '-b', help='The branch of the repository', default='main')
        args = parser.parse_args()
        main(args.repo, args.folder, args.username, args.branch)

except Exception as e:
    print(f"ERROR:{e}", end='')