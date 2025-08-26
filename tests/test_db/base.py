import os
import unittest
from sqlmodel import create_engine

from mozi.db import create_tables, drop_tables


engine = create_engine(
    url=os.getenv("POSTGRES_URL", ""),  # 测试环境使用 sqlite 代替 postgres
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
