import typing
import os
import json
import shutil
import gzip
from sys import modules
from send2trash import send2trash
from time import time


PathLike = typing.Union[str, 'File', 'Directory']
PathLikeObject = typing.Union['File', 'Directory']
DirLike = typing.Union[str, 'Directory']


class MetaTrash(type):

    def __setattr__(cls, name: str, value: typing.Any) -> None:
        if name == 'default_trash_path':
            raise ValueError('Can not change value of default_trash_path')
        if name == 'trash_path' and value != cls.default_trash_path:
            value = Path(value, 'Directory', assert_exists=True)
        return super().__setattr__(name, value)

class Trash(metaclass=MetaTrash):

    default_trash_path = 'Default:Trash:Path'
    trash_path: PathLike = default_trash_path

    @classmethod
    def set_trash_path(cls, new_trash_path: PathLike | None = None) -> PathLike:
        cls.trash_path = Path(new_trash_path, 'Directory', assert_exists=True) or cls.default_trash_path
        return cls.trash_path

    @classmethod
    def send_to_trash(cls, paths: str | list[str] | tuple[str]) -> None:
        if isinstance(paths, (str, PurePath)):
            paths = [paths]
        if cls.trash_path == cls.default_trash_path:
            send2trash([(path.fs if isinstance(path, PurePath) else path) for path in paths])
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
    def auto_cleanup(cls, days: int = 30) -> None:
        """Removes files and directories older than 'days' from the trash folder.
        
        Args:
            days (int): Number of days to keep files before deletion. Defaults to 30.
        """
        if cls.trash_path == cls.default_trash_path:
            return  # Skip cleanup when using system trash
            
        now = time()
        cutoff_time = now - (days * 86400)  # 86400 seconds in a day
        
        for child in cls.trash_path.childs:
            if child.ctime < cutoff_time:
                send2trash(child.fs)
                print(f"Deleted: {child.relative}")

def normpath(path: str) -> str:
    path = str(path)
    if path:
        if str(WORKINGDRIVE).lower() in path:
            path = path[0].upper() + path[1:]
        elif len(path) != 1 and (path[0] == os.path.sep or path[0] == os.path.sep):
            path = path[1:]
    else:
        path = os.path.sep
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
                def find_obj() -> PathLike:
                    for sub_class in cls.__subclasses__():
                        if os.path.splitext(path)[-1] in sub_class.SUPPORTED_EXTS:
                            return sub_class(path)
                    return Directory(path)
            else:
                def find_obj() -> PathLike:
                    for sub_class in cls.__subclasses__():
                        if sub_class.__name__ == sub_class_name:
                            return sub_class(path)
                    raise AttributeError(f'Invalid sub class name: {sub_class_name}')
        else:
            if sub_class_name is not None:
                if path.__class__.__name__ != sub_class_name:
                    raise AttributeError(f'Path: {path} must be a {sub_class_name} object with no instance reset param')
            find_obj = lambda: path
        new_obj = find_obj()
        if assert_exists:
            if not new_obj.exists:
                raise FileNotFoundError(f'Path: {new_obj.path} must exists with param assert_exists on')
        return new_obj

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
    def extension(self) -> str:
        if self.path.endswith(os.path.sep):
            return ''
        return os.path.splitext(self.path)[-1]

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
        return not WORKINGDRIVE in path
    
    @staticmethod
    def is_absolute(path: PathLike) -> bool:
        return WORKINGDRIVE in path

    @property
    def fs(self) -> str:
        """Returns the file system path of the object"""
        return self.absolute.path

    @property
    def is_file_path(self) -> bool:
        return self.extension in File.SUPPORTED_EXTS

    @property
    def is_dir_path(self) -> bool:
        return not self.is_file_path

    def copy(self) -> PathLikeObject:
        return self.__class__(self.path)

    def update(self) -> None:
        path = PurePath.from_sub_class(self.path)
        self.__class__ = path.__class__
        self.__dict__ = path.__dict__

    def replace(self, old: str, new: str) -> PathLikeObject:
        return PurePath.from_sub_class(self.path.replace(old, new))
    
    def split_component(self) -> list[str]:
        return str(self.path).replace('\\', os.path.sep).split(os.path.sep)
    
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
        except PermissionError:
            return False

    def move_to(self, dst_path: PathLike, send_to_trash: bool=True, overwrite: bool=False) -> None:
        dst_path = PurePath.from_sub_class(dst_path, reset_instance=False)
        assert type(self) == type(dst_path), f'Impossible to move {self.relative} to {dst_path.relative}'
        if self != dst_path:
            if dst_path.exists:
                if overwrite:
                    dst_path.remove(send_to_trash=send_to_trash)
                else:
                    raise FileExistsError(f'Dest path: {dst_path.relative} already exists')
            shutil.move(self.fs, dst_path.fs)
    
    @property
    def ctime(self) -> float:
        return os.path.getctime(self.path)
    
    def __add__(self, other: PathLike) -> PathLikeObject:
        return self.copy().__iadd__(other)
    
    def __iadd__(self, other: PathLike) -> PathLikeObject:
        self.path += str(other)
        self.update()
        return self
    
    def __sub__(self, other: PathLike) -> PathLikeObject:
        return self.copy().__isub__(other)
    
    def __isub__(self, other: PathLike) -> PathLikeObject:
        if self.path.endswith(str(other)):
            self.path = self.path.replace(str(other), '')
        self.update()
        return self
    
    def __truediv__(self, other: PathLike) -> PathLikeObject:
        return self.copy().__itruediv__(other)
    
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

    def __getitem__(self, index: typing.SupportsIndex | slice) -> str:
        return self.path[index]
    
    def __getattr__(self, name: str) -> typing.Any:
        if not '_path' in self.__dict__:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
        return getattr(self._path, name)


