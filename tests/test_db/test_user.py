# pylint:disable=disallowed-name
from datetime import datetime, timedelta
from unittest.mock import patch
from sqlmodel import Session
from .base import DBTestCase
from .user import User


class TestBaseModel(DBTestCase):

    @patch("mozi.utils.datetime")
    def test_update_time(self, mock_datetime):
        now = datetime(2021, 1, 1, 0, 0, 0)

        mock_now = mock_datetime.now
        mock_now.side_effect = [
            now,
            now + timedelta(seconds=10),
            now + timedelta(seconds=20)
        ]

        with Session(self.engine) as session:
            user = User(name='foo').update(session)

            assert user.id == 1
            assert user.email is None
            assert mock_now.call_count == 2  # created_at & updated_at
            assert user.created_at == now
            assert user.updated_at == datetime(2021, 1, 1, 0, 0, 10)

            user.update(session, email='test@example.com')
            assert user.id == 1
            assert user.email == 'test@example.com'
            assert mock_now.call_count == 3  # updated_at auto update
            assert user.created_at == now
            assert user.updated_at == datetime(2021, 1, 1, 0, 0, 20)

    def test_immutable_fields(self):
        with Session(self.engine) as session:
            user = User(name='foo').update(session)

            # pylint: disable=line-too-long
            with self.assertRaisesRegex(ValueError, "name is immutable and cannot be modified"):
                user.name = 'bar'
            with self.assertRaisesRegex(ValueError, "id is immutable and cannot be modified"):
                user.id = 2
            with self.assertRaisesRegex(ValueError, "created_at is immutable and cannot be modified"):
                user.created_at = datetime.now()
            with self.assertRaisesRegex(ValueError, "updated_at is immutable and cannot be modified"):
                user.updated_at = datetime.now()

            assert user.id == 1
            assert user.name == 'foo'

            with self.assertRaisesRegex(ValueError, "name is immutable and cannot be modified"):
                user.update(session, name='bar')


class TestUser(DBTestCase):

    def test_checkf(self):
        assert User.checkf('id')

        with self.assertRaises(ValueError):
            User.checkf('unkown')

    def test_create(self):
        with Session(self.engine) as session:
            User.create(session, name='foo')
            user = User.get_by_id(session, id=1)
            assert user.id == 1
            assert user.name == 'foo'

    def test_new_user(self):
        with Session(self.engine) as session:
            foo = User(name="foo").update(session)

            assert foo.id == 1
            assert foo.name == "foo"
            assert foo.uuid == "LCa0a2j_"
            assert foo.email is None
            assert foo.is_abled is True

            # create another user
            bar = User(
                name="bar",
                uuid="bar",
                email="bar@example.com",
                is_abled=False,
            ).update(session)
            assert bar.id == 2
            assert bar.name == "bar"
            assert bar.uuid == "bar"
            assert bar.email == "bar@example.com"
            assert bar.is_abled is False

            baz = User(id=3, name='baz').update(session)
            assert baz.id == 3

    def test_update(self):
        with Session(self.engine) as session:
            user = User(name='foo').update(session)

            assert user.id == 1
            assert user.uuid == 'LCa0a2j_'
            assert user.email is None

            # update fields
            user.email = 'foo@example.com'
            user.uuid = 'foo'
            user.update(session)

            assert user.id == 1
            assert user.uuid == 'foo'
            assert user.email == 'foo@example.com'

    def test_delete(self):
        with Session(self.engine) as session:
            user = User(name='foo').update(session)
            user.delete(session)
            assert User.get_by_id(session, 1) is None

    def test_get_by_id(self):
        with Session(self.engine) as session:
            user = User(name='foo').update(session)
            assert User.get_by_id(session, 1) == user

    def test_get_for_update(self):
        with Session(self.engine) as session:
            user = User(name='foo').update(session)
            assert User.get_for_update(session, 1) == user

    def test_get(self):
        with Session(self.engine) as session:
            assert User.get(session, name='foo') is None

            user = User.create(session, name='foo')
            assert user.id == 1
            result = User.get(session, name='foo')
            assert result is not None
            assert result.id == 1

            User.create(session, name='bar')
            assert User.count(session) == 2
            with self.assertRaisesRegex(ValueError, 'Multiple records found for User with'):
                User.get(session, is_abled=True)

    def test_gets_by_ids(self):
        with Session(self.engine) as session:
            assert User.count(session) == 0

            User(name='foo').update(session)
            User(name='bar').update(session)
            User(name='baz').update(session)

            assert User.count(session) == 3
            assert [u.name for u in User.gets_by_ids(session, [1, 2, 3])] == ['foo', 'bar', 'baz']

    def test_gets(self):
        with Session(self.engine) as session:
            assert User.count(session) == 0

            User(name='foo', age=13).update(session)
            User(name='bar', age=32).update(session)
            User(name='baz', age=None).update(session)

            count, users = User.gets(session, tart=0, limit=20, order_by='name')
            assert count == 3
            assert [u.name for u in users] == ['bar', 'baz', 'foo']

            # order by name desc
            count, users = User.gets(session, tart=0, limit=20, order_by='-name')
            assert count == 3
            assert [u.name for u in users] == ['foo', 'baz', 'bar']

            # start=0, limit=2
            count, users = User.gets(session, tart=0, limit=2, order_by='-name')
            assert count == 3
            assert [u.name for u in users] == ['foo', 'baz']

            # start=1, limit=2
            count, users = User.gets(session, start=1, limit=2, order_by='-name')
            assert count == 3
            assert [u.name for u in users] == ['baz', 'bar']

            # age >= 20 start=0, limit=2
            count, users = User.gets(
                session,
                start=0,
                limit=2,
                order_by='-name',
                filter_factory=lambda s: s.where(
                    User.age >= 20
                )
            )
            assert count == 1
