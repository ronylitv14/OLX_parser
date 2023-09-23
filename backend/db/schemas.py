from datetime import datetime
from pydantic import BaseModel

from db.models import TokenType


# Users classes
class UserBase(BaseModel):
    username: str
    hashed_password: str
    email: str | None
    is_superuser: bool


class User(UserBase):
    id: int

    class Config:
        from_attributes = True


# Token classes

class TokenBase(BaseModel):
    token: str
    token_type: TokenType = TokenType.bearer


class Token(TokenBase):
    expires_date: datetime


class TokenModel(Token):
    token_id: int
    user_id: int
    is_expired: bool

    class Config:
        from_attributes = True


# Adverts classes
class AdvertisementBase(BaseModel):
    title: str
    url: str
    price: int | None
    place: str | None
    query: str | None
    date_added: datetime
    tags: str | None


class AdvertisementCreate(AdvertisementBase):
    pass


class Advertisement(AdvertisementBase):
    id: int

    class Config:
        from_attributes = True
