from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    api_key: str = Field(index=True, unique=True)
    is_admin: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DataEndpoint(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: int = Field(index=True, foreign_key="user.id")
    name: str
    provider: str = Field(index=True)
    config_json: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