class Directory(PurePath):

    SUPPORTED_EXTS = ['']

    def __init__(self, path: PathLike=os.path.sep):
        super().__init__(path)
        if not self.is_dir_path:
            raise NotADirectoryError(f'Can not create Directory object from path: {path}')
    
    @property
    def full_name(self) -> str:
        return os.path.basename(self.fs)

    @property
    def name(self) -> str:
        return self.full_name
    
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
    def as_zip(self) -> 'Zip':
        return Zip(self.path)
    
    @property
    def childs(self) -> list[PathLikeObject]:
        return [PurePath.from_sub_class(os.path.join(self.fs, name)) for name in os.listdir(self.fs)]
    
    def child(self, child_name: str) -> PathLikeObject:
        return self * child_name
    
    def copy_to(self, dst_path: PathLike, overwrite: bool=False, send_to_trash=True) -> None:
        dst_path = PurePath.from_sub_class(dst_path, 'Directory', reset_instance=False)
        if self.fs != dst_path.fs:
            if dst_path.exists:
                if overwrite:
                    dst_path.remove(send_to_trash=send_to_trash)
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

    def __call__(self, mode: int=511, exist_ok: bool=False) -> 'Directory':
        os.makedirs(self.fs, mode, exist_ok)
        return self
    
    def __len__(self) -> int:
        return len(os.listdir(self.fs))
    
    def __iter__(self) -> typing.Iterator[PathLikeObject]:
        return iter(self.childs)
    
    def __getitem__(self, key: str) -> str:
        return 

    def __getitem__(self, key: int | slice | str) -> str:
        return self.child(key) if isinstance(key, str) else super().__getitem__(key)
    
    def __delitem__(self, child_name: str) -> None:
        self.child(child_name).remove()

    def __mul__(self, other: PathLike) -> PathLikeObject:
        return self.copy().__imul__(other)

    def __imul__(self, other: PathLike) -> PathLikeObject:
        self.path = os.path.join(self.fs, str(other))
        self.update()
        return self


