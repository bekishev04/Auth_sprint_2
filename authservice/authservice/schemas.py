import datetime
import uuid
from typing import List

from pydantic import BaseModel as PydanticBaseModel, validator, Field

from authservice.entrypoints import enums


class BaseModel(PydanticBaseModel):
    """Base Model"""

    class Config:
        anystr_strip_whitespace = True


class BaseModelSchema(PydanticBaseModel):
    """Base Model Schema"""

    id: uuid.UUID

    class Config:
        orm_mode = True


class RespMessage(BaseModel):
    message: str


class RespCreated(BaseModel):
    id: uuid.UUID


class RespLogon(BaseModel):
    access_token: str
    refresh_token: uuid.UUID


class ItemUser(BaseModelSchema):
    """Item Schema For User"""

    login: str
    full_name: str
    role: str


class ItemsUser(BaseModel):
    """List Item Schema of Users"""

    total: int = 0
    items: List[ItemUser]


class RespAuth(ItemUser):
    """Schema Resp Auth UserModel & token"""

    token: uuid.UUID | None


class AuthSchema(BaseModel):
    """Schema For Auth"""

    login: str
    password: str


class ReqUpdateUser(BaseModel):
    """Req Schema for Update User"""

    full_name: str
    login: str
    role: enums.UserRole


class ReqCreateUser(BaseModel):
    """Req Schema for Create User"""

    full_name: str
    login: str
    password: str


class ReqUserPasswordEdit(BaseModel):
    """Req For Edit Password Schema"""

    password_old: str
    password: str
    password_repeat: str

    @validator("password")
    def passwords_match(cls, v, values):

        # совпадение паролей
        if "password_repeat" in values and v != values["password_repeat"]:
            raise ValueError("Passwords don't match")

        return v


class ArgsPaginate(BaseModel):
    """Args Schema paginate"""

    offset: int = Field(0, ge=0, description="Номер сдвига")
    limit: int = Field(50, gt=0, description="Кол-во элементов")


class ArgsUser(ArgsPaginate):
    """Args Schema paginate For User"""

    full_name: str | None
    role: str | None
    login: str | None


class ReqLogin(BaseModel):
    """Req for login"""

    login: str
    password: str
    user_agent: str | None


class ReqRefreshToken(BaseModel):
    refresh_token: uuid.UUID


class ReqLogout(BaseModel):
    access_token: str
    refresh_token: uuid.UUID


class JWTPayload(BaseModelSchema):
    login: str | None
    full_name: str | None
    role: str
    valid_through: datetime.datetime


class ItemSession(BaseModelSchema):
    """Item of User Session"""

    created_at: datetime.datetime
    updated_at: datetime.datetime
    is_active: bool


class ItemsSession(BaseModel):
    """List of User Session Items"""

    total: int = 0
    items: List[ItemSession]


class RespHistory(BaseModelSchema):
    user_id: uuid.UUID
    logged_in_at: datetime.datetime
    user_agent: str


class RespHistoryItems(BaseModel):
    items: List[RespHistory]


class ReqHistory(BaseModel):
    user_id: uuid.UUID | None
    before: datetime.datetime | None
    after: datetime.datetime | None
