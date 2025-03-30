"""
This module provides various utility functions for file and directory operations, including path manipulations, file removal, compression, and shortcut creation. It leverages several external libraries such as `send2trash`, `shutil`, `pythoncom`, `winshell`, `pylnk3`, and `gzip` to facilitate these tasks.

Functions:
---------
    base_path:
        Returns the base directory path of the main Python file.
    dir_path:
        Returns the directory path for a given file or directory.
    ful_path:
        Joins multiple paths and normalizes them to use backslashes.
    dir_list:
        Returns all file paths in a directory.
    remove_definitly:
        Permanently removes files or directories.
    remove_to_trash:
        Moves files or directories to the trash.
    name_path:
        Returns the base name of a file or directory path.
    file_extension:
        Returns the file extension of a given file path.
    last_file:
        Retrieves the last modified file(s) in a directory that match a given name pattern.
    clear_TEMP:
        Clears temporary files with a specific prefix in the TEMP directory.
    create_shortcut:
        Creates a shortcut to a target file or directory.
    get_shortcut_target_path:
        Retrieves the target path of a shortcut.
    compress_gzip:
        Compresses a text file using gzip.
    decompress_gzip_file:
        Decompresses a gzip file and writes the decompressed content to an output file.
    create_gzip:
        Creates a gzip file with the given content.
    read_gzip:
        Reads the content of a gzip file and returns it.

Constants:
---------
    USERNAME (str): The username of the Windows user.
    USERPROFILE (str): The path to the username directory of the Windows user.
    MAIN_PYTHON_FILE (str): The path to the main python file when running the script
    lib.modules_PATH (str): The path to the directory "personnal_modules" containing notably this file.
    TEMP_PATH (str): The path to the temporary directory used for any files post-processing.
    BASE_PATH (str): The path to the directory containing the main python file when running the script
"""
from datetime import datetime
from time import sleep
from asyncio import sleep as async_sleep
from typing import Callable
from atexit import register

from lib.modules.display import Logger
from lib.modules.paths import Path, PathLike, TEMP_PATH, USERPROFILE


logger = Logger('[files]')


def sync_folders(path_a: PathLike, path_b: PathLike) -> None:
    """
    Recursively synchronizes files and folders between two directories.
    Copies files and folders that don't exist on the opposite side, without updating existing items.
    """
    source_path = Path(path_a, 'Directory', assert_exists=True)
    destination_path = Path(path_b, 'Directory')

    for _ in range(2):
        destination_path(exist_ok=True)

        for item in source_path:
            src_item = source_path * item.full_name
            dest_item = destination_path * item.full_name

            if item.is_dir_path:
                sync_folders(src_item, dest_item)
            elif item.is_file_path and not dest_item.exists:
                src_item.copy_to(dest_item)
        source_path, destination_path = destination_path, source_path

def last_file(target_dir: PathLike, name: str, n: int=1, new: str | None=None, list_only: bool=False) -> PathLike | list[PathLike]:
    """
    Retrieves the last modified file(s) in a directory that match a given name pattern.

    Parameters:
    ----------
        target_dir (str): The directory to search.
        name (str): The name pattern to match.
        n (int): The number of files to retrieve.
        new (str, optional): New extension or suffix for the file(s).
        list_only (bool, optional): If true, returns a list even if only one file is found.

    Returns:
    -------
        str | list[str]: The path(s) to the last modified file(s) matching the pattern.
    """
    target_dir = Path(target_dir, 'Directory')
    paths = [path for path in target_dir.childs if path.name.startswith(name)]
    nbrs = [int(path.name.replace(name, "")) for path in paths if path.name.replace(name, "").isdigit()]

    sorted_nbrs = sorted(nbrs, reverse=True)[:n]

    if len(sorted_nbrs) == 0:
        if new is not None:
            result = target_dir * f'{name}1{new}' if n == 1 else [target_dir * f'{name}{numero+1}{new}' for numero in range(n)]
        else:
            result = None if n == 1 else []
    else:
        if n == 1:
            result = target_dir * f'{name}{sorted_nbrs[0]+1}{new}'\
                if new is not None else target_dir * f'{name}{sorted_nbrs[0]}{paths[nbrs.index(sorted_nbrs[0])].extension}'
        else:
            result = [target_dir * f'{name}{numero}{new}' for numero in [sorted_nbrs[0] + 1 + i for i in range(n)]]\
                if new is not None else [target_dir * f'{name}{numero}{path.extension}' for numero, path in zip(sorted_nbrs, paths)][::-1]
    if list_only:
        if not isinstance(result, (list, tuple)):
            result = [result]
    return result
    
