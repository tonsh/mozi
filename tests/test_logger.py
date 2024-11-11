import os
from unittest import TestCase
import pytest
from mozi.utils import sort_list
from mozi.utils.logger import (
    DEFAULT_FORMAT, DEFAULT_LOG_DIR, MAX_FILE_SIZE, Formatter, HandlerEnum, LoggerConfig,
    LoggerItem, LoggerLoader, RotateConfig, get_logger,
)


class TestHandlerEnum(TestCase):

    def test_enum_values(self):
        assert HandlerEnum.contains('console') is True
        assert HandlerEnum.contains(HandlerEnum.CONSOLE) is True

        # not exist
        assert HandlerEnum.contains('unkown') is False


class TestFormatter(TestCase):

    def test_default_values(self):
        formatter = Formatter()
        assert formatter.name == 'default'
        assert formatter.format == DEFAULT_FORMAT
        assert formatter.to_dict() == {'default': {'format': DEFAULT_FORMAT}}

        formatter = Formatter(name='custom', format='%(message)s')
        assert formatter.name == 'custom'
        assert formatter.format == '%(message)s'
        assert formatter.to_dict() == {'custom': {'format': '%(message)s'}}


class TestRotateConfig(TestCase):
    def test_default_values(self):
        rotate_config = RotateConfig()
        assert rotate_config.max_bytes == MAX_FILE_SIZE
        assert rotate_config.backup_count == 5

        rotate_config = RotateConfig(max_bytes=204800, backup_count=10)
        assert rotate_config.max_bytes == 204800
        assert rotate_config.backup_count == 10


class TestLoggerItemInitialize(TestCase):
    def test_default_values(self):
        logger = LoggerItem(name='test')
        assert logger.name == 'test'
        assert logger.level == 'INFO'
        assert logger.formatter == "default"
        assert logger.log_path == DEFAULT_LOG_DIR
        assert logger.propagate is False
        assert logger.handlers == [HandlerEnum.CONSOLE]
        assert logger.rotate_cnf.max_bytes == MAX_FILE_SIZE
        assert logger.rotate_cnf.backup_count == 5

    def test_custom_values(self):
        logger = LoggerItem(
            name='test',
            level='DEBUG',
            formatter='simple',
            log_path='/tmp/logs/custom',
            propagate=True,
            handlers=[HandlerEnum.FILE, HandlerEnum.ERROR, HandlerEnum.FILE],
            rotate_cnf=RotateConfig(max_bytes=204800, backup_count=10)
        )
        assert logger.name == 'test'
        assert logger.level == 'DEBUG'
        assert logger.formatter == 'simple'
        assert logger.log_path == '/tmp/logs/custom'
        assert logger.propagate is True
        assert logger.rotate_cnf.max_bytes == 204800
        assert logger.rotate_cnf.backup_count == 10
        assert len(logger.handlers) == 2
        self.assertSetEqual(set(logger.handlers), set([HandlerEnum.FILE, HandlerEnum.ERROR]))

    def test_init(self):
        logger = LoggerItem(name='test')
        assert logger.uuid == 'n4bQgYhMfW'

        # default console handler
        assert logger.handlers == [HandlerEnum.CONSOLE]

        # reset handlers to HandlerEnum type
        logger = LoggerItem(name='test', handlers=['console', 'error'])  # type: ignore
        assert len(logger.handlers) == 2
        self.assertSetEqual(set(logger.handlers), set([HandlerEnum.ERROR, HandlerEnum.CONSOLE]))

        # uniq custom handlers
        logger = LoggerItem(
            name='test',
            handlers=[HandlerEnum.FILE, HandlerEnum.ERROR, HandlerEnum.FILE],
        )
        assert len(logger.handlers) == 2
        self.assertSetEqual(set(logger.handlers), set([HandlerEnum.ERROR, HandlerEnum.FILE]))


