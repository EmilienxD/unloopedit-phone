import typing as ty
import os
import json
import shutil
import gzip

from sys import modules
from time import time


PathLike = ty.Union[str, 'File', 'Directory']
PathLikeObject = ty.Union['File', 'Directory']
DirLike = ty.Union[str, 'Directory']


class MetaTrash(type):

    def __setattr__(cls, name: str, value: ty.Any) -> None:
        if name == Trash.default_trash_path:
            raise ValueError(f'Can not change the default system trash placeholder: "{Trash.default_trash_path}"')
        if name == 'trash_path' and value != cls.default_trash_path:
            value = Path(value, 'Directory')
            value(exist_ok=True)
        return super().__setattr__(name, value)

class Trash(metaclass=MetaTrash):

    default_trash_path = 'Default:Trash:Path'
    trash_path: PathLike = default_trash_path

    @classmethod
    def set_trash_path(cls, new_trash_path: PathLike | None = None) -> PathLike:
        cls.trash_path = Path(new_trash_path, 'Directory') or cls.default_trash_path
        return cls.trash_path

    @classmethod
    def send_to_trash(cls, paths: str | list[str] | tuple[str]) -> None:
        if isinstance(paths, (str, PurePath)):
            paths = [paths]
        if cls.trash_path == cls.default_trash_path:
            [Path(path).remove(send_to_trash=False) for path in paths]
        else:
            paths: list[PathLikeObject] = [Path(path) for path in paths]
            new_path_dsts: list[PathLikeObject] = [cls.trash_path * path.full_name for path in paths]
            for path, new_path_dst in zip(paths, new_path_dsts):
                i = 1
                while new_path_dst.exists:
                    new_path_dst = new_path_dst.parent * f'{new_path_dst.name.replace(f" ({i-1})", "")} ({i}){new_path_dst.extension}'
                    i += 1
                path.move_to(new_path_dst)
    
    @classmethod
    def auto_cleanup(cls, days: int = 30, max_size: float = 1.0) -> None:
        """Removes files and directories from the trash folder that are either:
        1. Older than specified number of days
        2. Exceeding the maximum size limit (oldest files removed first)
        
        Args:
            days (int): Number of days to keep files before deletion. Defaults to 30.
            max_size (float): Maximum size in GB for trash folder. Defaults to 1.0 GB.
        """
        if cls.trash_path == cls.default_trash_path:
            return  # Skip cleanup when using system trash
            
        now = time()
        cutoff_time = now - (days * 86400)  # 86400 seconds in a day
        
        # First pass - remove files older than cutoff
        for child in cls.trash_path.childs:
            if child.mtime < cutoff_time:
                child.remove(send_to_trash=False)
                print(f"Deleted old file: {child.relative}")
                
        # Second pass - check total size and remove oldest files if needed
        max_bytes = max_size * 1024 * 1024 * 1024  # Convert GB to bytes
        
        while cls.trash_path.size > max_bytes and cls.trash_path.childs:
            # Get oldest remaining file
            oldest = min(cls.trash_path.childs, key=lambda x: x.ctime)
            oldest.remove(send_to_trash=False)
            print(f"Deleted for size limit: {oldest.relative}")

def normpath(path: str) -> str:
    path = str(path)
    if path.replace('/', os.path.sep).replace('\\', os.path.sep) == os.path.sep:
        path = os.getcwd()
    if str(WORKINGDRIVE).lower() in path:
        path = path[0].upper() + path[1:]
    return os.path.normpath(path)

