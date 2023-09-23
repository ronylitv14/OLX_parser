import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ARRAY
from sqlalchemy import UniqueConstraint, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class TokenType(enum.Enum):
    bearer: str = "BEARER"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String)
    hashed_password = Column(String)
    email = Column(String, nullable=True)
    is_superuser = Column(Boolean)

    def __init__(self, username: str, hashed_password: str, email: str, is_superuser: bool):
        self.username = username
        self.hashed_password = hashed_password
        self.email = email
        self.is_superuser = is_superuser


class Token(Base):
    __tablename__ = "tokens"

    token_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(ForeignKey("users.id"))
    token = Column(String, nullable=False)
    expires_date = Column(DateTime, nullable=False)
    token_type = Column(Enum(TokenType), default=TokenType.bearer, nullable=False)
    is_expired = Column(Boolean, nullable=False, default=False)

    def __init__(self, user_id: int, token: str, expires_date: datetime, is_expired: bool = False,
                 token_type: TokenType = None):
        self.user_id = user_id
        self.token = token
        self.expires_date = expires_date
        if token_type:
            self.token_type = token_type

        self.is_expired = is_expired


class Advertisement(Base):
    __tablename__ = "adverts"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    title = Column(String)
    url = Column(String)
    price = Column(Integer, nullable=True)
    place = Column(String, nullable=True)
    query = Column(String, nullable=False)
    date_added = Column(DateTime)
    date_created = Column(DateTime, default=datetime.now)
    tags = Column(String, nullable=True)

    # __table_args__ = (
    #     UniqueConstraint("title", "url", "query", name="unique_values"),
    # )

    def __init__(self, title: str, url: str, price: int, place: str, query: str, date_added: datetime, tags):
        self.title = title
        self.url = url
        self.place = place
        self.price = price
        self.query = query
        self.date_added = date_added
        self.tags = tags
        self.date_created = datetime.now()

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
