import typing as ty
from copy import deepcopy
from atexit import register

from lib.modules.paths import Path, PathLike

from lib import utils


class JSONSaver:

    def __init__(self,
            json_path: PathLike = None,
            default: utils.JSONType | None = None,
            conv_type: type[list | set | dict] | None = None,
            auto_save: bool = True
        ) -> None:
        if default is not None:
            utils.assert_is_json_serializable(default)

        self.set_json_path(json_path)
        self._data = self._json_path.read(default=default) if (self._json_path is not None) and self._json_path.exists else default

        self._initial_type = type(self._data)
        if conv_type is not None:
            self._data = conv_type(self._data)

        self._initial_data = deepcopy(self._data)
        
        self._auto_save = auto_save
        register(self.atexit)
    
    def atexit(self) -> None:
        if self._auto_save:
            self.save()

    def set_json_path(self, json_path: PathLike) -> None:
        self._json_path = Path(json_path, 'File')
        self._initial_json_path = None if self._json_path is None else self._json_path.copy()

    def save(self) -> None:
        if (self._initial_data != self._data) and (self._json_path is not None):
            data = self._initial_type(self._data)
            utils.assert_is_json_serializable(data)
            self._json_path.write(data, overwrite=True, send_to_trash=False)
            self._initial_data = deepcopy(self._data)

    def __getattr__(self, name: str):
        if '_data' in self.__dict__:
            return self._data.__getattribute__(name)
        raise AttributeError('Attribute _data not found.')
    
    def __bool__(self) -> bool: return self._data.__bool__()
    def __len__(self) -> int: return len(self._data) 
    def __contains__(self, key: ty.Any) -> bool: return self._data.__contains__(key)
    def __iter__(self) -> ty.Iterator: return self._data.__iter__()
    def __str__(self) -> str: return self._data.__str__()
    def __repr__(self) -> str: return self._data.__repr__()
    def __getitem__(self, key: ty.Any) -> ty.Any: return self._data.__getitem__(key)
    def __setitem__(self, key: ty.Any, value: ty.Any) -> ty.Any: return self._data.__setitem__(key, value)
    def __delitem__(self, key: ty.Any) -> ty.Any: return self._data.__getitem__(key)

class Counter:
    def __init__(self, val: ty.Union[int, 'Counter'] = 0):
        self.val = val.val if isinstance(val, Counter) else val

    def increment(self, inc_val: int = 1) -> None:
        self.val += inc_val

    def decrement(self, dec_val: int = 1) -> None:
        self.val -= dec_val

    def set(self, new_val: int) -> None:
        self.val = new_val
    
    def get(self) -> int:
        return self.val

    def __add__(self, other: ty.Union[int, 'Counter']) -> 'Counter':
        if isinstance(other, self.__class__):
            return self.__class__(self.val + other.val)
        return self.__class__(self.val + other)

    def __sub__(self, other: ty.Union[int, 'Counter']) -> 'Counter':
        if isinstance(other, self.__class__):
            return self.__class__(self.val - other.val)
        return self.__class__(self.val - other)

    def __mul__(self, other: ty.Union[int, 'Counter']) -> 'Counter':
        if isinstance(other, self.__class__):
            return self.__class__(self.val * other.val)
        return self.__class__(self.val * other)

    def __truediv__(self, other: ty.Union[int, 'Counter']) -> 'Counter':
        if isinstance(other, self.__class__):
            return self.__class__(self.val / other.val)
        return self.__class__(self.val / other)

    def __eq__(self, other: ty.Union[int, 'Counter']) -> bool:
        if isinstance(other, self.__class__):
            return self.val == other.val
        return self.val == other

    def __lt__(self, other: ty.Union[int, 'Counter']) -> bool:
        if isinstance(other, self.__class__):
            return self.val < other.val
        return self.val < other

    def __le__(self, other: ty.Union[int, 'Counter']) -> bool:
        if isinstance(other, self.__class__):
            return self.val <= other.val
        return self.val <= other

    def __gt__(self, other: ty.Union[int, 'Counter']) -> bool:
        if isinstance(other, self.__class__):
            return self.val > other.val
        return self.val > other

    def __ge__(self, other: ty.Union[int, 'Counter']) -> bool:
        if isinstance(other, self.__class__):
            return self.val >= other.val
        return self.val >= other

    def __str__(self) -> str:
        return str(self.val)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.val})"

    def __int__(self) -> int:
        return self.val
    
    def __round__(self, ndigits: None = None) -> int:
        return round(self.val, ndigits)