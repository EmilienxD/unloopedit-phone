"""
This module provides internal utility methods for working with functions within a script.
It includes functions to retrieve a list of functions defined in a module and to get the default arguments of a function.

Functions:
---------
    get_own_functions: Retrieves a list of functions defined in the specified module.
    get_func_kwargs: Retrieves a dictionary of default argument values for a specified function.
"""
import typing as ty
import sys
import inspect

from types import FunctionType

from src.modules.paths import Path, PathLike


def enable_folder_imports(src_path: PathLike, folder_name: str) -> PathLike:
    target_folder_path = find_folder_path(src_path, folder_name)
    if not target_folder_path in sys.path:
        sys.path.append(target_folder_path)
    return target_folder_path

def find_folder_path(src_path: PathLike, folder_name: str) -> PathLike:
    target_folder_path = Path(src_path, reset_instance=False).parent
    while target_folder_path.full_name != folder_name:
        target_folder_path = target_folder_path.parent
        if not target_folder_path.full_name:
            raise FileNotFoundError(f'Folder name: {folder_name} not found in src: {src_path.relative}')
    return target_folder_path

def get_own_functions(module_name: str) -> list[callable]:
    """
    Retrieves a list of functions defined in the specified module.

    Parameters:
    ----------
        module_name (str): The name of the module.

    Returns:
    -------
        list[callable]: A list of functions defined in the module.
    """
    module = sys.modules[module_name]
    return [obj for name, obj in inspect.getmembers(module) if isinstance(obj, FunctionType) and obj.__module__ == module.__name__]

def get_func_args(func: ty.Callable) -> list:
    """
    Retrieves a dictionary of default argument values for a specified function.

    Parameters:
    ----------
        func (callable): The function to inspect.

    Returns:
    -------
        dict: A dictionary where keys are argument names and values are default values.
    """
    signature = inspect.signature(func)
    
    args = [
        k for k, v in signature.parameters.items()
        if v.default is inspect.Parameter.empty
    ]
    
    return args

def get_func_kwargs(func: ty.Callable) -> dict:
    """
    Retrieves a dictionary of default argument values for a specified function.

    Parameters:
    ----------
        func (callable): The function to inspect.

    Returns:
    -------
        dict: A dictionary where keys are argument names and values are default values.
    """
    signature = inspect.signature(func)
    
    default_values = {
        k: v.default
        for k, v in signature.parameters.items()
        if v.default is not inspect.Parameter.empty
    }
    
    return default_values

def get_func_args_and_kwargs(func: ty.Callable) -> tuple[list, dict]:
    """
    Retrieves a dictionary of default argument values for a specified function.

    Parameters:
    ----------
        func (callable): The function to inspect.

    Returns:
    -------
        dict: A dictionary where keys are argument names and values are default values.
    """
    signature = inspect.signature(func)

    args = []
    kwargs = {}
    for k, v in signature.parameters.items():
        if v.default is inspect.Parameter.empty:
            args.append(k)
        else:
            kwargs[k] = v    
    return args, kwargs

def get_func_kwargs_an(func: ty.Callable) -> dict[str, dict]:
    """
    Returns a dictionary of all keyword parameters of the given function.
    Each key is the name of the parameter, and its value is a dictionary
    containing:
    - 'default': The default value of the parameter.
    - 'type': The type annotation of the parameter, or the type of the default
      value if no annotation is provided. For Union types, only the first type is used.

    :param func: A callable object to introspect.
    :return: A dictionary of keyword parameter information.
    """
    signature = inspect.signature(func)
    annotations = ty.get_type_hints(func)
    
    kwargs_info = {}
    for name, param in signature.parameters.items():
        if param.default is not inspect.Parameter.empty:
            default_value = param.default
            param_type = annotations.get(name, type(default_value))

            # Handle Union types by taking first type
            if 'UnionType' in str(type(param_type)) and hasattr(param_type, '__args__'):
                param_type = param_type.__args__[0]
            
            kwargs_info[name] = {
                "default": default_value,
                "type": param_type
            }
    
    return kwargs_info

def get_all_method_names(instance: object, first_name: str) -> list[str]:
    """
    Retrieves all method names of an instance that start with a specified prefix.

    Args:
    - `instance` (object): The instance whose method names are to be retrieved.
    - `first_name` (str): The prefix to filter method names.

    Returns:
    - list[str]: A list of method names that start with the specified prefix.
    """
    return [name for name in dir(instance) if callable(getattr(instance, name)) and not name.startswith("__") and name.startswith(first_name)]

def is_property(obj: object, attr_name: str) -> bool | None:
    cls = obj.__class__
    for cls in obj.__class__.__mro__:
        attr = cls.__dict__.get(attr_name)
        if isinstance(attr, property):
            return True
    if attr_name in obj.__dict__:
        return False
    return None

class classproperty(object):
    def __init__(self, f):
        self.f = f
    def __get__(self, obj, owner):
        return self.f(owner)
    

class GlobalPostLoad(type):

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # A custom dict that postpones actual instantiation
        class TrackingDict(dict):
            def __setitem__(self, key: str, value: ty.Any):
                if not key.startswith('__') and callable(value):
                    # Save the callable to be invoked lazily
                    cls.set(key, value)
                else:
                    super().__setitem__(key, value)
        return TrackingDict()

    @classmethod
    def set(cls, name: str, caller: ty.Callable[[], ty.Any]) -> None:
        assert callable(caller), f'Can not set: "{caller}" as a {cls.__class__.__name__} caller'

        caller_name = f'{name}__caller'

        if not hasattr(cls, name) and hasattr(cls, caller_name):
            raise ValueError(f'Can not set {cls.__class__.__name__} variable: "{caller_name}"')
        
        setattr(cls, caller_name, lambda cls: caller())
        setattr(cls, name, None)

    def __getattribute__(cls, name: str) -> ty.Any:
        # Standard attribute access
        value = super().__getattribute__(name)
        if value is None:
            # Look for a __caller if the value is None
            caller_name = f'{name}__caller'
            if hasattr(cls, caller_name):
                caller = super().__getattribute__(caller_name)
                new_value = caller()  # Instantiate the object
                setattr(cls, name, new_value)  # Cache the result
                return new_value
        return value