class TestLoggerItemLoader(TestCase):

    def test_load_empty_config(self):
        # empty config return default values
        logger = LoggerItem.load('test', config=None)
        assert logger == LoggerItem(name='test')

        logger = LoggerItem.load('test', config={})
        assert logger == LoggerItem(name='test')

    def test_load(self):
        config = {
            'level': 'DEBUG',
            'formatter': 'simple',
            'propagate': True,
            'handlers': ['file', 'error', 'file'],
            'rotate_cnf': {'max_bytes': 204800, 'backup_count': 10}
        }
        logger = LoggerItem.load('test', config=config)
        self.assertEqual(logger, LoggerItem(name='test', **config))

        # using global log_path
        logger = LoggerItem.load('test', config=config, log_path='/tmp/logs')
        self.assertEqual(logger, LoggerItem(name='test', log_path='/tmp/logs', **config))

        # using custom log_path only for current logger
        config['log_path'] = '/tmp/logs/custom'
        logger = LoggerItem.load('app', config=config, log_path='/tmp/logs')
        self.assertEqual(logger, LoggerItem(name='app', **config))
        assert logger.log_path == '/tmp/logs/custom'


class TestLoggerItem(TestCase):

    def test_log_file(self):
        # using default log path
        logger = LoggerItem('app')
        assert logger.log_file == f'{DEFAULT_LOG_DIR}/app.log'
        assert logger.error_file == f'{DEFAULT_LOG_DIR}/app_error.log'

        # make sub directory
        logger = LoggerItem('app.log')
        assert logger.log_file == f'{DEFAULT_LOG_DIR}/app/log.log'
        assert logger.error_file == f'{DEFAULT_LOG_DIR}/app/log_error.log'

        # custom log base dir
        logger = LoggerItem('app.log', log_path='/tmp/logs/custom')
        assert logger.log_file == '/tmp/logs/custom/app/log.log'
        assert logger.error_file == '/tmp/logs/custom/app/log_error.log'

        # relative path
        logger = LoggerItem('app.log', log_path='data/tests/tmp/logs/../')
        assert logger.log_file == f'{os.getcwd()}/data/tests/tmp/app/log.log'
        assert logger.error_file == f'{os.getcwd()}/data/tests/tmp/app/log_error.log'

        # absolute path
        logger = LoggerItem('app.log', log_path='/tmp/logs/app.log')
        assert logger.log_file == '/tmp/logs/app.log/app/log.log'
        assert logger.error_file == '/tmp/logs/app.log/app/log_error.log'

    def test_to_dict(self):
        logger = LoggerItem('app')
        assert logger.to_dict() == {
            'app': {
                'level': 'INFO',
                'propagate': False,
                'handlers': ['console-oXLO3K5HR0'],
            }
        }

        logger = LoggerItem(
            'app',
            level='DEBUG',
            propagate=True,
            handlers=[HandlerEnum.ROTATE, HandlerEnum.ERROR]
        )
        self.assertEqual(sort_list(logger.to_dict()), sort_list({
            'app': {
                'level': 'DEBUG',
                'propagate': True,
                'handlers': ['rotate-oXLO3K5HR0', 'error-oXLO3K5HR0'],
            }
        }))


