# pylint: disable=redefined-builtin
from datetime import datetime
from typing import Any, Generic, List, Optional, TypeVar, Union
from sqlalchemy import Engine
from sqlmodel import SQLModel, Field, Session, func, select
from sqlmodel.sql.expression import Select, SelectOfScalar

from .logger import get_logger
from .utils import now

Statement = Union[Select, SelectOfScalar]
logger = get_logger('sqlalchemy.engine')


def create_db_and_tables(engine: Engine):
    """Create database and tables"""
    SQLModel.metadata.create_all(engine)


def drop_db_and_tables(engine: Engine):
    """Drop database and tables"""
    SQLModel.metadata.drop_all(engine)


class BaseTable(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: Optional[datetime] = Field(default_factory=now)
    updated_at: Optional[datetime] = Field(
        default_factory=now,
        sa_column_kwargs={
            'onupdate': now,
        },
    )

    __immutable_fields__: set = set()

    def __setattr__(self, name: str, value: Any) -> None:
        self.__immutable_fields__.update({'id', 'created_at', 'updated_at'})

        if name in self.__immutable_fields__ and getattr(self, name) is not None:
            raise ValueError(f'{name} is immutable and cannot be modified')

        return super().__setattr__(name, value)


# Uses TypeVar and Generic to ensure type safety
T = TypeVar('T', bound=BaseTable)


class DBMixin(Generic[T]):
    """
    A mixin class that provides common database operations for SQLModel models.
    Generic type T must be a SQLModel subclass.
    """
    @classmethod
    def checkf(cls, field) -> bool:
        if not hasattr(cls, field):
            raise ValueError(f'{cls.__name__} has no `{field}` attribute.')
        return True

    def _upsert(self, session: Session) -> T:
        """ Update or insert a record. """
        try:
            session.add(self)
            session.commit()
            session.refresh(self)
            return self  # type: ignore
        except Exception:
            session.rollback()
            raise

    def _delete(self, session: Session):
        try:
            session.delete(self)
            session.commit()
        except Exception:
            session.rollback()
            raise

    @classmethod
    def _all(cls, session: Session, statement: Statement) -> List[T]:
        result = list(session.exec(statement).all())
        return result or result[0]

    @classmethod
    def _filter_by(cls, only_count: bool = False, **kwargs) -> Statement:
        """Filter records by given criteria."""
        if only_count:
            statement = select(func.count(cls.id))  # pylint: disable=not-callable  # type: ignore
        else:
            statement = select(cls)

        for key, value in kwargs.items():
            if hasattr(cls, key):
                statement = statement.where(getattr(cls, key) == value)
        return statement

    def update(self, session: Session, **kwargs) -> T:
        for key, val in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, val)
        return self._upsert(session)

    def delete(self, session: Session):
        return self._delete(session)

    @classmethod
    def get_by_id(cls, session: Session, id: int) -> Optional[T]:
        """Get a record by its ID."""
        return session.get(cls, id)  # type: ignore

    @classmethod
    def get_for_update(cls, session: Session, id: int) -> Optional[T]:
        """ 使用 with_for_update 方法，可以确保在查询记录时锁定这些记录，以防止其他事务修改它们。"""
        statement = cls._filter_by(id=id).with_for_update()
        return session.exec(statement).one_or_none()

    @classmethod
    def gets_by_ids(cls, session: Session, ids: List[int]) -> List[T]:
        if not ids:
            return []

        statement = select(cls).where(cls.id.in_(ids))  # type: ignore
        return cls._all(session, statement)

    @classmethod
    def count(cls, session: Session, **kwargs) -> int:
        statement = cls._filter_by(only_count=True, **kwargs)
        return session.exec(statement).first() or 0

    @classmethod
    def gets(cls, session: Session, start: int = 0, limit: int = 20, order_by: Optional[str] = None, **kwargs) -> tuple[int, List[T]]:  # pylint: disable=line-too-long
        total = cls.count(session, **kwargs)

        statement = cls._filter_by(**kwargs)
        if order_by:
            if order_by.startswith('-'):
                order_by = getattr(cls, order_by[1:]).desc()
            else:
                order_by = getattr(cls, order_by)
            statement = statement.order_by(order_by)
        statement = statement.offset(start).limit(limit)

        return total, cls._all(session, statement)


class BaseModel(BaseTable, DBMixin):
    pass
