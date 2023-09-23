FROM szwarc/python-3.11-bullseye-poetry

LABEL authors="ronylitv"

WORKDIR /src/app

COPY requirements.txt /src/app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY ./utils /src/app/utils
COPY ./dashboard.py /src/app/dashboard.py


CMD ["streamlit", "run", "dashboard.py"]
