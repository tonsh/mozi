from datetime import datetime
import hashlib
import hmac
import os
import time
from typing import Iterator
import pytz

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
