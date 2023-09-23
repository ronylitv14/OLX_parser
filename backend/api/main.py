from datetime import date, timedelta
from typing import List

from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm


from db import schemas
from db.crud import get_adverts, get_distinct_queries
from db.database import SessionLocal
from api.auth import (
    authenticate_user,
    create_jwt_token,
    oauth2_scheme,
    check_token_expiration,
)
from api.auth import TOKEN_EXPIRES_TIME

from celery_worker.worker import celery_app, get_and_save_date

olx_app = FastAPI()


def get_db() -> Session:
    db = SessionLocal()
    return db


@olx_app.post("/token", response_model=schemas.Token)
async def get_token_data(form_date: OAuth2PasswordRequestForm = Depends()):
    """
    Endpoint to get token data for a user.

    :param form_date: OAuth2 password request form data
    :type form_date: OAuth2PasswordRequestForm, default is Depends()

    :return: JWT token data
    :rtype: schemas.Token

    :raises HTTPException: If the username or password is incorrect
    """

    db = get_db()
    user = authenticate_user(db, form_date.username, form_date.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_time = timedelta(minutes=TOKEN_EXPIRES_TIME)
    access_token = create_jwt_token(
        {"user": user.username}, db=db, time_expires=access_token_time
    )

    return access_token


@olx_app.post("/api/v1/adverts")
async def save_olx_data(
    query: str,
    limit: int = 1,
    price_from: float = 0.0,
    price_to: float = 0.0,
    token: str = Depends(oauth2_scheme),
):
    """
    Endpoint to save OLX data asynchronously.

    :param query: The query string for searching adverts
    :type query: str

    :param limit: The number of adverts to retrieve, defaults to 1
    :type limit: int, optional

    :param price_from: The minimum price of adverts, defaults to .0
    :type price_from: float, optional

    :param price_to: The maximum price of adverts, defaults to .0
    :type price_to: float, optional

    :param token: Authentication token, default is extracted from the request headers
    :type token: str, optional

    :return: JSON response indicating the task status
    :rtype: JSONResponse

    :raises HTTPException: If backend is not responding or query param is missing
    """
    check_token_expiration(token=token)

    celery_status = celery_app.control.ping()

    if not query:
        return JSONResponse(
            content={
                "error": "You should specify `query` param",
            },
            status_code=status.HTTP_400_BAD_REQUEST,
            media_type="application/json",
        )

    if not celery_status:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Backend doesn`t work well! Try again later!",
        )

    get_and_save_date(query, limit, price_from, price_to)

    return JSONResponse(
        content={
            "msg": "Task added to the queue",
        },
        status_code=status.HTTP_200_OK,
        media_type="application/json",
    )


@olx_app.get("/api/v1/adverts", response_model=List[schemas.Advertisement])
async def get_data_from_db(
    query: str, date_from: date, date_to: date, token: str = Depends(oauth2_scheme)
):
    """
    Endpoint to retrieve data from the database based on query and date range.

    :param query: The query string for searching adverts
    :type query: str

    :param date_from: The start date for retrieving adverts
    :type date_from: date

    :param date_to: The end date for retrieving adverts
    :type date_to: date

    :param token: Authentication token, default is extracted from the request headers
    :type token: str, optional

    :return: List of advertisements matching the criteria
    :rtype: List[schemas.Advertisement]

    :raises HTTPException: If there is a database error
    """
    check_token_expiration(token=token)

    db = get_db()

    try:
        data = get_adverts(db=db, query=query, start_date=date_from, end_date=date_to)
    except OperationalError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error with database!",
        )

    finally:
        db.close()

    return data


@olx_app.get("/api/v1/query-types", response_class=JSONResponse)
async def get_query_types(token: str = Depends(oauth2_scheme)):
    """
    Endpoint to retrieve distinct query types from the database.

    :param token: Authentication token, default is extracted from the request headers
    :type token: str, optional

    :return: JSON response with distinct query types
    :rtype: JSONResponse

    :raises HTTPException: If there is a database error
    """
    check_token_expiration(token=token)

    db = get_db()

    try:
        distinct_queries = get_distinct_queries(db=db)
    except OperationalError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error with database!",
        )
    finally:
        db.close()

    return distinct_queries