class File(PurePath):

    SUPPORTED_EXTS = [
            '.txt', '.log', '.json', '.gz', '.py', '.pyw', '.html', '.htm', 
            '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', 
            '.pdf', '.csv', '.xml', '.yaml', '.yml', 
            '.tar', '.bz2', '.7z', '.rar',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg', 
            '.mp3', '.wav', '.ogg', '.flac', 
            '.mp4', '.avi', '.mkv', '.mov', '.wmv', 
            '.exe', '.dll', '.bat', '.sh', '.cmd',
            '.db', '.sql', '.dump',
            '.c', '.cpp', '.h', '.hpp', '.java', '.class', '.jar', 
            '.rb', '.php', '.js', '.ts', '.css', '.scss', 
            '.go', '.rs', '.swift', '.kt', '.dart',
            '.aep', '.jsx', '.ffx'
        ]
    
    def __init__(self, path: PathLike):
        super().__init__(path)
        if not self.is_file_path:
            raise IsADirectoryError(f'Can note create a File object from path: {path}')

    @property
    def full_name(self) -> str:
        return os.path.basename(self.fs)
    
    @property
    def name(self) -> str:
        return os.path.splitext(os.path.basename(self.fs))[0]
    
    def rename(self, new_name: str) -> PathLike:
        new_path = self.parent * new_name
        os.rename(self.fs, new_path.fs)
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
    
    def read(self, default: typing.Any='', mode: str | None=None) -> typing.Any:
        ext = self.extension
        if not ext in File.SUPPORTED_EXTS:
            raise NotImplementedError(f'Can not use read function for file: {self.relative}')
        data = ''
        if ext in ['.txt', '.py', '.html', '.log']:
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
    
    def write(self, data: typing.Any, overwrite: bool=True, send_to_trash: bool=True, mode: str | None=None) -> None:
        ext = self.extension
        if not ext in File.SUPPORTED_EXTS:
            raise NotImplementedError(f'Can not use read function for file: {self.relative}')
        if overwrite:
            self.remove(send_to_trash, not_exists_ok=True)
        if self.exists:
            raise FileExistsError(f'Can not overwrite file: {self.relative}')
        else:
            if ext in ['.txt', '.py', '.log', '.yml', '.yaml']:
                with open(self.fs, 'w' if mode is None else mode) as file:
                    file.write(data)
            elif ext == '.json':
                with open(self.fs, 'w' if mode is None else mode) as file:
                    json.dump(data, file, indent=4)
            elif ext == '.gz':
                with gzip.open(self.fs, 'wt' if mode is None else mode) as file:
                    if isinstance(data, str):
                        file.write(data)
                    elif isinstance(data, bytes):
                        with gzip.open(self.fs, 'wb') as binary_file:
                            binary_file.write(data)
                    else:
                        raise ValueError(f"For GZ files, data should be a string or bytes not: {data}")
            elif ext == '.mp4':
                if isinstance(data, bytes):
                    with open(self.fs, 'wb') as video_file:
                        video_file.write(data)
                elif hasattr(data, 'content'):
                    with open(self.fs, 'wb') as video_file:
                        video_file.write(data.content)
                elif hasattr(data, 'iter_content'):
                    with open(self.fs, 'wb') as video_file:
                        for chunk in data.iter_content(chunk_size=1024):
                            if chunk:
                                video_file.write(chunk)
                else:
                    raise ValueError(f"Unsupported data type for MP4 file: {type(data)}")
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
        
    def copy_to(self, dst_path: PathLike, overwrite: bool=False, send_to_trash: bool=True) -> None:
        dst_path = PurePath.from_sub_class(dst_path, 'File', reset_instance=False)
        if self.fs != dst_path.fs:
            if dst_path.exists:
                if overwrite:
                    dst_path.remove(send_to_trash=send_to_trash)
                else:
                    raise FileExistsError(f'Dest path: {dst_path.relative} already exists')
            shutil.copy2(self.fs, dst_path.fs)

    @property
    def size(self) -> int:
        return os.path.getsize(self.fs)


