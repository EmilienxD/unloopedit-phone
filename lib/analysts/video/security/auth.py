from datetime import datetime
from random import shuffle
from lib.config import Paths
from lib.helpers import JSONSaver
from lib.exceptions import NoMoreValidAccountError


RPD_QUOTA = 50
RPM_QUOTA = 1


json_saver = JSONSaver(json_path=Paths('lib/analysts/video/config.json'), auto_save=True)

# Initial shuffle for homogeneous use of API keys
keys = list(json_saver.keys())
shuffle(keys)
for key in keys:
    json_saver[key] = json_saver.pop(key)

# JSON structure:
# {
#    "MyApiKeyHere": {      
#        "invalid_until": null,
#        "requests_today": 0,
#        "last_reset": "2024-02-01T00:00:00",
#        "email": "MyEmailHere"
# },
# ...

def set_auto_save() -> None:
    json_saver._auto_save = True

def set_no_auto_save() -> None:
    json_saver._auto_save = False

def add_key(key: str, email: str = '') -> None:
    if key not in json_saver:
        json_saver[key] = {
            "invalid_until": None,
            "requests_today": 0,
            "last_reset": datetime.now().isoformat(),
            "email": email
        }

def remove_key(key: str) -> None:
    if key not in json_saver:
        raise KeyError(f"Key '{key}' does not exist.")
    del json_saver[key]

def is_valid_key(key: str, raise_error: bool = False) -> bool:
    """Check if an API key is valid for use."""
    if key not in json_saver:
        if raise_error:
            raise ValueError(f'Key: {key} not found.')
        return False

    key_data = json_saver[key]
    now = datetime.now()

    if key_data.get("requests_today", 0) >= RPD_QUOTA:
        if raise_error:
            raise ValueError(f'Key: {key} exceeded RPD quota.')
        return False
    if key_data.get("invalid_until") and datetime.fromisoformat(key_data["invalid_until"]) > now:
        if raise_error:
            raise ValueError(f'Key: {key} currently unavalable.')
        return False
    return True

def clear_keys() -> None:
    json_saver.clear()

def reset_daily_quotas() -> None:
    """Reset request counters if a new day has started."""
    now = datetime.now()
    for key, value in json_saver.items():
        last_reset = datetime.fromisoformat(value.get("last_reset", "1970-01-01T00:00:00"))
        if last_reset.date() < now.date():
            json_saver[key]["requests_today"] = 0
            json_saver[key]["last_reset"] = now.isoformat()

def get_valid_key(key: str | None = None, raise_error: bool = False) -> str | None:
    """Retrieve a key that has not exceeded RPD."""
    reset_daily_quotas()
    
    now = datetime.now()
    for _key, value in json_saver.items():
        if (value["requests_today"] < RPD_QUOTA and
            value["invalid_until"] is None or datetime.fromisoformat(value["invalid_until"]) <= now and
            ((not key) or (key == _key))):
            json_saver[_key]["invalid_until"] = None
            rotate_key(_key)
            return _key
    if raise_error:
        raise NoMoreValidAccountError('No more valid api keys.')
    return None  # No available keys

def get_valid_keys(count: int | None = None, raise_error: bool = False) -> list[str]:
    """Retrieve multiple keys that have not exceeded RPD."""
    reset_daily_quotas()
    
    valid_keys = []
    now = datetime.now()
    for key, value in json_saver.items():
        if value["requests_today"] < RPD_QUOTA and (
            value["invalid_until"] is None or datetime.fromisoformat(value["invalid_until"]) <= now
        ):
            json_saver[key]["invalid_until"] = None
            valid_keys.append(key)
    
    valid_keys = valid_keys if count is None else valid_keys[:count]

    if (not valid_keys) and raise_error:
        raise NoMoreValidAccountError('No more valid api keys.')
    
    [rotate_key(key) for key in valid_keys]
    return valid_keys

def rotate_key(key: str) -> None:
    """Rotate key for fair distribution."""
    json_saver[key] = json_saver.pop(key)

def increment_key_usage(key: str, n: int = 1) -> None:
    """Increase request count for a key (to be called inside video analyst)."""
    if key in json_saver:
        json_saver[key]["requests_today"] += n