class PurePath:   #not compatible with shutil, pygame, subprocess operations -> need to call the fs form

    def __init__(self, path: PathLike=os.path.sep):
        if type(self) == PurePath:
            raise NotImplementedError('Do not use class PurePath as the main class')
        self.path = path

    @classmethod
    def from_sub_class(cls, path: PathLike=os.path.sep, sub_class_name: str | None=None, reset_instance: bool=True, assert_exists: bool=False) -> PathLikeObject:
        if reset_instance or type(path) == str:
            path = normpath(path)
            if path.startswith(f'~{os.path.sep}'):
                path = os.path.join(os.path.expanduser('~'), path.removeprefix(f'~{os.path.sep}'))
            if sub_class_name is None:
                if os.path.exists(path):
                    if os.path.isfile(path):
                        path = File(path)
                    else:
                        path = Directory(path)
                elif os.path.splitext(path)[-1]:
                    path = File(path)
                else:
                    path = Directory(path)
            else:
                if sub_class_name == File.__name__:
                    path = File(path)
                elif sub_class_name == Directory.__name__:
                    path = Directory(path)
                else:
                    raise AttributeError(f'Invalid sub class name: {sub_class_name}')
        else:
            if sub_class_name is not None:
                if not any(c.__name__ == sub_class_name for c in path.__class__.__mro__):
                    raise AttributeError(f'Path: {path.relative} must be a {sub_class_name} object with no instance reset param')

        if assert_exists:
            if not path.exists:
                raise FileNotFoundError(f'Path: {path.relative} must exists with param assert_exists on')
        return path

    @property
    def path(self) -> str:
        return self._path
    
    @path.setter
    def path(self, path: PathLike):
        if isinstance(path, str):
            self._path = normpath(path)
        elif isinstance(path, PurePath):
            self._path = path._path
        else:
            raise AttributeError(f'Can not create a Path object with path: {path.relative}')

    @property
    def parent(self) -> 'Directory':
        parent = Directory(os.path.dirname(self.fs))
        if parent.fs == self.fs:
            raise AttributeError(f'Can not get a parent from path: {self.relative}')
        return parent

    @property
    def relative(self) -> PathLikeObject:
        rel_copy = self.copy()
        if PurePath.is_absolute(rel_copy):
            rel_copy.path = rel_copy.path.split(BASE_PATH.fs, 1)[-1]
            if rel_copy.path.startswith(os.path.sep):
                rel_copy.path = rel_copy.path[1:]
        return rel_copy

    @property
    def absolute(self) -> PathLikeObject:
        abs_copy = self.copy()
        if abs_copy.path == os.path.sep:
            abs_copy.path = BASE_PATH.fs
        elif PurePath.is_relative(abs_copy):
            abs_copy.path = os.path.join(BASE_PATH.fs, abs_copy.path)
        return abs_copy

    @staticmethod
    def is_relative(path: PathLike) -> bool:
        return not str(WORKINGDRIVE) in path
    
    @staticmethod
    def is_absolute(path: PathLike) -> bool:
        return WORKINGDRIVE in path

    @property
    def fs(self) -> str:
        """Returns the file system path of the object"""
        if PurePath.is_relative(self.path):
            return os.path.join(BASE_PATH.fs, self.path)
        return self.path
    
    @property
    def ufs(self) -> str:
        return normpath(self.relative.path.replace('\\', os.path.sep).removeprefix(os.path.sep).removesuffix(os.path.sep
               )).replace(str(USERPROFILE), f'~')

    @property
    def is_file_path(self) -> bool:
        if os.path.isfile(self.fs):
            return True
        return bool(self.extension)

    @property
    def is_dir_path(self) -> bool:
        if os.path.exists(self.fs):
            return not os.path.isfile(self.fs)
        return not bool(self.extension)

    def copy(self) -> PathLikeObject:
        return self.__class__(self.path)

    def update(self) -> None:
        path = PurePath.from_sub_class(self.path)
        self.__class__ = path.__class__
        self.__dict__ = path.__dict__

    def replace(self, old: str, new: str) -> PathLikeObject:
        old = normpath(old)
        new = normpath(new)
        return PurePath.from_sub_class(self.path.replace(old, new).replace('\\', os.path.sep).removeprefix(os.path.sep).removesuffix(os.path.sep))
    
    def split_components(self) -> list[str]:
        return str(self.path.removeprefix('.').removeprefix('~')).replace('\\', os.path.sep).split(os.path.sep)
    
    def split(self, sep: str=os.path.sep, maxsplit: int=-1) -> list[PathLikeObject]:
        return [PurePath.from_sub_class(path) for path in str(self.path).replace('\\', os.path.sep).split(sep, maxsplit)]
    
    @property
    def siblings(self) -> list[PathLikeObject]:
        return [sibling for sibling in self.parent.childs if sibling != self]

    @property
    def is_accessible(self) -> bool:
        try:
            with open(self.fs, 'rb+'):
                return True
        except (FileNotFoundError, PermissionError):
            return False

    def move_to(self, dst_path: PathLike, send_to_trash: bool=True, overwrite: bool=False, exist_ok: bool=False) -> None:
        dst_path = PurePath.from_sub_class(dst_path)
        if self != dst_path:
            if dst_path.exists:
                if overwrite:
                    dst_path.remove(send_to_trash=send_to_trash)
                elif exist_ok:
                    self.remove(send_to_trash=send_to_trash)
                    return
                else:
                    raise FileExistsError(f'Dest path: {dst_path.relative} already exists')
            shutil.move(self.fs, dst_path.fs)
    
    @property
    def ctime(self) -> float:
        return os.path.getctime(self.fs)
    
    @property
    def mtime(self) -> float:
        return os.path.getmtime(self.fs)
    
    def __add__(self, other: PathLike) -> PathLikeObject:
        path = self.path + str(other)
        return PurePath.from_sub_class(path)
    
    def __iadd__(self, other: PathLike) -> PathLikeObject:
        self.path += str(other)
        self.update()
        return self
    
    def __sub__(self, other: PathLike) -> PathLikeObject:
        path = self.path.replace(str(other), '') if self.path.endswith(str(other)) else self.path
        return PurePath.from_sub_class(path)
    
    def __isub__(self, other: PathLike) -> PathLikeObject:
        if self.path.endswith(str(other)):
            self.path = self.path.replace(str(other), '')
        self.update()
        return self
    
    def __truediv__(self, other: PathLike) -> PathLikeObject:
        parent = self
        try:
            while parent.full_name != os.path.basename(str(other)):
                parent = parent.parent
        except ValueError:
            raise ValueError(f'Can not find: {other}')
        
        path = parent.parent.path
        return PurePath.from_sub_class(path)
    
    def __itruediv__(self, other: PathLike) -> PathLikeObject:
        parent = self
        try:
            while parent.full_name != os.path.basename(str(other)):
                parent = parent.parent
        except ValueError:
            raise ValueError(f'Can not find: {other}')
        self.path = parent.parent.path
        self.update()
        return self

    def __str__(self) -> str:
        return str(self.path)

    def __repr__(self) -> str:
        return repr(self.path)

    def __fspath__(self) -> str:
        return self.fs

    def __bytes__(self):
        return bytes(self.fs)

    def __eq__(self, other: PathLike) -> bool:
        return (self.fs == other.fs) if isinstance(other, PurePath) else self.fs == other

    def __hash__(self) -> int:
        return hash(self.fs)

    def __contains__(self, chars: PathLike) -> bool:
        return str(chars) in self.path
    
    def __bool__(self) -> bool:
        return bool(self.path)

    def __getitem__(self, index: ty.SupportsIndex | slice) -> str:
        return self.path[index]
    
    def __getattr__(self, name: str) -> ty.Any:
        if not '_path' in self.__dict__:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
        return getattr(self._path, name)


