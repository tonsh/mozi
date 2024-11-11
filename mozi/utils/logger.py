import copy
from dataclasses import dataclass, field
from enum import Enum
import logging
import logging.config
import os
from typing import List, Optional, Union

from . import FilePath, Path, ensure_dir, get_config, uuid

# custom logging level type
Level = int
LevelName = str

DEFAULT_LOG_DIR = '/tmp/logs'
MAX_FILE_SIZE = 104857600  # 100MB
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


class HandlerEnum(Enum):
    CONSOLE = 'console'
    ROTATE = 'rotate'
    FILE = 'file'
    ERROR = 'error'

    @classmethod
    def contains(cls, value: Union[str, 'HandlerEnum']) -> bool:
        return HandlerEnum.__contains__(value)


@dataclass
class Formatter:
    name: str = field(default='default')
    format: str = field(default=DEFAULT_FORMAT)

    def to_dict(self) -> dict:
        return {self.name: {'format': self.format}}


@dataclass
class RotateConfig:
    max_bytes: int = field(default=MAX_FILE_SIZE)
    backup_count: int = field(default=5)


@dataclass
class LoggerItem:
    name: str
    level: LevelName = field(default='INFO')
    handlers: List[HandlerEnum] = field(default_factory=list)
    propagate: bool = field(default=False)   # Default do not propagate to root logger
    formatter: str = field(default='default')
    log_path: Path = field(default=DEFAULT_LOG_DIR)
    rotate_cnf: RotateConfig = field(default_factory=RotateConfig)

    def __post_init__(self):
        if not self.handlers:
            self.handlers = [HandlerEnum.CONSOLE]

        # uniq handlers
        handlers = [HandlerEnum(h) for h in self.handlers]
        self.handlers = list(set(handlers))

        self.uuid: str = uuid(self.name, length=10)
        self._log_file: Optional[FilePath] = None
        self._error_file: Optional[FilePath] = None

    @classmethod
    def load(cls, name: str, config: Optional[dict] = None, log_path: Optional[Path] = None) -> 'LoggerItem':  # pylint: disable=line-too-long
        config = copy.deepcopy(config) or {}

        handlers = config.get('handlers') or ['console']
        if handlers:
            config['handlers'] = [HandlerEnum(h) for h in handlers]

        log_path = config.get('log_path') or log_path
        if log_path:
            config['log_path'] = log_path

        return cls(name=name, **config)

    @property
    def log_file(self) -> FilePath:
        """ Normalize the log file path and directory. """
        if not self._log_file:
            file_name = self.name.replace('.', '/')
            log_file = f"{self.log_path}/{file_name}.log"

            if not os.path.isabs(log_file):
                # 相对路径转换为绝对路径
                log_file = os.path.abspath(log_file)

            # 创建日志目录
            ensure_dir(os.path.dirname(log_file))

            self._log_file = log_file
        return self._log_file

    @property
    def error_file(self) -> FilePath:
        fname = os.path.basename(self.log_file)
        fpath = os.path.dirname(self.log_file)
        fname = fname.replace('.log', '_error.log')

        if fpath:
            fpath = f"{fpath}/"
        return f"{fpath}{fname}"

    def console(self) -> dict:
        return {
            f'console-{self.uuid}': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': self.formatter,
                'stream': 'ext://sys.stdout'
            }
        }

    def file(self) -> dict:
        return {
            f'file-{self.uuid}': {
                'class': 'logging.FileHandler',
                'level': self.level,
                'formatter': self.formatter,
                'filename': self.log_file,
            }
        }

    def rotate(self) -> dict:
        return {
            f'rotate-{self.uuid}': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': self.level,
                'formatter': self.formatter,
                'filename': self.log_file,
                'maxBytes': self.rotate_cnf.max_bytes,
                'backupCount': self.rotate_cnf.backup_count,
            }
        }

    def error(self) -> dict:
        return {
            f'error-{self.uuid}': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'ERROR',
                'formatter': self.formatter,
                'filename': self.error_file,
                'maxBytes': self.rotate_cnf.max_bytes,
                'backupCount': self.rotate_cnf.backup_count,
            }
        }

    def get_handlers_dict(self) -> dict:
        handlers = {}
        for handler in HandlerEnum:
            if handler in self.handlers:
                handlers.update(getattr(self, handler.value)())
        return handlers

    def to_dict(self) -> dict:
        return {
            self.name: {
                'level': self.level,
                'handlers': [f"{h.value}-{self.uuid}" for h in self.handlers],
                'propagate': self.propagate,
            }
        }


@dataclass
class LoggerConfig:
    formatters: List[Formatter] = field(default_factory=list)
    loggers: List[LoggerItem] = field(default_factory=list)

    def __post_init__(self):
        if not self.formatters:
            self.formatters = [Formatter()]

        if not self.loggers:
            raise ValueError("No logger configuration found")

    def to_dict(self) -> dict:
        handlers, loggers = {}, {}
        for logger in self.loggers:
            handlers.update(logger.get_handlers_dict())
            loggers.update(logger.to_dict())

        fmts = {}
        for formatter in self.formatters:
            fmts.update(formatter.to_dict())

        config = {
            'version': 1,
            'formatters': fmts,
            'handlers': handlers,
            'loggers': loggers,
        }
        return config


class LoggerLoader:

    def __init__(self, yml_files: List[FilePath], log_path: Optional[Path] = None):
        self.yml_files = yml_files
        self.config: dict = get_config(self.yml_files, 'logging')
        self.log_path = log_path

    def load(self) -> LoggerConfig:
        config = copy.deepcopy(self.config)

        if not config or not config.get('loggers'):
            raise ValueError("No logging configuration found")

        loggers = []
        log_path = config.get('log_path') or self.log_path
        for name, cnf in config['loggers'].items():
            loggers.append(LoggerItem.load(name, cnf, log_path))

        fmts = [
            Formatter(name=k, format=v['format']) for k, v in config.get('formatters', {}).items()
        ]
        log_config = LoggerConfig(
            formatters=fmts,
            loggers=loggers
        )

        logging.config.dictConfig(log_config.to_dict())
        return log_config


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
