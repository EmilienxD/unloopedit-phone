import asyncio

from mega import Mega

from lib.modules.paths import Path, PathLike
from lib.modules.display import Logger

from lib.config import Paths
from lib.utils import create_unique_date

from .security import auth


class MegaCloud:

    logger = Logger('[MegaCloud]')
    ROOT_NAME = 'Cloud Drive'
    TEMP_PATH = Paths('TEMP')

    def __init__(self, account_uniquename: str | None = None):
        self.account = auth.select_account(account_uniquename)
        self.mega = Mega()
        self.user = None

    def login(self) -> None:
        """
        Logs in to the Mega account.
        """
        if self.user is None:
            self.user = self.mega.login(self.account.email, self.account.password)
            self.logger.info(f'Connected with account: {self.account.uniquename}')

    def rotate_account(self, account_uniquename: str | None = None) -> None:
        self.close()
        auth.rotate_account(self.account)
        self.account = auth.select_account(account_uniquename)
        self.login()

    @property
    def storage_details(self) -> dict[str, float]:
        """
        Retrieves storage details including total, used, and available space.
        :return: Dictionary with storage details.
        """
        self.login()

        storage = self.user.get_storage_space()
        total_space = storage['total'] / (1024 ** 3)  # Convert to GB
        used_space = storage['used'] / (1024 ** 3)  # Convert to GB
        available_space = total_space - used_space

        return {
            "total": total_space,
            "used": used_space,
            "available": available_space
        }
    
    def rotate_until_enough_storage(self, size: float) -> None:
        if size  / (1024 ** 3) > self.storage_details["available"]:
            self.rotate_until_enough_storage(size)
    
    def get(self, cloud_path: PathLike) -> dict | None:
        """
        Gets a file object from Mega by its path.
        
        :param cloud_path: Path to the file/folder, can include folders and filename
        :return: File object if found, None otherwise
        """
        if not cloud_path:
            return None

        self.login()

        cloud_path = Path(cloud_path)
        components = cloud_path.split_component()

        if len(components) == 1:
            components.insert(0, self.ROOT_NAME)

        files = self.user.get_files()
        current_folder_id = None

        for component in components[:-1]:
            folder = next((f for f in files.values() if f['a'].get('n') == component and 
                         (current_folder_id is None or f['p'] == current_folder_id)), None)
            if not folder:
                return None
            current_folder_id = folder['h']

        filename = components[-1]
        for file in files.values():
            if (current_folder_id is None or file['p'] == current_folder_id) and file['a'].get('n') == filename:
                return file

        return None

    def exists(self, cloud_path: PathLike):
        """
        Checks if a file exists at the specified path in Mega.
        
        :param cloud_path: Path to check, can include folders and filename
        :return: True if file exists, False otherwise
        """
        return self.get(cloud_path) is not None

    def create_folder(self, path: PathLike, exists_ok: bool = True):
        """
        Creates a folder structure on Mega based on the given path.
        
        :param path: The full folder path (e.g., 'Videos/2024/March')
        :return: The last created folder object
        """
        self.login()

        path = Path(path).relative
        components = path.split_component()

        files = self.user.get_files()
        parent_id = self.user.root_id
        created = False

        for i, component in enumerate(components):
            folder = next((f for f in files.values() if f['a'].get('n') == component and f['p'] == parent_id), None)

            if folder:
                parent_id = folder['h']
            else:
                folder = self.user.create_folder(component, parent_id)
                created = True
                
                if i == len(components) - 1:
                    break
    
                files = self.user.get_files()
                parent_id = next(iter(folder.values()))
            
        if not exists_ok and not created:
            raise FileExistsError(f'Folder: {path} already exists.')

        self.logger.info(f'Folder: {path.relative} created.')
        return folder

    async def upload_async(self,
            path: PathLike,
            cloud_path: PathLike | None = None,
            force_sync: bool = False
        ) -> None:
        """
        Uploads a file to the specified folder on Mega.
        :param path: Path to the video file on the local system.
        :param folder_name: Name of the folder on Mega to store the video.
        """
        path = Path(path, 'File', assert_exists=True)

        if cloud_path:
            cloud_path = Path(cloud_path).relative
            if cloud_path.is_file_path:
                new_name = cloud_path.full_name
                cloud_path = cloud_path.parent
            else:
                new_name = path.full_name
        else:
            new_name = path.full_name        
        
        temp_path = self.TEMP_PATH * create_unique_date()
        temp_path(exist_ok=True)
        temp_file_path = temp_path * new_name
        path.copy_to(temp_file_path, overwrite=True, send_to_trash=False)

        try:
            self.login()

            self.rotate_until_enough_storage(path.size)

            folder_descriptor = str(cloud_path.relative).replace('\\', '/') if cloud_path else None
            if cloud_path:
                dest = self.user.find_path_descriptor(folder_descriptor)
                if not dest:
                    self.create_folder(cloud_path)
                    dest = self.user.find_path_descriptor(folder_descriptor)
            else:
                dest = None

            if force_sync:
                self.user.upload(temp_file_path.fs, dest=dest)
            else:
                await asyncio.to_thread(lambda p=temp_file_path.fs, d=dest: self.user.upload(p, dest=d))
            
            self.logger.info(f'File: {path.relative} created at: {folder_descriptor}')
        finally:
            temp_path.remove(send_to_trash=False, not_exists_ok=True)

    def upload(self,
            path: PathLike,
            cloud_path: PathLike | None = None
        ) -> None:
        """
        Uploads a file to the specified folder on Mega.
        :param path: Path to the video file on the local system.
        :param folder_name: Name of the folder on Mega to store the video.
        """
        asyncio.run(self.upload_async(path=path, cloud_path=cloud_path, force_sync=True))

    async def download_async(self,
        cloud_path: PathLike | None = None,
        path: PathLike | None = None,
        overwrite: bool = False,
        send_to_trash: bool = True,
        max_concurrent: int = 6,
        force_sync: bool = False
    ) -> list[dict]:
        """
        Downloads an entire folder from Mega, preserving the directory structure.
        
        :param cloud_path: Path to the folder on Mega
        :param path: Local destination path
        :param overwrite: Whether to overwrite existing files
        :param send_to_trash: Whether to send existing files to trash when overwriting
        :return: List of downloaded file objects
        """
        max_concurrent = max_concurrent or 1
        assert max_concurrent > 0, f'Invalid max concurrent value: {max_concurrent}'

        self.login()
        
        cloud_path = Path(cloud_path or self.ROOT_NAME).relative
        path = Path(path or '/')

        assert cloud_path.is_file_path == path.is_file_path,\
            f"""Cloud path and local path must be either both files or both folders.
            Got: {cloud_path} and: {path.relative}"""

        if path.exists:
            if overwrite:
                path.remove(send_to_trash=send_to_trash)
            else:
                raise FileExistsError(f'Path: {path.relative} already exists.')
        
        cloud_path = Path(cloud_path).relative if cloud_path else None
        
        f = self.get(cloud_path)
        if not f:
            raise FileNotFoundError(f'Cloud folder not found: {cloud_path}')
        
        sema = None if force_sync else asyncio.Semaphore(max_concurrent)
        
        async def task(f: dict, p: PathLike):
            async with sema:
                await asyncio.to_thread(lambda tf=(None, f), ps=p.fs: self.user.download(tf, dest_filename=ps))
            self.logger.info(f'Downloaded file: {p.relative}')
        
        tasks = []
        if f.get('t') == 1:    # Folder
            files = self.user.get_files()
            downloaded_files = []
            
            path(exist_ok=True)
            
            def _dlr(folder_id: str, current_path: PathLike):
                items = [f for f in files.values() if f['p'] == folder_id]
                
                for item in items:
                    item_name: str = item['a']['n']
                    item_path = current_path * item_name
                    
                    if item['t'] == 0:    # File
                        if item_path.exists:
                            if overwrite:
                                item_path.remove(send_to_trash=send_to_trash)
                            else:
                                continue
                                
                        tasks.append(task(item, item_path))
                        downloaded_files.append(item)
                        
                    elif item['t'] == 1:    # Folder
                        item_path(exist_ok=True)
                        _dlr(item['h'], item_path)
            
            _dlr(f['h'], path)
        else:
            if force_sync:
                self.user.download(f, dest_filename=path.fs)
            else:
                tasks.append(task(f, path))

        await asyncio.gather(*tasks)
        return f
    
    def download(self,
        cloud_path: PathLike | None = None,
        path: PathLike | None = None,
        overwrite: bool = False,
        send_to_trash: bool = True,
        max_concurrent: int = 6
    ) -> list[dict]:
        """
        Downloads an entire folder from Mega, preserving the directory structure.
        
        :param cloud_path: Path to the folder on Mega
        :param path: Local destination path
        :param overwrite: Whether to overwrite existing files
        :param send_to_trash: Whether to send existing files to trash when overwriting
        :return: List of downloaded file objects
        """
        return asyncio.run(self.download_async(
            cloud_path=cloud_path,
            path=path,
            overwrite=overwrite,
            send_to_trash=send_to_trash,
            max_concurrent=max_concurrent,
            force_sync=True
        ))

    def __enter__(self):
        self.login()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def close(self) -> None:
        self.user = None
        self.logger.info('Closing')