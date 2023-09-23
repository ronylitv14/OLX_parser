from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.dialects.postgresql import insert as psql_upsert
from db.models import Advertisement
from db.schemas import AdvertisementCreate


def create_advert(
        db: Session,
        advert: AdvertisementCreate
):
    """
    Creates or updates an advert in the database.

    If an advert with the same url, title, and query exists in the database, it updates
    the title, url, and query fields of the existing record with new values and updates
    the date_created to the current datetime. Otherwise, it creates a new record.

    :param db: The database session object
    :type db: Session

    :param advert: The advert object containing the details to be added or updated in the database
    :type advert: AdvertisementCreate
    """
    db_advert = Advertisement(
        title=advert.title,
        url=advert.url,
        place=advert.place,
        price=advert.price,
        query=advert.query,
        date_added=advert.date_added,
        tags=advert.tags
    )

    # stmt = psql_upsert(Advertisement).values(db_advert.to_dict()).on_conflict_do_update(
    #     index_elements=['url', 'title', 'query'],
    #     set_=dict(title=advert.title, url=advert.url, query=advert.query, date_created=datetime.now())
    # )
    # db.execute(stmt)
    db.add(db_advert)


def get_adverts(
        db: Session,
        query: str,
        start_date: date,
        end_date: date
):

    """
    Retrieves adverts from the database based on the query parameter and date range.

    If query parameter is "all", it retrieves all adverts added within the date range and having a non-null price.
    Otherwise, it retrieves adverts matching the query parameter and added within the date range.

    :param db: The database session object
    :type db: Session

    :param query: The query string used to filter adverts based on their query field
    :type query: str

    :param start_date: The start date of the date range within which to filter the adverts
    :type start_date: date

    :param end_date: The end date of the date range within which to filter the adverts
    :type end_date: date

    :return: A list of advert objects matching the criteria
    :rtype: List[Advertisement]
    """
    if query == "all":
        stmt = select(Advertisement).where(
            Advertisement.date_added > start_date
        ).where(
            Advertisement.date_added <= end_date
        ).where(
            Advertisement.price != None
        )

    else:
        stmt = select(Advertisement).where(
            Advertisement.query.ilike(f"%{query}%")
        ).where(
            Advertisement.date_added > start_date
        ).where(
            Advertisement.date_added <= end_date
        )

    data = [item[0] for item in db.execute(stmt).all()]

    return data


def get_distinct_queries(
        db: Session
):
    """
    Retrieves distinct query strings from the adverts stored in the database.

    :param db: The database session object
    :type db: Session

    :return: A list of distinct query strings from the database
    :rtype: List[str]
    """
    return [item[0] for item in db.query(Advertisement.query).distinct().all()]