class Zip(PurePath):

    SUPPORTED_EXTS = ['.zip']

    def __init__(self, path_a: PathLike=os.path.sep, path_b: PathLike=None):
        self._path = ''
        self.dst_path = ''
        (self.set_dst_path(path_a) if path_a.extension == Zip.SUPPORTED_EXTS[0] else self.set_src_path(path_a))\
            if isinstance(path_a, PurePath) else\
        (self.set_dst_path(path_a) if path_a.endswith(Zip.SUPPORTED_EXTS[0]) else self.set_src_path(path_a))

        if path_b:
            self.set_src_path(path_b) if not self.path else self.set_dst_path(path_b)

    def set_src_path(self, src_path: PathLike) -> None:
        super().__init__(src_path)

    def set_dst_path(self, dst_path: PathLike=None) -> None:
        if dst_path is None:
            self.dst_path = os.path.splitext(self.path)[0] + Shortcut.SUPPORTED_EXTS[0]
        else:
            if isinstance(dst_path, PurePath):
                if not isinstance(dst_path, Zip):  
                    raise AttributeError(f'Invalid argument dst: {dst_path}')
                self.dst_path = dst_path.dst_path
            elif isinstance(dst_path, str):
                if not dst_path.endswith(Zip.SUPPORTED_EXTS[0]):
                    raise AttributeError(f'Invalid argument dst: {dst_path}')
                self.dst_path = dst_path
            else:
                raise AttributeError(f'Invalid argument dst: {dst_path}')

    @property
    def exists(self) -> bool:
        return self.dst_path and os.path.exists(self.dst_path)

    extension = SUPPORTED_EXTS[0]

    def copy(self) -> PathLikeObject:
        return Zip(self.path, self.dst_path)
    
    def unpack(self, overwrite: bool=False, send_to_trash: bool=True, exist_ok: bool=False) -> PathLikeObject:
        assert self.path, 'Source not setted'
        assert self.dst_path, 'Dest not setted'
        if not self.exists:
            raise FileNotFoundError(f"The dest folder '{self.relative}' does not exist.")
        if os.path.exists(self.path):
            print('Source already exists')
            if not exist_ok:
                if overwrite:
                    PurePath.from_sub_class(self.path).remove(send_to_trash=send_to_trash)
                    shutil.unpack_archive(self.dst_path, self.fs, Zip.SUPPORTED_EXTS[0])
                else:
                    raise FileExistsError(f'Can not unpack a zip to: {self.relative}')
        else:
            shutil.unpack_archive(self.dst_path, self.fs, Zip.SUPPORTED_EXTS[0])
        return PurePath.from_sub_class(self.path)

    def __call__(self, dst_path: PathLike=None, exist_ok: bool=False) -> 'Zip':
        if dst_path is not None:
            self.set_dst_path(dst_path)
        assert self.path, 'Source not setted'
        assert self.dst_path, 'Dest not setted'
        print(f'Saving a compressed copy of folder {self.path} to {self.dst_path}...')
        if not os.path.exists(self.path):
            raise FileNotFoundError(f"The source path: '{self.path}' does not exist.")
        if not self.exists:
            shutil.make_archive(self.dst_path.removesuffix(Zip.SUPPORTED_EXTS[0]), Zip.SUPPORTED_EXTS[0].removeprefix('.'), self.path)
            print("Done")
        else:
            print('Zip folder already exists')
            if not exist_ok:
                raise FileExistsError(f'Can not create a zip to: {self.relative}')
        return self
    
    def copy_to(self, dst_path: PathLike, overwrite: bool=False, send_to_trash=True) -> None:
        dst_path = PurePath.from_sub_class(dst_path, 'Zip', reset_instance=False)
        if self.fs != dst_path.fs:
            if dst_path.exists:
                if overwrite:
                    dst_path.remove(send_to_trash=send_to_trash)
                else:
                    raise FileExistsError(f'Dest path: {dst_path.relative} already exists')
            shutil.copy2(self.dst_path, dst_path.fs)

    def remove(self, send_to_trash: bool=True, not_exists_ok: bool=True) -> None:
        if os.path.exists(self.dst_path):
            if send_to_trash:
                Trash.send_to_trash(self.dst_path)
            else:
                os.remove(self.fs)
        elif not not_exists_ok:
            raise FileNotFoundError(f'Path: {self.relative} not found')

    @property
    def size(self) -> int:
        return os.path.getsize(self.dst_path)

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
USERNAME = os.environ['USERNAME']
HOMEDRIVE = os.environ['HOMEDRIVE']
WORKINGDRIVE = BASE_PATH.split(os.path.sep, 1)[0] + os.path.sep
USERPROFILE = os.environ['USERPROFILE']
PROGRAMFILES = os.environ['PROGRAMFILES']
PROGRAMFILESX86 = os.environ['PROGRAMFILES(X86)']
PROGRAMDATA = os.environ['PROGRAMDATA']
try:
    MAIN_PYTHON_FILE = modules['__main__'].__file__
except AttributeError:
    MAIN_PYTHON_FILE = None

TEMP_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'TEMP')

BASE_PATH = BasePath(BASE_PATH)

HOMEDRIVE = Directory(HOMEDRIVE)

WORKINGDRIVE = Directory(WORKINGDRIVE)

USERPROFILE = Directory(USERPROFILE)

PROGRAMFILES = Directory(PROGRAMFILES)

PROGRAMFILESX86 = Directory(PROGRAMFILESX86)

PROGRAMDATA = Directory(PROGRAMDATA)

MAIN_PYTHON_FILE = File(MAIN_PYTHON_FILE)

TEMP_PATH = Directory(TEMP_PATH)