class Directory(PurePath):
    
    @property
    def full_name(self) -> str:
        return os.path.basename(self.fs)

    @property
    def name(self) -> str:
        return self.full_name
    
    @property
    def extension(self) -> str:
        return ''
    
    @property
    def no_extension(self) -> str:
        return self.copy()
    
    @property
    def exists(self) -> bool:
        return os.path.isdir(self.fs)
    
    def remove(self, send_to_trash: bool=True, not_exists_ok: bool=True) -> None:
        if self.exists:
            if send_to_trash:
                Trash.send_to_trash(self.fs)
            else:
                shutil.rmtree(self.fs)
        elif not not_exists_ok:
            raise FileNotFoundError(f'Path: {self.relative} not found')
        
    def clear(self, send_to_trash: bool=True, not_exists_ok: bool=True) -> None:
        if self.exists:
            if send_to_trash:
                Trash.send_to_trash([child.fs for child in self.childs])
            else:
                [path.remove(send_to_trash=False, not_exists_ok=False) for path in self.childs]
        elif not not_exists_ok:
            raise FileNotFoundError(f'Path: {self.relative} not found')
    
    @property
    def childs(self) -> list[PathLikeObject]:
        return [PurePath.from_sub_class(os.path.join(self.fs, name)) for name in os.listdir(self.fs)]
    
    def child(self, child_name: str) -> PathLikeObject:
        return self * child_name
    
    def copy_to(self, dst_path: PathLike, overwrite: bool=False, send_to_trash: bool=True, exist_ok: bool=False) -> None:
        dst_path = PurePath.from_sub_class(dst_path)
        if self.fs != dst_path.fs:
            if dst_path.exists:
                if overwrite:
                    dst_path.remove(send_to_trash=send_to_trash)
                elif exist_ok:
                    return
                else:
                    raise FileExistsError(f'Dest path: {dst_path.relative} already exists')
            shutil.copytree(self.fs, dst_path.fs)

    @property
    def size(self) -> int:
        if self.path == WORKINGDRIVE.path:
            return shutil.disk_usage('/')[1]
        total_size = 0
        for dirpath, _, filenames in os.walk(self.fs):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)
        return total_size
    
    def pack(self,
            dst_path: PathLike=None,
            overwrite: bool=False,
            send_to_trash: bool=True,
            exist_ok: bool=False
        ) -> 'File':
        if not self.exists:
            raise FileNotFoundError(f'Can not pack: "{self.relative}".')

        dst_path = File(dst_path or (self.parent * (self.name + ".zip")))

        if dst_path.exists:
            if overwrite:
                dst_path.remove(send_to_trash=send_to_trash)
            elif exist_ok:
                return dst_path
            else:
                raise FileExistsError(f'Can not pack: "{self.relative}"')

        shutil.make_archive(dst_path.no_extension.fs, dst_path.extension.removeprefix('.'), self.fs)
        return dst_path

    def __call__(self, mode: int=511, exist_ok: bool=False) -> 'Directory':
        os.makedirs(self.fs, mode, exist_ok)
        return self
    
    def __len__(self) -> int:
        return len(os.listdir(self.fs))
    
    def __iter__(self) -> ty.Iterator[PathLikeObject]:
        return iter(self.childs)
    
    def __getitem__(self, key: str) -> str:
        return 

    def __getitem__(self, key: int | slice | str) -> str:
        return self.child(key) if isinstance(key, str) else super().__getitem__(key)
    
    def __delitem__(self, child_name: str) -> None:
        self.child(child_name).remove()

    def __mul__(self, other: PathLike) -> PathLikeObject:
        path = os.path.join(self.fs, str(other))
        return PurePath.from_sub_class(path)

    def __imul__(self, other: PathLike) -> PathLikeObject:
        self.path = os.path.join(self.fs, str(other))
        self.update()
        return self


