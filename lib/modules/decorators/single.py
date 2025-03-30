from typing import Self


def single(cls: Self) -> Self:
    instances = {}
    def get_instance(*args, **kwargs) -> Self:
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    get_instance.__dict__.update(cls.__dict__)
    return get_instance