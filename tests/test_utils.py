import os
import shutil
from unittest import TestCase, mock

from mozi.utils import (
    deep_update, ensure_dir, get_config, get_timestamp, hmac_sha256, is_dev, is_prod, is_test,
    sort_list, timestamp_to_datetime, utc2datetime, uuid, is_debug
)


class TestEnv(TestCase):

    def test_is_test(self):
        assert is_test() is True
        assert is_dev() is False
        assert is_prod() is False
        assert is_debug() is True


class TestEnsureDir(TestCase):

    def setUp(self) -> None:
        self.base_dir = "/tmp/mozi-utils"
        self.test_dir = f"{self.base_dir}/tests"
        self.tmp_dir = f"{self.test_dir}/tmp"

        return super().setUp()

    def tearDown(self) -> None:
        if os.path.exists(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)

        return super().tearDown()

    def test_empty_dir(self):
        with self.assertRaises(ValueError):
            ensure_dir("")

    def test_exist_dir(self):
        assert os.path.exists(self.test_dir)
        assert ensure_dir(self.test_dir) == self.test_dir
        assert os.path.exists(self.test_dir)

        assert ensure_dir(f"{self.test_dir}/..") == "/tmp/mozi-utils"
        assert ensure_dir(f"{self.test_dir}/../tests/") == "/tmp/mozi-utils/tests"

    def test_file_path(self):
        file_path = f"{self.test_dir}/__init__.py"
        with open(file_path, 'a', encoding="utf-8") as f:
            f.write("foo")

        with self.assertRaises(ValueError):
            ensure_dir(file_path)

    def test_ensure_dir(self):
        assert os.path.exists(self.tmp_dir) is False
        assert ensure_dir(self.tmp_dir) == self.tmp_dir
        assert os.path.exists(self.tmp_dir)

    def test_recusion_mkdir(self):
        assert os.path.exists(self.tmp_dir) is False
        director = f"{self.tmp_dir}/foo/bar"
        assert ensure_dir(director) == director
        assert os.path.exists(director)


@mock.patch("time.time", return_value=1714026382.9015903)
def test_get_timestamp(mock_time):
    assert mock_time() == 1714026382.9015903
    assert get_timestamp() == 1714026382901


def test_timestamp_to_datetime():
    fmt = "%Y-%m-%d %H:%M:%S.%f%z"
    assert timestamp_to_datetime(1714026382901).strftime(fmt) == "2024-04-25 14:26:22.901000+0800"
    assert timestamp_to_datetime(1714026382901, timezone="Asia/Tokyo").strftime(fmt) == "2024-04-25 15:26:22.901000+0900"  # pylint: disable=line-too-long


def test_utc2datetime():
    assert utc2datetime("2024-04-25T06:26:22.901Z").strftime("%Y-%m-%d %H:%M:%S%z") == "2024-04-25 14:26:22+0800"  # pylint: disable=line-too-long


def test_hmac_sha256():
    sig = hmac_sha256("abcdefgh", "timestamp=1716540253587")
    assert sig == "8fffb1c6fc8b4afe33b572670f877429a1948233625f9a8c046b40d697f06c23"


def test_uuid():
    sig = uuid('hello world')
    assert sig == "uU0nuZNN"

    sig = uuid('hello world', length=4)
    assert sig == "uU0n"

    sig = uuid('hello world', length=10)
    assert sig == "uU0nuZNNPg"


class DeepUpdateTestCase(TestCase):
    def test_deep_update_with_empty(self):
        assert not deep_update({}, {})

        data = {'a': 1, 'b': 2}
        assert deep_update({}, data) == data
        assert deep_update(data, {}) == data

    def test_deep_update(self):
        dict1 = {'a': 1, 'b': 2}
        dict2 = {'b': 3, 'c': 4}
        assert deep_update(dict1, dict2) == {'a': 1, 'b': 3, 'c': 4}

    def test_deep_update_nested(self):
        dict1 = {'a': {'x': 1}, 'b': 2}
        dict2 = {'a': {'y': 2}, 'c': 3}
        expected = {'a': {'x': 1, 'y': 2}, 'b': 2, 'c': 3}
        assert deep_update(dict1, dict2) == expected

    def test_deep_update_overwrite(self):
        dict1 = {'a': {'x': 1}, 'b': 2}
        dict2 = {'a': {'x': 2}, 'b': 3}
        expected = {'a': {'x': 2}, 'b': 3}
        assert deep_update(dict1, dict2) == expected


class TestYamlConfigFile(TestCase):

    def setUp(self) -> None:
        self.config_path = f"{os.getenv("APP_PATH", "")}/tests/data"
        self.empty_file = "/tmp/empty.yml"

        self.tmp_config_value = {
            'logging': {
                'loggers': {
                    'tmp': {
                        'handlers': ['console', 'rotate'],
                    },
                    'sqlalchemy': {
                        'handlers': ['console'],
                        'level': 'INFO'
                    }
                }
            }
        }

        self.config_value = {
            'logging': {
                'log_path': 'data/tests/logs',
                'formatters': {
                    'default': {
                        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                    },
                    'simple': {
                        'format': '%(message)s'
                    }
                },
                'loggers': {
                    'test': {
                        'handlers': ['console']
                    },
                    'bug': None,
                    'sqlalchemy': {
                        'level': 'DEBUG',
                        'handlers': ['console', 'rotate', 'error'],
                        'formatter': "simple",
                        'propagate': True,
                        'log_path': 'data/tests/logs/sqlalchemy',
                    }
                }
            }
        }

    def tearDown(self) -> None:
        if os.path.exists(self.empty_file):
            os.remove(self.empty_file)

        return super().tearDown()

    def test_file_not_exists(self):
        with self.assertRaises(FileNotFoundError):
            get_config(["nonexistent.yaml"])

    def test_empty_file(self):
        with self.assertRaises(FileNotFoundError):
            get_config([""])

        with open('/tmp/empty.yml', 'w', encoding='utf-8') as f:
            f.write("")
        assert get_config([self.empty_file]) == {}

    def test_file_overwrite(self):
        config = get_config([f"{self.config_path}/tmp.yml"])
        self.assertDictEqual(config, self.tmp_config_value)

        config = get_config([f"{self.config_path}/config.yml"])
        self.assertDictEqual(sort_list(config), sort_list(self.config_value))

        # 配置文件覆盖
        config = get_config([f"{self.config_path}/tmp.yml", f"{self.config_path}/config.yml"])
        self.assertDictEqual(
            sort_list(config),
            sort_list(deep_update(self.tmp_config_value, self.config_value))
        )

        # get by key
        config = get_config([f"{self.config_path}/config.yml"], key="logging")
        self.assertDictEqual(
            sort_list(config),
            sort_list(self.config_value['logging'])
        )


def test_sort_list():
    assert not sort_list({})
    assert sort_list({'a': 1, 'b': 2}) == {'a': 1, 'b': 2}
    assert sort_list({'a': [3, 2, 1]}) == {'a': [1, 2, 3]}
    assert sort_list({'a': {'b': [3, 2, 1]}}) == {'a': {'b': [1, 2, 3]}}
    assert sort_list({'a': {'b': {'c': [3, 2, 1]}}}) == {'a': {'b': {'c': [1, 2, 3]}}}
