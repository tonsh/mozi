import base64
from datetime import datetime
import hashlib
import hmac
import os
import time
from typing import Iterator, List, Optional
import pytz
import yaml

APP_ENV = os.environ.get("APP_ENV", "dev")

# custom typings
Path = str
FilePath = str


def is_prod() -> bool:
    return APP_ENV == "prod"


def is_dev() -> bool:
    return APP_ENV == "dev"


def is_test() -> bool:
    return APP_ENV == "test"


def ensure_dir(directory: Path) -> Path:
    """ Create directory if it doesn't exist. """
    directory = directory.strip()
    if not directory:
        raise ValueError("Param directory is empty.")

    directory = os.path.normpath(directory)
    if os.path.exists(directory):
        if not os.path.isdir(directory):
            raise ValueError(f"Not a directory: {directory}")
    else:
        head, tail = os.path.split(directory)
        if not tail and head == "/":
            raise OSError(f"Root directory missing? {directory}")
        if head:
            ensure_dir(head)

        os.mkdir(directory)
    return directory


def get_timestamp():
    return int(time.time() * 1000)


def timestamp_to_datetime(timestamp: int, timezone: str = "Asia/Shanghai") -> datetime:
    """ Convert timestamp(ms) to datetime. """
    next_time = int(timestamp) / 1000.0
    return datetime.fromtimestamp(next_time, tz=pytz.timezone(timezone))


def hmac_sha256(api_secret: str, message: str) -> str:
    m = hmac.new(api_secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256)
    return m.hexdigest()


def uuid(message: str, length: int = 8) -> str:
    hash_bytes = hashlib.sha256(message.encode("utf-8")).digest()
    result = base64.urlsafe_b64encode(hash_bytes).decode("utf-8")
    return result[:length]


def deep_update(dict1: dict, dict2: dict) -> dict:
    """
    Recursively updates dict1 with values from dict2.
    """
    for key, value in dict2.items():
        if isinstance(value, dict) and key in dict1 and isinstance(dict1[key], dict):
            deep_update(dict1[key], value)
        else:
            dict1[key] = value
    return dict1


def get_config(yml_files: List[FilePath], key: Optional[str] = None) -> dict:
    config_data = {}
    for path in yml_files:
        with open(path, 'r', encoding='utf-8') as config_file:
            config_data = deep_update(config_data, yaml.safe_load(config_file) or {})
    if key:
        return config_data.get(key) or {}
    return config_data


def sort_list(data: dict) -> dict:
    """ Sort list in dict. """
    for _, val in data.items():
        if isinstance(val, list):
            val.sort()
        elif isinstance(val, dict):
            sort_list(val)  # Recursively handle nested dicts
    return data
