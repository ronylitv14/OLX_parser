FROM diliplakshya/python-3.11.1-poetry-slim-bullseye

WORKDIR /src/app

COPY ./pyproject.toml /src/app/pyproject.toml

# Install dependencies system-wide.
RUN poetry config virtualenvs.create false && poetry install --no-root

# Copy the application code to the container.
COPY ./api /src/app/api
COPY ./celery_worker /src/app/celery_worker
COPY ./db /src/app/db
COPY ./db_migrations /src/app/db_migrations
COPY ./alembic.ini /src/app/alembic.ini



