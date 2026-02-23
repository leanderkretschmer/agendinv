from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str
    password: str = Field(min_length=8)
    is_admin: bool = False


class LoginInput(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    username: str
    api_key: str
    is_admin: bool


class EndpointCreate(BaseModel):
    name: str
    provider: str
    config: Dict[str, Any] = Field(default_factory=dict)


class EndpointOut(BaseModel):
    id: int
    name: str
    provider: str
    config: Dict[str, Any]


class DataResponse(BaseModel):
    endpoint_id: int
    provider: str
    data: Dict[str, Any]


class DashboardContext(BaseModel):
    user: UserOut
    endpoints: List[EndpointOut]
    message: Optional[str] = None
