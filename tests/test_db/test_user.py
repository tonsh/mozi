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

        user = User(name='foo').update()

        assert user.id == 1
        assert user.email is None
        assert mock_now.call_count == 2  # created_at & updated_at
        assert user.created_at == now
        assert user.updated_at == datetime(2021, 1, 1, 0, 0, 10)

        user.update(email='test@example.com')
        assert user.id == 1
        assert user.email == 'test@example.com'
        assert mock_now.call_count == 3  # updated_at auto update
        assert user.created_at == now
        assert user.updated_at == datetime(2021, 1, 1, 0, 0, 20)

    def test_immutable_fields(self):
        user = User(name='foo').update()

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
            user.update(name='bar')


class TestUser(DBTestCase):

    def test_checkf(self):
        assert User.checkf('id')

        with self.assertRaises(ValueError):
            User.checkf('unkown')

    def test_create(self):
        User.create(name='foo')
        user = User.get_by_id(id=1)
        assert user is not None
        assert user.id == 1
        assert user.name == 'foo'

    def test_new_user(self):
        foo = User(name="foo").update()

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
        ).update()
        assert bar.id == 2
        assert bar.name == "bar"
        assert bar.uuid == "bar"
        assert bar.email == "bar@example.com"
        assert bar.is_abled is False

        baz = User(id=3, name='baz').update()
        assert baz.id == 3

    def test_update(self):
        user = User(name='foo').update()

        assert user.id == 1
        assert user.uuid == 'LCa0a2j_'
        assert user.email is None

        # update fields
        user.email = 'foo@example.com'
        user.uuid = 'foo'
        user.update()

        assert user.id == 1
        assert user.uuid == 'foo'
        assert user.email == 'foo@example.com'

    def test_delete(self):
        user = User(name='foo').update()
        user.delete()
        assert User.get_by_id(1) is None

    def test_get_by_id(self):
        user = User(name='foo').update()
        assert User.get_by_id(1) == user

    def test_get_for_update(self):
        user = User(name='foo').update()
        with Session(self.engine) as session:
            user_for_update = User.get_for_update(session, 1)
            assert user_for_update is not None
            assert user_for_update == user
            assert user_for_update.is_abled is True

            # 注意：若此处使用 user_for_update.update() 会破坏事务
            user_for_update._update(session, is_abled=False)  # pylint: disable=protected-access
            assert user_for_update.is_abled is False

    def test_get(self):
        assert User.get(name='foo') is None

        user = User.create(name='foo')
        assert user.id == 1
        result = User.get(name='foo')
        assert result is not None
        assert result.id == 1

        User.create(name='bar')
        assert User.count() == 2
        with self.assertRaisesRegex(ValueError, 'Multiple records found for User with'):
            User.get(is_abled=True)

    def test_gets_by_ids(self):
        assert User.count() == 0

        User(name='foo').update()
        User(name='bar').update()
        User(name='baz').update()

        assert User.count() == 3
        assert [u.name for u in User.gets_by_ids([1, 2, 3])] == ['foo', 'bar', 'baz']

    def test_gets(self):
        assert User.count() == 0

        User(name='foo', age=13).update()
        User(name='bar', age=32).update()
        User(name='baz', age=None).update()

        count, users = User.gets(tart=0, limit=20, order_by='name')
        assert count == 3
        assert [u.name for u in users] == ['bar', 'baz', 'foo']

        # order by name desc
        count, users = User.gets(tart=0, limit=20, order_by='-name')
        assert count == 3
        assert [u.name for u in users] == ['foo', 'baz', 'bar']

        # start=0, limit=2
        count, users = User.gets(tart=0, limit=2, order_by='-name')
        assert count == 3
        assert [u.name for u in users] == ['foo', 'baz']

        # start=1, limit=2
        count, users = User.gets(start=1, limit=2, order_by='-name')
        assert count == 3
        assert [u.name for u in users] == ['baz', 'bar']

        # age >= 20 start=0, limit=2
        count, users = User.gets(
            start=0,
            limit=2,
            order_by='-name',
            filter_factory=lambda s: s.where(
                User.age >= 20
            )
        )
        assert count == 1

    def test_all(self):
        assert User.count() == 0

        User(name='foo', age=13).update()
        User(name='bar', age=32).update()
        User(name='baz', age=None).update()

        users = User.all(order_by='name')
        assert [u.name for u in users] == ['bar', 'baz', 'foo']

        # order by name desc
        users = User.all(order_by='-name')
        assert [u.name for u in users] == ['foo', 'baz', 'bar']

        # age >= 20
        users = User.all(
            order_by='-name',
            filter_factory=lambda s: s.where(
                User.age >= 20
            )
        )
        assert [u.name for u in users] == ['bar']
