import os
import shutil
from unittest import TestCase, mock

from mozi.utils import (
    ensure_dir, get_timestamp, hmac_sha256, is_dev, is_prod, is_test,
    timestamp_to_datetime
)


class TestEnv(TestCase):

    def test_is_test(self):
        assert is_test() is True
        assert is_dev() is False
        assert is_prod() is False


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


def test_hmac_sha256():
    sig = hmac_sha256("abcdefgh", "timestamp=1716540253587")
    assert sig == "8fffb1c6fc8b4afe33b572670f877429a1948233625f9a8c046b40d697f06c23"
