import os

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

from dotenv import load_dotenv


user = os.getenv("POSTGRES_USER")
password = os.getenv("POSTGRES_PASSWORD")
db_name = os.getenv("POSTGRES_DB")

print(user)
print(password)
print(db_name)

SQLALCHEMY_DATABASE_URL = f"postgresql://{user}:{password}@db/{db_name}"

try:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,

    )

except OperationalError:
    print(user)
    print(password)
    print(db_name)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

