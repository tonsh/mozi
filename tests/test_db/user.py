from typing import Optional
from sqlmodel import Field
from mozi.db import BaseModel
from mozi.utils import uuid


class User(BaseModel, table=True):
    __tablename__ = "users"

    name: str = Field(unique=True)
    uuid: Optional[str] = Field(unique=True, default=None)
    email: Optional[str] = Field(default=None)
    age: Optional[int] = Field(default=None)
    is_abled: bool = Field(default=True)

    __immutable_fields__ = {'name'}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if not self.uuid:
            self.uuid = uuid(self.name)
