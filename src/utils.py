import typing as ty
import re
import json
import base64
import urllib.parse

from sys import platform
from time import sleep
from datetime import datetime

from src.modules.paths import Path
from src.modules.internal_script import get_func_kwargs_an


T = ty.TypeVar('T')


### BASICS ######################################################################################

def list_get(_list: list[T], index: int, default: None = None) -> T | None:
    try:
        return _list[index]
    except IndexError:
        return default
    
def to_even(v: int | float, round_up: bool = False) -> int:
    v = int(v)
    return round(v if v % 2 == 0 else (v + 1 if round_up else v - 1))

ALPHABET = "abcdefghijklmnopqrstuvwxyz"

def is_duplicated(lst: ty.Iterable, e: ty.Any) -> bool:
    lst = list(lst)
    for _ in (0, 1):
        if e in lst:
            lst.remove(e)
        else:
            return False
    return True


### USER INTERACTION ######################################################################################

def ask_user(prompt: str = '', default_output: str = '', valid_outputs: list[T] | ty.Callable[[T], bool] | None = None, type: ty.Callable[[str], T] = str) -> T:
    out = input(prompt).strip() or default_output
    if type != str or valid_outputs:
        while True:
            try:
                if out != default_output:
                    out = type(out)
                if (not valid_outputs) or (valid_outputs(out) if callable(valid_outputs) else (out in valid_outputs)):
                    break
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(e, end=' | ')

            print('Invalid input.')
            out = input(prompt).strip()
    return out


### TEXT ######################################################################################

def reduce_text(text: str, max_len: int = 250, end: bool = True) -> str:
    if len(text) > max_len:
        if end:
            # Remove from end
            text = ' '.join(text[:max_len].split(' ')[:-1]) if ' ' in text else text[:max_len]
            return text + '...'
        else:
            # Remove from start 
            text = ' '.join(text[-max_len:].split(' ')[1:]) if ' ' in text else text[-max_len:]
            return '...' + text
    return text


### SQL ######################################################################################

def get_table_items_from_object(cls) -> dict[str, dict[str, type]]:
    allowed_types = (
        'str', 'list', 'set', 'tuple',
        'dict', 'int', 'float', 'bool'
    )

    sdata = cls._sdata if getattr(cls, '_sdata', None) else get_func_kwargs_an(cls.__init__)
    bad_cols = [col for col, col_info in sdata.items() if col_info['type'].__name__ not in allowed_types]
    for bad_col in bad_cols:
        sdata.pop(bad_col)
    return sdata

def build_sql_items(obj) -> dict[str, str]:
    conv_type = {
        'str': 'TEXT',
        'list': 'JSONB',
        'set': 'JSONB',
        'tuple': 'JSONB',
        'dict': 'JSONB',
        'int': 'INTEGER',
        'float': 'DOUBLE PRECISION',
        'bool': 'BOOLEAN'
    }
    sdata = obj._sdata if getattr(obj, '_sdata', None) else get_func_kwargs_an(obj.__init__)
    return {'id': 'TEXT PRIMARY KEY', **{k: f"{conv_type[v['type'].__name__]}" for k, v in sdata.items()}}

def build_sql_table_command(obj) -> str:
    return (f'CREATE TABLE IF NOT EXISTS "{obj._TABLE_NAME}" (' + "\n    "
        + ",\n    ".join(f"{k} {v}" for k, v in build_sql_items(obj).items())
        + "\n);")

def parse_sql_args(obj, items: dict) -> dict:
    sdata = obj._sdata if getattr(obj, '_sdata', None) else get_func_kwargs_an(obj.__init__)
    _items = {k: None if items[k] is None else v['type'](items[k])
              for k, v in sdata.items() if k in items}
    _items['id'] = items['id']
    return _items

def build_sql_args(obj) -> tuple:
    sdata = obj._sdata if getattr(obj, '_sdata', None) else get_func_kwargs_an(obj.__init__)
    conv_type = {'list': lambda x: None if x is None else json.dumps(x, separators=(',', ':')),
                 'set': lambda x: None if x is None else json.dumps(list(x), separators=(',', ':')),
                 'tuple': lambda x: None if x is None else json.dumps(list(x), separators=(',', ':')),
                 'dict': lambda x: None if x is None else json.dumps(x, separators=(',', ':')),
                 'Enum': lambda x: x.value}
    return tuple((obj.id, *(conv_type.get(v['type'].__name__, lambda x: x)(getattr(obj, k))
                            for k, v in sdata.items())))

