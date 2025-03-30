import sys
import os


p = os.path.join(os.path.dirname(__file__), os.path.basename(__file__).removeprefix('_'))
root_name = os.path.splitext(os.path.basename(p))[0]
p = os.path.dirname(p)

while os.path.basename(p) != root_name:
    p = os.path.dirname(p)
    if p.endswith(':/'):
        raise FileNotFoundError(f'Root: {root_name} not found.')

sys.path.insert(0, os.path.abspath(p))


del root_name, p
__all__ = []