class TestLoggerItemHandlers(TestCase):

    def test_console_handler(self):
        logger = LoggerItem('app')
        self.assertDictEqual(logger.console(), {
            'console-oXLO3K5HR0': {
                'class': 'logging.StreamHandler',
                'formatter': 'default',
                'level': 'INFO',
                'stream': 'ext://sys.stdout'
            }
        })

    def test_file_handler(self):
        config = {
            'level': 'DEBUG',
            'handlers': [HandlerEnum.FILE],
            'formatter': 'simple',
            'log_path': '/tmp/logs/custom',
        }
        logger = LoggerItem('app', **config)
        self.assertDictEqual(logger.file(), {
            'file-oXLO3K5HR0': {
                'class': 'logging.FileHandler',
                'level': 'DEBUG',
                'formatter': 'simple',
                'filename': '/tmp/logs/custom/app.log',
            }
        })

    def test_rotate_handler(self):
        config = {
            'level': 'DEBUG',
            'handlers': [HandlerEnum.ROTATE],
            'formatter': 'simple',
            'log_path': '/tmp/logs/custom',
            'rotate_cnf': RotateConfig(max_bytes=204800, backup_count=10),
        }
        logger = LoggerItem('app', **config)
        self.assertDictEqual(logger.rotate(), {
            'rotate-oXLO3K5HR0': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'DEBUG',
                'formatter': 'simple',
                'filename': '/tmp/logs/custom/app.log',
                'maxBytes': 204800,
                'backupCount': 10,
            }
        })

    def test_error_handler(self):
        config = {
            'level': 'DEBUG',
            'handlers': [HandlerEnum.FILE],
            'formatter': 'simple',
            'log_path': '/tmp/logs/custom',
        }
        logger = LoggerItem('app', **config)
        self.assertDictEqual(logger.error(), {
            'error-oXLO3K5HR0': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'ERROR',
                'formatter': 'simple',
                'filename': '/tmp/logs/custom/app_error.log',
                'maxBytes': 104857600,
                'backupCount': 5,
            }
        })

    def test_get_handlers_dict(self):
        hargs = [HandlerEnum.ERROR, HandlerEnum.CONSOLE, HandlerEnum.FILE, HandlerEnum.ROTATE]
        logger = LoggerItem('app', handlers=hargs)
        self.assertDictEqual(logger.get_handlers_dict(), {
            'console-oXLO3K5HR0': {
                'class': 'logging.StreamHandler',
                'formatter': 'default',
                'level': 'INFO',
                'stream': 'ext://sys.stdout'
            },
            'file-oXLO3K5HR0': {
                'class': 'logging.FileHandler',
                'level': 'INFO',
                'formatter': 'default',
                'filename': '/tmp/logs/app.log',
            },
            'rotate-oXLO3K5HR0': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'INFO',
                'formatter': 'default',
                'filename': '/tmp/logs/app.log',
                'maxBytes': 104857600,
                'backupCount': 5,
            },
            'error-oXLO3K5HR0': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'ERROR',
                'formatter': 'default',
                'filename': '/tmp/logs/app_error.log',
                'maxBytes': 104857600,
                'backupCount': 5,
            },
        })