def redirect_from_downloads(
        download_func: Callable[..., None],
        dest_path: PathLike,
        src_name_template: str='',
        iteration_delay: float=0.25,
        start_download_time_limit: float=10,
        end_download_time_limit: float=60
    ) -> None:
    """
    Redirects a file downloaded from the web to a specified destination path.

    This function monitors the Downloads directory for new files and moves the most recently downloaded file to the specified destination path.

    Parameters:
    ----------
        download_func (callable): A function that initiates the download process.
        dest_path (str): The destination path where the downloaded file will be moved.
        iteration_delay (float): The delay (in seconds) between each check for new downloads. Default is 0.1 seconds.
        time_limit (float): The maximum time (in seconds) to wait for the download to appear in the Downloads directory. Default is 30 seconds.
    """
    dest_path = Path(dest_path)
    if dest_path.exists:
        raise PermissionError(f'Dest path: {dest_path.relative} already exists')

    downloads_path = USERPROFILE * 'Downloads'

    total_time = 0
    if dest_path.extension in src_name_template:
        download_path = downloads_path * src_name_template
        download_func()
    else:
        i_crdownload_paths = [p for p in downloads_path if p.extension == ".crdownload"]

        if not getattr(async_redirect_from_downloads, 'initialized', False):
            [p.remove(send_to_trash=False) for p in i_crdownload_paths]
            async_redirect_from_downloads.initialized = True

        download_func()

        def get_crdownload_path() -> PathLike:
            nonlocal total_time
            while True:
                for new_download_path in downloads_path:
                    if ((new_download_path.extension == ".crdownload")
                        and (src_name_template in new_download_path.full_name)
                        and (not (new_download_path in i_crdownload_paths))):
                        return new_download_path
                sleep(iteration_delay)
                total_time += iteration_delay
                if total_time > start_download_time_limit:
                    raise RuntimeError(f'Limit time: {start_download_time_limit} exceeded. No downloaded file started')

        crdownload_path = get_crdownload_path()
        download_path = crdownload_path.replace(".crdownload", '')
        i = 1
        while crdownload_path.exists and download_path.exists:
            download_path = download_path.parent * f'{download_path.name.replace(f" ({i-1})", "")} ({i}){download_path.extension}'
            i += 1

    def wait_download_path():
        nonlocal total_time
        while True:
            for new_download_path in downloads_path:
                if new_download_path == download_path:
                    return

                sleep(iteration_delay)
                total_time += iteration_delay
                if total_time > end_download_time_limit:
                    raise RuntimeError(f'Limit time: {end_download_time_limit} exceeded. No downloaded file found')

    wait_download_path()
    sleep(0.25)
    download_path.move_to(dest_path)

async def async_redirect_from_downloads(
        download_func: Callable[..., None],
        dest_path: PathLike,
        src_name_template: str='',
        iteration_delay: float=0.25,
        start_download_time_limit: float=10,
        end_download_time_limit: float=60
    ) -> None:
    """
    (async) Redirects asyncronously a file downloaded from the web to a specified destination path.

    This function monitors the Downloads directory for new files and moves the most recently downloaded file to the specified destination path.

    Parameters:
    ----------
        download_func (callable): A function that initiates the download process.
        dest_path (str): The destination path where the downloaded file will be moved.
        iteration_delay (float): The delay (in seconds) between each check for new downloads. Default is 0.1 seconds.
        time_limit (float): The maximum time (in seconds) to wait for the download to appear in the Downloads directory. Default is 30 seconds.
    """
    dest_path = Path(dest_path)
    if dest_path.exists:
        raise PermissionError(f'Dest path: {dest_path.relative} already exists')

    downloads_path = USERPROFILE * 'Downloads'

    total_time = 0
    if dest_path.extension in src_name_template:
        download_path = downloads_path * src_name_template
        download_func()
    else:
        i_crdownload_paths = [p for p in downloads_path if p.extension == ".crdownload"]

        if not getattr(async_redirect_from_downloads, 'initialized', False):
            [p.remove(send_to_trash=False) for p in i_crdownload_paths]
            async_redirect_from_downloads.initialized = True

        download_func()

        def get_crdownload_path() -> PathLike:
            nonlocal total_time
            while True:
                for new_download_path in downloads_path:
                    if ((new_download_path.extension == ".crdownload")
                        and (src_name_template in new_download_path.full_name)
                        and (not (new_download_path in i_crdownload_paths))):
                        return new_download_path
                sleep(iteration_delay)
                total_time += iteration_delay
                if total_time > start_download_time_limit:
                    raise RuntimeError(f'Limit time: {start_download_time_limit} exceeded. No downloaded file started')

        crdownload_path = get_crdownload_path()
        download_path = crdownload_path.replace(".crdownload", '')
        i = 1
        while crdownload_path.exists and download_path.exists:
            download_path = download_path.parent * f'{download_path.name.replace(f" ({i-1})", "")} ({i}){download_path.extension}'
            i += 1

    async def wait_download_path():
        nonlocal total_time
        while True:
            for new_download_path in downloads_path:
                if new_download_path == download_path:
                    return

                await async_sleep(iteration_delay)
                total_time += iteration_delay
                if total_time > end_download_time_limit:
                    raise RuntimeError(f'Limit time: {end_download_time_limit} exceeded. No downloaded file found')

    await wait_download_path()
    await async_sleep(0.25)
    download_path.move_to(dest_path)

