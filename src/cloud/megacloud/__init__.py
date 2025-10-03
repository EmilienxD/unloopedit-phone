import asyncio

from mega import Mega

from src.modules.paths import Path, PathLike
from src.modules.files import generate_random_path, TempDir
from src.modules.display import Logger

from src.config import Paths
from src.exceptions import StorageLimitExceededError

from .security import auth


class MegaCloud:

    logger = Logger('[MegaCloud]')
    ROOT_NAME = 'Cloud Drive'

    def __init__(self, account_uniquename: str | None = None):
        self.account = auth.ACCOUNT
        self.mega = Mega()
        self.user = None

    def login(self) -> None:
        """
        Logs in to the Mega account.
        """
        if self.user is None:
            self.user = self.mega.login(self.account.email, self.account.password)
            self.logger.info(f'Connected with account: {self.account.uniquename}')

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

    def get(self, cloud_path: PathLike) -> dict | None:
        """
        Gets a file object from Mega by its path.
        
        :param cloud_path: Path to the file/folder, can include folders and filename
        :return: File object if found, None otherwise
        """
        if not cloud_path:
            return None

        self.login()

        cloud_path = Path(cloud_path).relative
        components = cloud_path.split_components()

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

    def create_folder(self, cloud_path: PathLike, exists_ok: bool = True) -> None:
        """
        Creates a folder structure on Mega based on the given path.
        
        :param path: The full folder path (e.g., 'Videos/2024/March')
        :return: The last created folder object
        """
        self.login()

        cloud_path = Path(cloud_path).relative
        components = cloud_path.split_components()

        files = self.user.get_files()
        parent_id = self.user.root_id
        created = False

        for i, component in enumerate(components):
            folder = next((f for f in files.values() if f['a'].get('n') == component and f['p'] == parent_id), None)

            if folder:
                parent_id = folder['h']
            elif component:
                folder = self.user.create_folder(component, parent_id)
                created = True
                
                if i == len(components) - 1:
                    break
    
                files = self.user.get_files()
                parent_id = next(iter(folder.values()))
        
        if not exists_ok and not created:
            raise FileExistsError(f'Folder: {cloud_path.ufs} already exists.')

        if created:
            self.logger.info(f'Folder: {cloud_path.ufs} created.')
        return folder
    
    def list_files(self, cloud_path: PathLike | None = None) -> list[PathLike]:
        """
        Lists all items (files and folders) directly under the given Mega “cloud_path”.
        Returns a list of cloud paths (as strings), e.g.:

            mc = MegaCloud(...)
            mc.login()
            mc.list_files("MyFolder/SubFolder")
            # -> ["MyFolder/SubFolder/file1.mp4", "MyFolder/SubFolder/NestedFolder"]

        If `cloud_path` is None or empty, lists everything directly under the root.
        Raises:
          - FileNotFoundError   if the specified folder does not exist.
          - NotADirectoryError  if the specified path exists but is a file.
        """
        self.login()

        # Determine which folder node we are listing.
        if cloud_path:
            # Normalize and try to fetch the node for the given path
            requested = Path(cloud_path).relative
            node = self.get(requested)
            if node is None:
                raise FileNotFoundError(f"Cloud folder not found: {requested}")
            # In Mega’s metadata, 't' == 1 means “folder”
            if node.get("t") != 1:
                raise NotADirectoryError(f"Cloud path is not a folder: {requested}")
            parent_id = node["h"]
            base_path = requested
        else:
            # No cloud_path given → use root folder
            parent_id = self.user.root_id
            base_path = None

        # Fetch all items in the account and filter by parent‐ID
        all_nodes = self.user.get_files()
        children = [f for f in all_nodes.values() if f["p"] == parent_id]

        result: list[str] = []
        for child in children:
            name = child["a"].get("n")
            result.append((Path(base_path) * name if base_path else Path(name)).relative)
        return result

    async def upload_async(self,
            path: PathLike,
            cloud_path: PathLike | None = None,
            max_concurrent: int = 6,
            overwrite: bool = False,
            send_to_trash: bool = False,
            exists_ok: bool = True
        ) -> None:
        """
        Uploads a file to the specified folder on Mega.
        :param path: Path to the video file on the local system.
        :param folder_name: Name of the folder on Mega to store the video.
        """
        self.login()

        path = Path(path, assert_exists=True)

        if cloud_path is None:
            cloud_path = path.full_name
        else:
            cloud_path = Path(cloud_path).relative

        max_concurrent = max(1, max_concurrent)
        sema = asyncio.Semaphore(max_concurrent)

        async def task(p: PathLike, d: dict, cp: PathLike):
            async with sema:
                await asyncio.to_thread(self.user.upload, filename=p.fs,
                                        dest=d, dest_filename=cp.full_name)
            self.logger.info(f'Uploaded file: {p.relative} to {cp.ufs}')

        with TempDir(generate_random_path(dir_path=Paths('TEMP'), ext='',
                                          prefix='mega_', min_len=8)) as temp:
            temp_target = temp * path.full_name
            path.copy_to(temp_target, overwrite=True, send_to_trash=False)

            if path.size / (1024 ** 3) > self.storage_details["available"]:
                raise StorageLimitExceededError(f'Can not upload {path} to mega.')

            tasks = []

            def _upr(p: PathLike, cp: PathLike):
                cp = cp.relative
                cloud_dir = cp.parent.relative

                if self.exists(cp):
                    if overwrite:
                        self.delete(cp, send_to_trash=send_to_trash, skip_errors=True)
                    else:
                        if exists_ok:
                            return
                        else:
                            raise FileExistsError(f'File: {cp.ufs} already exists.')

                if p.is_file_path:
                    dest = self.user.find_path_descriptor(cloud_dir.ufs.replace('\\', '/')) if cloud_dir else None
                    tasks.append(task(p, dest, cp))
                else:
                    self.create_folder(cp, exists_ok=True)
                    for sub_p in p:
                        _upr(sub_p, cp * sub_p.full_name)

            _upr(path, cloud_path)
            await asyncio.gather(*tasks)

    def upload(self,
            path: PathLike,
            cloud_path: PathLike | None = None,
            max_concurrent: int = 6,
            overwrite: bool = False,
            send_to_trash: bool = False,
            exists_ok: bool = True
        ) -> None:
        """
        Uploads a file to the specified folder on Mega.
        :param path: Path to the video file on the local system.
        :param folder_name: Name of the folder on Mega to store the video.
        """
        asyncio.run(self.upload_async(path=path, cloud_path=cloud_path, max_concurrent=max_concurrent,
                                      overwrite=overwrite, send_to_trash=send_to_trash, exists_ok=exists_ok))

    async def download_async(self,
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
        max_concurrent = max_concurrent or 1
        assert max_concurrent > 0, f'Invalid max concurrent value: {max_concurrent}'

        self.login()
        
        cloud_path = Path(cloud_path or self.ROOT_NAME).relative
        path = Path(path or '/')

        assert cloud_path.is_file_path == path.is_file_path,\
            f"""Cloud path and local path must be either both files or both folders.
            Got: {cloud_path} and: {path.relative}"""
        
        cloud_path = Path(cloud_path).relative if cloud_path else None
        
        f = self.get(cloud_path)
        if not f:
            raise FileNotFoundError(f'Cloud file not found: {cloud_path}')

        if path.exists:
            if overwrite:
                path.remove(send_to_trash=send_to_trash)
            else:
                raise FileExistsError(f'Path: {path.relative} already exists.')
        
        max_concurrent = max(1, max_concurrent)
        sema = asyncio.Semaphore(max_concurrent)
        
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
            max_concurrent=max_concurrent
        ))
    
    def delete(self,
        cloud_path: PathLike,
        send_to_trash: bool = True,
        skip_errors: bool = False
    ) -> None:
        self.login()

        del_func = self.user.delete if send_to_trash else self.user.destroy
        
        f = self.get(cloud_path)
        if f is None:
            if skip_errors:
                self.logger.warning(f'Failed to delete {cloud_path}: File not found.')
                return
            else:
                raise FileNotFoundError(f'Cloud file not found: {cloud_path}')

        del_func(f['h'])
        self.logger.info(f'Deleted: {cloud_path}')

    def __enter__(self):
        self.login()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def close(self) -> None:
        self.user = None
        self.logger.info('Closing')