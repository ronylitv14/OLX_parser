import os
import sys
from typing import List

# from dotenv import load_dotenv
from celery import Celery
from sqlalchemy.exc import OperationalError

from celery_worker.scraper import parse_full_request
from db.crud import create_advert
from db.schemas import AdvertisementCreate
from db.database import SessionLocal


BROKER_URL = os.getenv("BROKER_URL")
MAIN_URL = os.getenv("MAIN_URL")
BACKEND_URL = os.getenv("BACKEND_URL")

if not BROKER_URL:
    print("Error: You have to set `BROKER_URL` in environment variables")
    sys.exit(1)

celery_app = Celery(
    "celery_app",
    broker=BROKER_URL,
    backend=BACKEND_URL,
)


def get_and_save_date(
        query: str,
        limit: int,
        price_from: float,
        price_to: float,

):
    """
    Initiates the process to parse and save advertisement data based on user-defined criteria.

    :param query: The query string to use when parsing advertisements
    :type query: str

    :param limit: The maximum number of pages to parse
    :type limit: int

    :param price_from: The minimum price of the advertisements to parse
    :type price_from: float

    :param price_to: The maximum price of the advertisements to parse
    :type price_to: float
    """
    chain = parse_full_user_request.s(query, limit, price_from, price_to) | fill_adverts_db.s()
    chain()


@celery_app.task(name="parse_data")
def parse_full_user_request(
        query: str,
        limit: int,
        price_from: float = .0,
        price_to: float = .0
) -> List[dict]:
    """
    Celery task to parse advertisements data based on user criteria.

    :param query: The query string to use when parsing advertisements
    :type query: str

    :param limit: The maximum number of pages to parse
    :type limit: int

    :param price_from: The minimum price of the advertisements to parse, defaults to .0
    :type price_from: float, optional

    :param price_to: The maximum price of the advertisements to parse, defaults to .0
    :type price_to: float, optional

    :returns: A list of parsed advertisements as dictionaries
    :rtype: List[dict]
    """

    parsed_adverts = parse_full_request(
        netloc=MAIN_URL,
        query=query,
        limit=limit,
        price_from=price_from,
        price_to=price_to
    )

    return parsed_adverts


@celery_app.task(name="fill_db", ignore_result=True)
def fill_adverts_db(
        result,
):
    """
    Celery task to fill the database with parsed advertisement data.

    :param result: The list of parsed advertisements as dictionaries to save to the database
    :type result: list of dictionaries

    :raises OperationalError: If there is an error during database operations
    """

    db = SessionLocal()

    try:
        for advert in result:
            create_advert(
                db=db,
                advert=AdvertisementCreate(
                    title=advert["title"],
                    url=advert["url"],
                    price=advert["price"],
                    place=advert["place"],
                    tags=advert["tag"],
                    query=advert["query"],
                    date_added=advert["date_added"]
                )
            )

    except OperationalError as err:
        print(f"Error happened while saving data! Error info: {err}")
    finally:
        db.commit()
        db.close()