class TempFolderCleaner:
    """
    A class to manage the cleaning of a temporary folder.

    This class provides methods to clear the contents of a specified directory, optionally sending them to the trash instead of deleting them permanently.
    It also ensures that the directory is cleared when the instance is deleted.

    Attributes:
    ----------
        temp_path (PathLike): The path to the directory to be cleaned.
        definitly (bool): If True, the contents are deleted permanently; otherwise, they are sent to the trash.

    Methods:
    -------
        clear(): Clears the contents of the specified directory.
        __del__(): Ensures the directory is cleared when the instance is deleted.
    """


    def __init__(self, temp_path: PathLike=TEMP_PATH, definitly: bool=False, init_clear: bool=False, uninit_clear: bool=False, bin_path: PathLike=None) -> None:
        self.temp_path = Path(temp_path, 'Directory')
        self.definitly = definitly
        self.bin_path = Path(bin_path, 'Directory') if bin_path is not None else None
        if init_clear:
            self.clear()
        if uninit_clear:
            register(self.close)

    def clear(self):
        if self.temp_path.childs:
            logger.info(f'Temp folder: {self.temp_path} cleared')
        if self.bin_path is None:
            self.temp_path.clear(send_to_trash=not self.definitly)
        else:
            for child in self.temp_path.childs:
                if self.definitly:
                    child.remove(send_to_trash=False)
                else:
                    new_path = self.bin_path * child.full_name
                    if new_path.exists:
                        new_path = last_file(new_path.parent, new_path.name, new=new_path.extension, list_only=False) # Use incrementation to find a new name for the file
                    child.move_to(new_path)
    
    def close(self) -> None:
        try:
            self.clear()
        except Exception as e:
            logger.warn(f"Error skipped when cleaning temp folder: '{str(self.temp_path.relative)}'")

def folder_backup(folder_path: PathLike, backup_working_dir_path: PathLike=None, replace_previous_backup: bool=False) -> None:
    """
    Backs up a folder to a specified path.

    This function creates a compressed archive of the specified folder and saves it to the backup path.
    If no backup path is provided, it uses the TEMP_PATH directory.

    Parameters:
    ----------
        folder_path (str): The path to the folder to be backed up.
        backup_path (str, optional): The path where the backup will be saved. If not provided, it defaults to TEMP_PATH.
    """
    folder_path = Path(folder_path, 'Directory', assert_exists=True)
    backup_working_dir_path = folder_path.parent if backup_working_dir_path is None else Path(backup_working_dir_path, 'Directory', assert_exists=True)
    backups_folder_path = backup_working_dir_path * f'{folder_path.name}_backups'
    if backups_folder_path.exists:
        if replace_previous_backup:
            assert all(path.full_name.startswith(f'{folder_path.name}_backup_') and path.full_name.endswith('.zip') for path in backups_folder_path.childs),\
                f'All files in {backups_folder_path} must start with {folder_path.name}_backup_ and end with .zip'
            backups_folder_path.clear(send_to_trash=True)
    else:
        backups_folder_path()
    backup_path = backups_folder_path * f'{folder_path.name}_backup_{datetime.now():%Y-%m-%d_%H-%M-%S}.zip'
    folder_path.as_zip(backup_path)


def folder_restore(folder_path: PathLike, backup_path: PathLike=None) -> None:
    """
    Restores a folder from a specified backup path.

    This function extracts the contents of a compressed archive from the backup path and saves it to the specified folder path.
    If no backup path is provided, it uses the TEMP_PATH directory.
    """
    raise NotImplementedError
