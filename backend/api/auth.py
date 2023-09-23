import os
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt, ExpiredSignatureError

from dotenv import load_dotenv

from api.encrypt_utils import verify_password
from db import models
from db import schemas

load_dotenv()

SECRET_KEY = str(os.getenv("SECRET_KEY")) or None
ALGORITHM = str(os.getenv("ALGORITHM")) or None
TOKEN_EXPIRES_TIME = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_user(db: Session, username: str) -> models.User | None:
    """
    Retrieves a user from the database using the provided username.

    :param db: The database session object to use for the query
    :type db: Session

    :param username: The username of the user to retrieve
    :type username: str

    :returns: The User object if found, otherwise None
    :rtype: models.User | None
    """
    user = db.query(models.User).where(
        models.User.username == username
    ).first()
    if user:
        return user
    return None


def authenticate_user(db: Session, username: str, password: str):
    """
    Authenticates a user using the provided username and password.

    :param db: The database session object to use for the query
    :type db: Session

    :param username: The username of the user to authenticate
    :type username: str

    :param password: The password to use for authentication
    :type password: str

    :returns: The User object if authentication succeeds, otherwise False
    :rtype: models.User | bool
    """

    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def check_token_expiration(token: Depends(oauth2_scheme)):
    """
    Checks the expiration status of a JWT token.

    :param token: The JWT token to check
    :type token: str

    :raises HTTPException: If the token has expired or the signature verification fails
    """
    try:
        jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been expired"
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token signature verification failed. "
                   "The token may have been tampered with."
        )


def create_jwt_token(
        data: dict,
        db: Session,
        time_expires: timedelta | None = None
) -> schemas.Token:
    """
    Creates a new JWT token or retrieves the existing one if it has not expired.

    :param data: The data to encode into the JWT token
    :type data: dict

    :param db: The database session object to use for queries
    :type db: Session

    :param time_expires: The expiration time for the token, if any
    :type time_expires: timedelta | None

    :returns: A Token object with the generated or retrieved
    JWT token and its expiration date
    :rtype: schemas.Token

    :raises HTTPException: If the user specified in data does not exist
    """

    to_encode = data.copy()
    username = to_encode.get("user")
    user = get_user(db, username)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    token_data = db.query(models.Token).where(
        models.Token.user_id == user.id
    ).order_by(
        models.Token.expires_date.desc()
    ).first()

    if (token_data and
            (token_data.expires_date - datetime.utcnow()) > timedelta(seconds=5)):

        return schemas.Token(
            user_id=token_data.user_id,
            token=token_data.token,
            expires_date=token_data.expires_date
        )

    if time_expires:
        token_time = datetime.utcnow() + time_expires
    else:
        token_time = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": token_time})
    jwt_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    new_token = models.Token(
        user_id=user.id,
        token=jwt_token,
        expires_date=token_time,
        is_expired=False
    )

    db.add(new_token)
    db.commit()

    return schemas.Token(
        token=jwt_token,
        expires_date=token_time
    )


def get_current_user(token: Depends(oauth2_scheme), db: Session) -> models.User:
    """
    Retrieves the current user based on the JWT token provided.

    :param token: The JWT token containing the user information
    :type token: str

    :param db: The database session object to use for queries
    :type db: Session

    :returns: The User object corresponding to the token
    :rtype: models.User

    :raises HTTPException: If there is an issue with
    the JWT token or the user does not exist
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authorized!",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        username = payload.get("user")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user(db, username)
    if user is None:
        raise credentials_exception
    return user
