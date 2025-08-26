import unittest
from sqlmodel import create_engine

from mozi.db import create_tables, drop_tables


TEST_DB_URI = "sqlite:////var/tmp/mozi-test.db"
engine = create_engine(
    url=TEST_DB_URI,
    echo=False,
    pool_pre_ping=True,  # Check if the connection is alive
)


class DBTestCase(unittest.TestCase):

    def setUp(self):
        create_tables(engine)
        self.engine = engine

        return super().setUp()

    def tearDown(self):
        drop_tables(engine)

        return super().tearDown()