def build_sql_save_command(cls) -> str:
    sdata = cls._sdata if getattr(cls, '_sdata', None) else get_func_kwargs_an(cls.__init__)
    keys = list(sdata.keys())
    return (f'INSERT INTO "{cls._TABLE_NAME}" (id, ' + ", ".join(keys) + ")\nVALUES ($1, "
            + ", ".join(f"${i+2}" for i in range(len(keys)))
            + ")\nON CONFLICT(id) DO UPDATE SET\n    "
            + ",\n    ".join(f"{item_name} = excluded.{item_name}" for item_name in keys))


def build_sql_keys(cls) -> str:
    sdata = cls._sdata if getattr(cls, '_sdata', None) else get_func_kwargs_an(cls.__init__)
    return (f"id, {', '.join(name for name in sdata.keys())}")


### URLS / FILENAMES ######################################################################################


def encode_urlsafe(s):
    return base64.urlsafe_b64encode(s.encode()).decode().rstrip('=')

def decode_urlsafe(s):
    padding = '=' * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + padding).decode()

def json_to_filename(data: 'JSONType') -> str:
    str_data = json.dumps(data)
    if len(str_data) > 200:
        raise ValueError(f'Filename too long: {str_data}')
    return urllib.parse.quote(str_data, safe='')

def filename_to_json(filename: str) -> 'JSONType':
    return json.loads(urllib.parse.unquote(filename))

def sanitize_url(url: str) -> str:
    return url.split('?is_from_webapp', 1)[0].split('?t=')[0].removesuffix('/').replace('\n', '').replace('\r', '')

def get_source_from_url(url: str) -> str:
    """
    Identifies the source platform from a given URL.

    Parameters:
    ----------
        url (str): The URL to be checked.

    Returns:
    -------
        str: The name of the source platform if found, else None.
    """
    url = sanitize_url(url)
    for source in ['tiktok', 'youtube', 'x', 'instagram']:
        if source in url.lower():
            return source
    
def build_video_url(source: str = '', author = '', wid: str = '') -> str:
    if source.lower() == 'tiktok': 
        return f'https://www.tiktok.com/@{author}/video/{wid}'
    elif source.lower() == 'youtube':
        return f'https://www.youtube.com/watch?v={wid}'
    elif source.lower() == 'x':
        return f'https://x.com/{author}/status/{wid}'
    elif source.lower() == 'instagram':
        return f'https://www.instagram.com/{author}/reel/{wid}'
    return ''

def extract_video_info(url: str) -> tuple[str, str, str]:
    """source, author, id"""
    url = sanitize_url(url)
    if "tiktok" in url:
        match = re.search(r"@([^/]+)/video/(\d+)", url)
        if match:
            return ("tiktok", *match.groups())
    elif "youtube" in url:
        comps = url.split('v=', 1)
        if len(comps) == 2:
            return ("youtube", "", comps[-1])
    elif "x" in url or "twitter.com" in url:
        match = re.search(r"/status/(\d+)", url)
        if match:
            return ("x", url.split('/status', 1)[0].split('/')[-1], match.group(1))
    elif "instagram" in url:
        match = re.search(r"instagram\.com/([^/]+)/reel/([^/]+)", url)
        if match:
            return ("instagram", match.group(1), match.group(2))
    return ("", "", "")

def build_audio_url(source: str = '', wid: str = '') -> str:
    if source.lower() == 'tiktok': 
        return f'https://www.tiktok.com/music/original-sound-{wid}'
    elif source.lower() == 'youtube':
        return f'https://music.youtube.com/watch?v={wid}'
    elif source.lower() == 'instagram':
        return f'https://www.instagram.com/reels/audio/{wid}'
    return ''

def extract_audio_info(url: str) -> tuple[str, str]:
    """source, id"""
    url = sanitize_url(url)
    if "tiktok" in url:
        if 'music' in url:
            return ("tiktok", url.split('-')[-1])
    elif "youtube" in url:
        comps = url.split('v=', 1)
        if len(comps) == 2:
            return ("youtube", comps[-1])
    elif "instagram" in url:
        comps = url.split('/audio/', 1)
        if len(comps) == 2:
            return ("instagram", comps[-1])
    return ("", "")

def is_valid_filename(filename: str) -> bool:
    r"""
    Check if a string is a valid filename (cross-platform safe).

    Forbidden characters: / \ : * ? " < > | 
    Also checks for empty/whitespace-only strings.

    Returns True if valid, False otherwise.
    """
    if not filename or filename.strip() == "":
        return False
    
    invalid_chars = r'[\/:*?"<>|]'
    if re.search(invalid_chars, filename):
        return False
    
    reserved_names = {
        "CON", "PRN", "AUX", "NUL",
        *(f"COM{i}" for i in range(1, 10)),
        *(f"LPT{i}" for i in range(1, 10))
    }
    if filename.upper().split('.')[0] in reserved_names:
        return False
    
    if len(filename) > 255:
        return False
    return True


