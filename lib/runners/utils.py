import typing as ty
from functools import wraps

from lib.exceptions import TaskDisabledError, ConfigError


P = ty.ParamSpec('P')
T = ty.TypeVar('T')


def obligatory_task(var: bool) -> ty.Callable[P, T]:
    def decorator(func: ty.Callable[P, T]) -> ty.Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            if var:
                return func(*args, **kwargs)
            else:
                raise TaskDisabledError(func.__name__, 'Blocking config')
        return wrapper
    return decorator

def optional_task(var: bool, on_miss: ty.Callable | ty.Any = None) -> ty.Callable[P, T]:
    def decorator(func: ty.Callable[P, T]) -> ty.Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            return func(*args, **kwargs) if var else (on_miss(*args, **kwargs) if callable(on_miss) else on_miss)
        return wrapper
    return decorator

def check_config_compatibility(config: dict, config_schema: dict) -> None:
    """
    Checks if the given config dictionary is compatible with the schema dictionary.
    Raises a ValueError if the config does not fit the schema.

    Parameters:
    - config (dict): The configuration dictionary to validate.
    - config_schema (dict): The schema dictionary with expected types as values.

    Raises:
    - ValueError: If the config does not match the schema in keys or types.
    """
    def validate(config, schema, path=""):
        if not isinstance(config, dict):
            raise ConfigError(f"Expected a dictionary at '{path}', but got {type(config).__name__}.")
        
        for key, expected_type in schema.items():
            full_path = f"{path}.{key}" if path else key

            if key not in config:
                raise ConfigError(f"Missing key '{full_path}' in the config.")
            
            value = config[key]
            
            # If expected type is a dict, recurse
            if isinstance(expected_type, dict):
                if not isinstance(value, dict):
                    raise ConfigError(f"Expected a dictionary at '{full_path}', but got {type(value).__name__}.")
                validate(value, expected_type, path=full_path)
            elif not (isinstance(value, int) and expected_type == float):   # Exception for int on float expectation (e.g. 1 -> 1.0)
                # Check type compatibility
                if not isinstance(value, expected_type):
                    raise ConfigError(
                        f"Type mismatch at '{full_path}': Expected {expected_type.__name__}, got {type(value).__name__}."
                    )

    validate(config, config_schema)