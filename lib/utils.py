from __future__ import annotations
import typing as ty
import re
import json

from time import sleep
from datetime import datetime
from lib.modules.paths import Path

if ty.TYPE_CHECKING:
    from lib.dataproc.videodata import VideoData
    from lib.dataproc.scenepack import ScenePack
    from lib.dataproc.myvideo import MyVideo


### BASICS ######################################################################################

T = ty.TypeVar('T')

def list_get(_list: list[T], index: int, default: None = None) -> T | None:
    try:
        return _list[index]
    except IndexError:
        return default
    
def to_even(v: int | float, round_up: bool = False) -> int:
    v = int(v)
    return round(v if v % 2 == 0 else (v + 1 if round_up else v - 1))


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

def build_sql_items(obj: VideoData | ScenePack | MyVideo) -> dict[str, str]:
    conv_type = {
        'str': 'TEXT',
        'list': 'JSONB',
        'dict': 'JSONB',
        'int': 'INTEGER',
        'float': 'REAL',
        'bool': 'BOOLEAN'
    }
    return {'id': 'TEXT PRIMARY KEY', **{k: f"{conv_type[v['type'].__name__]}" for k, v in obj._sdata.items()}}

def build_sql_table_command(obj: VideoData | ScenePack | MyVideo) -> str:
    return (f'CREATE TABLE IF NOT EXISTS "{obj.__name__}" (' + "\n    "
        + ",\n    ".join(f"{k} {v}" for k, v in build_sql_items(obj).items())
        + "\n);")

def parse_sql_args(obj: VideoData | ScenePack | MyVideo, items: dict) -> dict:
    _items = {k: None if items[k] is None else v['type'](items[k])
              for k, v in obj._sdata.items() if k in items}
    _items['id'] = items['id']
    return _items

def build_sql_args(obj: VideoData | ScenePack | MyVideo) -> tuple:
    conv_type = {'list': lambda x: None if x is None else json.dumps(x, separators=(',', ':')),
                 'dict': lambda x: None if x is None else json.dumps(x, separators=(',', ':'))}
    x=  tuple((obj.id, *(conv_type.get(v['type'].__name__, lambda x: x)(attr if (attr := getattr(obj, k)) else v['default'])
                            for k, v in obj._sdata.items())))
    return x

def build_sql_save_command(cls: VideoData | ScenePack | MyVideo) -> str:
    keys = list(cls._sdata.keys())
    return (f'INSERT INTO "{cls.__name__}" (id, ' + ", ".join(keys) + ")\nVALUES ($1, "
            + ", ".join(f"${i+2}" for i in range(len(keys)))
            + ")\nON CONFLICT(id) DO UPDATE SET\n    "
            + ",\n    ".join(f"{item_name} = excluded.{item_name}" for item_name in keys))


def build_sql_keys(cls: VideoData | ScenePack | MyVideo) -> str:
    return (f"id, {', '.join(name for name in cls._sdata.keys())}")


### URLS ######################################################################################

URL_PATH_SEPARATOR = '{{{'
PLATEFORMS = ['tiktok', 'youtube', 'x', 'instagram']

def build_url(source: str = '', author = '', wid: str = '') -> str:
    if source.lower() == 'tiktok': 
        return f'https://www.tiktok.com/@{author}/video/{wid}'
    elif source.lower() == 'youtube':
        return f'https://www.youtube.com/watch?v={wid}'
    elif source.lower() == 'x':
        return f'https://x.com/{author}/status/{wid}'
    elif source.lower() == 'instagram':
        return f'https://www.instagram.com/{author}/reel/{wid}'
    return ''

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
    for source in PLATEFORMS:
        if source in url.lower():
            return source

def filename_to_url(filename: str) -> str:
    p = Path(filename)
    return build_url(*(p.name.split(URL_PATH_SEPARATOR)[:3]))

def sanitize_url(url: str) -> str:
    return url.split('?is_from_webapp', 1)[0].split('?t=')[0]

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

def url_to_filename(url: str, extension: str = '.mp4') -> str:
    return URL_PATH_SEPARATOR.join(extract_video_info(url)) + extension


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

def str_to_date(date_str: str) -> datetime:
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