### DATE ######################################################################################

DATE_FORMAT = "%d-%m-%Y_%H-%M-%S-%f"

def create_unique_date() -> str:
    unique_date = date_to_str()
    if hasattr(create_unique_date, 'prev_date'):
        while unique_date == create_unique_date.prev_date:
            sleep(0.01)
            unique_date = date_to_str()
    create_unique_date.prev_date = unique_date
    return unique_date

def date_to_str(date: datetime | None = None) -> str:
    if date is None:
        date = datetime.now()
    return date.strftime(DATE_FORMAT)[:-4]

def str_to_date(date_str: str | None = None) -> datetime:
    if date_str is None:
        return datetime.now()
    return datetime.strptime(date_str, DATE_FORMAT)


### JSON ######################################################################################

JSONType = str | int | float | bool | dict | list

def assert_is_json_serializable(data: JSONType) -> None:
    try:
        json.dumps(data)
    except (TypeError, ValueError) as e:
        raise ValueError('Invalid json data') from e

def is_json_serializable(data: JSONType) -> bool:
    try:
        json.dumps(data)
        return True
    except (TypeError, ValueError) as e:
        return False

def pretty_json(data: JSONType) -> JSONType:
    return json.dumps(data, indent=4)

def parse_corrupted_json(text: str) -> JSONType:
    """
    Safely extract and parse the first valid JSON object or array from a string.
    Removes any leading/trailing non-JSON content by locating the first balanced JSON structure.
    """
    # Find first { or [
    start = min(
        (text.find('{') if '{' in text else float('inf')),
        (text.find('[') if '[' in text else float('inf'))
    )
    if start == float('inf'):
        raise ValueError("No JSON object or array found in the text.")

    # Pick opening and matching closing character
    open_char = text[start]
    close_char = '}' if open_char == '{' else ']'

    # Now, iterate to find matching closing bracket
    depth = 0
    for i in range(start, len(text)):
        c = text[i]
        if c == open_char:
            depth += 1
        elif c == close_char:
            depth -= 1
            if depth == 0:
                json_str = text[start:i+1]
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Found JSON-like string but failed to parse: {e}")

    raise ValueError("No balanced JSON object found in the text.")

def apply_schema(json_data: dict, json_schema: dict):
    """
    Reduces a JSON structure based on a given JSON schema.
    
    :param json_data: The input JSON data to be reduced.
    :param json_schema: The JSON schema dict to enforce.
    :return: A reduced JSON structure.
    """
    def reduce_object(data: dict, schema: dict):
        if not isinstance(data, dict) or not isinstance(schema, dict):
            return None

        result = {}
        required_keys = schema.get("required", [])
        properties = schema.get("properties", {})
        
        for key, subschema in properties.items():
            if key in data:
                reduced_value = reduce_value(data[key], subschema)
                if reduced_value is not None:
                    result[key] = reduced_value

        if all(key in result for key in required_keys):
            return result
        else:
            return None

    def reduce_array(data: dict, schema: dict):
        if not isinstance(data, list) or not isinstance(schema, dict):
            return None

        item_schema = schema.get("items", {})
        reduced_array = [
            reduce_value(item, item_schema)
            for item in data
        ]
        return None if None in reduced_array else reduced_array

    def reduce_value(data: dict, schema: dict):
        data_type = schema.get("type")
        enum_values = schema.get("enum")
        
        # Check enum values
        if enum_values is not None:
            if data in enum_values:
                return data
            else:
                return None  # Value not in enum
        
        if data_type == object:
            return reduce_object(data, schema)
        elif data_type == "array":
            return reduce_array(data, schema)
        elif data_type == "string" and isinstance(data, str):
            return data
        elif data_type == "integer" and isinstance(data, int):
            return data
        elif data_type == "number" and isinstance(data, (int, float)):
            return data
        elif data_type == "boolean" and isinstance(data, bool):
            return data
        else:
            return None  # Type mismatch or unsupported type

    return reduce_object(json_data, json_schema)


### Copy/Paste ###############################################################################################

if platform == 'win32':
    import pyperclip
    def copy_to_clipboard(text: str) -> None:
        pyperclip.copy(text)
elif platform == 'darwin':
    import subprocess
    def copy_to_clipboard(text: str) -> None:
        subprocess.run("pbcopy", text=True, input=text, check=True)
elif platform == 'linux':
    import subprocess
    def copy_to_clipboard(text: str) -> None:
        with subprocess.Popen(['xclip','-selection', 'clipboard'], stdin=subprocess.PIPE) as pipe:
            pipe.communicate(input=text.encode('utf-8'))
else:
    def copy_to_clipboard(text: str) -> None:
        raise NotImplementedError(f'Unknwon platform: {platform}')