class TestLoggerConfig(TestCase):

    def test_default_values(self):
        with pytest.raises(ValueError, match="No logger configuration found"):
            LoggerConfig()

        logger = LoggerItem('app')
        config = LoggerConfig(loggers=[logger])
        assert config.formatters == [Formatter()]
        assert config.loggers == [logger]

        fmt = Formatter(name='simple', format='%(message)s')
        config = LoggerConfig(
            formatters=[fmt],
            loggers=[logger],
        )
        assert config.formatters == [fmt]
        assert config.loggers == [logger]

    def test_to_dict(self):
        fmts = [
            Formatter(name='default', format=DEFAULT_FORMAT),
            Formatter(name='simple', format='%(message)s'),
        ]
        loggers = [
            LoggerItem('test'),
            LoggerItem('app', level='DEBUG', formatter='simple', log_path='/tmp/logs/custom',
                       handlers=[HandlerEnum.ROTATE, HandlerEnum.ERROR]),
        ]
        config = LoggerConfig(
            formatters=fmts,
            loggers=loggers,
        )
        data = config.to_dict()

        assert data['version'] == 1
        self.assertListEqual(list(data.keys()), ['version', 'formatters', 'handlers', 'loggers'])
        self.assertDictEqual(data['formatters'], {
            'default': {'format': DEFAULT_FORMAT},
            'simple': {'format': '%(message)s'},
        })

        self.assertListEqual(
            list(data['handlers'].keys()),
            ['console-n4bQgYhMfW', 'rotate-oXLO3K5HR0', 'error-oXLO3K5HR0']
        )
        self.assertDictEqual(data['handlers'], {
            'console-n4bQgYhMfW': {
                'class': 'logging.StreamHandler',
                'formatter': 'default',
                'level': 'INFO',
                'stream': 'ext://sys.stdout'
            },
            'rotate-oXLO3K5HR0': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'DEBUG',
                'formatter': 'simple',
                'filename': '/tmp/logs/custom/app.log',
                'maxBytes': 104857600,
                'backupCount': 5,
            },
            'error-oXLO3K5HR0': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'ERROR',
                'formatter': 'simple',
                'filename': '/tmp/logs/custom/app_error.log',
                'maxBytes': 104857600,
                'backupCount': 5,
            }
        })

        self.assertDictEqual(sort_list(data['loggers']), sort_list({
            'test': {
                'level': 'INFO',
                'handlers': ['console-n4bQgYhMfW'],
                'propagate': False,
            },
            'app': {
                'level': 'DEBUG',
                'handlers': ['rotate-oXLO3K5HR0', 'error-oXLO3K5HR0'],
                'propagate': False,
            },
        }))

        self.assertDictEqual(sort_list(data), sort_list({
            'version': 1,
            'formatters': {
                'default': {'format': DEFAULT_FORMAT},
                'simple': {'format': '%(message)s'},
            },
            'handlers': {
                'console-n4bQgYhMfW': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'default',
                    'level': 'INFO',
                    'stream': 'ext://sys.stdout'
                },
                'rotate-oXLO3K5HR0': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'level': 'DEBUG',
                    'formatter': 'simple',
                    'filename': '/tmp/logs/custom/app.log',
                    'maxBytes': 104857600,
                    'backupCount': 5,
                },
                'error-oXLO3K5HR0': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'level': 'ERROR',
                    'formatter': 'simple',
                    'filename': '/tmp/logs/custom/app_error.log',
                    'maxBytes': 104857600,
                    'backupCount': 5,
                },
            },
            'loggers': {
                'test': {
                    'level': 'INFO',
                    'handlers': ['console-n4bQgYhMfW'],
                    'propagate': False,
                },
                'app': {
                    'level': 'DEBUG',
                    'handlers': ['rotate-oXLO3K5HR0', 'error-oXLO3K5HR0'],
                    'propagate': False,
                },
            },
        }))


class TestLoggerLoader(TestCase):
    def setUp(self) -> None:
        self.config_path = f"{os.getenv("APP_PATH", "")}/tests/data"
        self.empty_file = "/tmp/logloader-empty.yml"

    def tearDown(self) -> None:
        if os.path.exists(self.empty_file):
            os.remove(self.empty_file)

        return super().tearDown()

    def test_load_no_logging_config(self):
        with open(self.empty_file, 'w', encoding='utf-8') as f:
            f.write("")

        loader = LoggerLoader([self.empty_file])
        with pytest.raises(ValueError, match="No logging configuration found"):
            loader.load()

        with open(self.empty_file, 'w', encoding='utf-8') as f:
            f.write("logging:\n")
            f.write("  loggers:")

        loader = LoggerLoader([self.empty_file])
        with pytest.raises(ValueError, match="No logging configuration found"):
            loader.load()

    def test_load_config(self):
        config = LoggerLoader([f'{self.config_path}/config.yml']).load()

        self.assertListEqual(config.formatters, [
            Formatter(name='default', format=DEFAULT_FORMAT),
            Formatter(name='simple', format='%(message)s')
        ])
        self.assertListEqual([lg.name for lg in config.loggers], ['test', 'bug', 'sqlalchemy'])

        logger = get_logger('sqlalchemy')
        assert len(logger.handlers) == 3

    def test_log_path(self):
        confs = [
            f'{self.config_path}/config.yml',
            f'{self.config_path}/tmp.yml',
        ]
        config = LoggerLoader(confs).load()
        for logger in config.loggers:
            if logger.name == 'tmp':
                assert logger.log_path == 'data/tests/logs'
            elif logger.name == 'test':
                assert logger.log_path == 'data/tests/logs'
            elif logger.name == 'sqlalchemy':
                assert logger.log_path == 'data/tests/logs/sqlalchemy'

        # redefine default log path
        log_path = 'data/tests/logs/global'
        config = LoggerLoader([f'{self.config_path}/tmp.yml'], log_path=log_path).load()
        for logger in config.loggers:
            assert logger.log_path == log_path