class File(PurePath):

    @property
    def full_name(self) -> str:
        return os.path.basename(self.fs)
    
    @property
    def name(self) -> str:
        return os.path.splitext(os.path.basename(self.fs))[0]
    
    @property
    def extension(self) -> str:
        return '.' + self.path.split('.')[-1]
    
    @property
    def no_extension(self) -> DirLike:
        return Directory(self.path.removesuffix(self.extension))
    
    def rename(self, new_name: str) -> PathLike:
        new_path = self.parent * new_name
        os.rename(self.fs, new_path.fs)
        self.path = new_path
        return new_path
    
    @property
    def exists(self) -> bool:
        return os.path.isfile(self.fs)
    
    def __call__(self, exist_ok: bool=False) -> 'File':
        assert self.parent.exists, f'Can not create a file at directory path: {self.parent.path}'
        if not self.exists:
            with open(self.fs, 'w') as file:
                file.write('')
        elif not exist_ok:
            raise FileExistsError(f'Can not create the file: {self.relative}')
        return self
    
    def read(self, default: ty.Any='', mode: str | None=None) -> ty.Any:
        ext = self.extension
        data = ''
        if ext in ['.txt', '.py', '.html', '.log', '.srt']:
            with open(self.fs, 'r' if mode is None else mode) as file:
                data = file.read()

        elif ext == '.json':
            try:
                with open(self.fs, 'r' if mode is None else mode) as file:
                    data = json.load(file)
            except json.JSONDecodeError:
                data = ''
        elif ext == '.gz':
            try:
                with gzip.open(self.fs, 'rt' if mode is None else mode) as file:  #mode: 'rt' or 'rb'
                    data = file.read()
            except (gzip.BadGzipFile, ValueError) as e:
                print(e)
                data = ''
        else:
            raise NotImplementedError(f'Can not use read function for file: {self.relative}')

        if data == '':
            data = default
        return data
    
    def write(self, data: ty.Any, overwrite: bool=True, send_to_trash: bool=True, mode: str | None=None) -> None:
        ext = self.extension
        if overwrite:
            self.remove(send_to_trash, not_exists_ok=True)
        if self.exists:
            raise FileExistsError(f'Can not overwrite file: {self.relative}')
        else:
            if ext in ['.txt', '.py', '.log', '.yml', '.yaml']:
                with open(self.fs, ('w' if mode is None else mode), encoding="utf-8") as file:
                    file.write(data)
            elif ext == '.json':
                with open(self.fs, ('w' if mode is None else mode), encoding="utf-8") as file:
                    json.dump(data, file, indent=4)
            elif ext == '.gz':
                with gzip.open(self.fs, ('wt' if mode is None else mode)) as file:
                    if isinstance(data, str):
                        file.write(data)
                    elif isinstance(data, bytes):
                        with gzip.open(self.fs, 'wb') as binary_file:
                            binary_file.write(data)
                    else:
                        raise ValueError(f"For GZ files, data should be a string or bytes not: {data}")
            elif ext in ('.mp4', '.mov', '.mkv', '.avi', '.webm',
                         '.mp3', '.m4a', '.wav', '.flac', '.aac', '.ogg',
                         '.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp',
                         '.zip'):
                if isinstance(data, bytes):
                    with open(self.fs, 'wb') as binary_file:
                        binary_file.write(data)
                elif hasattr(data, 'content'):
                    with open(self.fs, 'wb') as binary_file:
                        binary_file.write(data.content)
                elif hasattr(data, 'iter_content'):
                    with open(self.fs, 'wb') as binary_file:
                        for chunk in data.iter_content(chunk_size=1024):
                            if chunk:
                                binary_file.write(chunk)
                else:
                    raise ValueError(f"Unsupported data type for binary file: {type(data)}")
            else:
                raise NotImplementedError(f'Can not use write function for file: {self.relative}')

    def clear(self, overwrite: bool=True, send_to_trash: bool=True, not_exists_ok: bool=True) -> None:
        if self.exists:
            self.write('', overwrite, send_to_trash)
        elif not not_exists_ok:
            raise FileNotFoundError(f'Path: {self.relative} not found')

    def remove(self, send_to_trash: bool=True, not_exists_ok: bool=True) -> None:
        if self.exists:
            if send_to_trash:
                Trash.send_to_trash(self.fs)
            else:
                os.remove(self.fs)
        elif not not_exists_ok:
            raise FileNotFoundError(f'Path: {self.relative} not found')
        
    def copy_to(self, dst_path: PathLike, overwrite: bool=False, send_to_trash: bool=True, exist_ok: bool=False) -> None:
        dst_path = PurePath.from_sub_class(dst_path)
        if self.fs != dst_path.fs:
            if dst_path.exists:
                if overwrite:
                    dst_path.remove(send_to_trash=send_to_trash)
                elif exist_ok:
                    return
                else:
                    raise FileExistsError(f'Dest path: {dst_path.relative} already exists')
            shutil.copy2(self.fs, dst_path.fs)

    @property
    def size(self) -> int:
        return os.path.getsize(self.fs)
    
    def unpack(self,
            dst_path: PathLike,
            overwrite: bool=False,
            send_to_trash: bool=True,
            exist_ok: bool=False
        ) -> 'Directory':
        if not self.exists:
            raise FileNotFoundError(f'Can not unpack: "{self.relative}".')
        
        if not (ext := self.extension) in (".zip", ".tar", ".gztar", ".bztar", ".xztar"):
            raise ValueError(f'Can not unpack: "{self.relative}". Invalid extension: "{ext}"')
        del ext

        dst_path = Directory(dst_path)

        if dst_path.exists:
            if overwrite:
                dst_path.remove(send_to_trash=send_to_trash)
            elif exist_ok:
                return dst_path
            else:
                raise FileExistsError(f'Can not unpack: "{self.relative}"')
            
        shutil.unpack_archive(self.fs, dst_path.fs, self.extension.removeprefix('.'))
        return dst_path


