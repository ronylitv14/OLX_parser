from typing import Optional, Dict

import pandas as pd
import streamlit as st
import requests

import os
from dotenv import load_dotenv

load_dotenv()


class InvalidAuthData(Exception):
    pass


CATEGORIES = ["Электроника", "Детский мир", "Недвижимость", "Авто", "Запчасти для транспорта",
              "Работа", "Животные", "Дом и сад", "Электроника", "Бизнес и услуги", "Аренда и прокат",
              "Мода и стиль", "Хобби, отдых и спорт", "Отдам даром", "Обмен", "Авто для победы",
              "Товары для школы", "Товары для победы"]

DATA_API_DOMAIN = os.getenv("DATA_API_DOMAIN")


@st.cache_data
def get_data(
        params: Optional[Dict | None],
        token_data: dict
) -> pd.DataFrame:
    token = token_data.get("token")
    token_type = token_data.get("token_type")

    if not (token and token_type):
        raise InvalidAuthData

    response = requests.get(
        url=f"{DATA_API_DOMAIN}/api/v1/adverts",
        params=params,
        headers={
            "Authorization": f"{token_data['token_type'].title()} {token_data['token']}"
        }
    )

    data = response.json()
    data = pd.DataFrame(data)

    return data[["title", "url", "price", "place", "tags", "query", "date_added"]]


@st.cache_data
def preprocess_data(
        market_df: pd.DataFrame,
        price_from: float,
        price_to: float,
        category: str
):
    if not (price_to and price_from):
        return market_df
    return market_df[
        (market_df["price"] >= price_from) & (market_df["price"] <= price_to) & (market_df["tags"] == category)]