class BasePath(Directory):

    @property
    def relative(self) -> PathLikeObject:
        return self

    @property
    def absolute(self) -> PathLikeObject:
        return self
    
    @property
    def fs(self) -> str:
        return self.path
    

def Path(path: PathLikeObject=os.path.sep, path_type: str='auto_detect', reset_instance: bool=False, assert_exists: bool=False) -> PathLikeObject:
    return None if path == None else PurePath.from_sub_class(
        path=path,
        sub_class_name=(None if path_type == 'auto_detect' else path_type),
        reset_instance=reset_instance,
        assert_exists=assert_exists
    )


BASE_PATH = os.getcwd()
USERNAME = os.getenv('USERNAME', 'mobile')
HOMEDRIVE = os.getenv('HOMEDRIVE', '/')
WORKINGDRIVE = BASE_PATH.split(os.path.sep, 1)[0] + os.path.sep
USERPROFILE = os.path.expanduser("~")
PROGRAMFILES = os.getenv('PROGRAMFILES', '/Applications')
PROGRAMFILESX86 = os.getenv('PROGRAMFILES(X86)', '/Applications')
PROGRAMDATA = os.getenv('PROGRAMDATA', '/var/mobile')

try:
    MAIN_PYTHON_FILE = modules['__main__'].__file__
except AttributeError:
    MAIN_PYTHON_FILE = os.path.join(BASE_PATH, '__main__.py')

TEMP_PATH = os.path.join(os.path.dirname(__file__), 'TEMP')

BASE_PATH = BasePath(BASE_PATH)

HOMEDRIVE = Directory(HOMEDRIVE)

WORKINGDRIVE = Directory(WORKINGDRIVE)

USERPROFILE = Directory(USERPROFILE)

PROGRAMFILES = Directory(PROGRAMFILES)

PROGRAMFILESX86 = Directory(PROGRAMFILESX86)

PROGRAMDATA = Directory(PROGRAMDATA)

MAIN_PYTHON_FILE = File(MAIN_PYTHON_FILE)

TEMP_PATH = Directory(TEMP_PATH)

