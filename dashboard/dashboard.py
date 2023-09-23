import os.path

import streamlit as st
import requests
from plotly import express as px

from dotenv import load_dotenv

# Importing necessary modules for data retrieval and preprocessing
from utils.market_data_preprocessing import (
    get_data,
    preprocess_data,
    InvalidAuthData,
    CATEGORIES
)

load_dotenv(os.path.join(os.curdir, ".env"))

DATA_API_DOMAIN = os.getenv("DATA_API_DOMAIN")

# Setting up the page configuration for the Streamlit app
st.set_page_config(
    page_title="Real-time analysis of secondary market data",
    page_icon=":star:",
    layout="wide"
)


# Form to accept user inputs for data analysis
with st.form("my_form"):
    form_col1, form_col2 = st.columns(2)

    username = form_col1.text_input("Username", help="user1")
    password = form_col2.text_input("Password", help="123456", type="password")

    # Fetching query options from the API
    # query_options = requests.get(f"{DATA_API_DOMAIN}/query-types").json()
    # query_options.append("all")

    # Setting up columns for different input fields
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    # Input fields for selecting query, start date, end date, and price range
    # query = col1.selectbox("Tags", options=query_options)
    query = col1.text_input("Query")
    start_date = col2.date_input(label="Start date", )
    end_date = col3.date_input(label="End date")
    price_from = col4.number_input(label="Price from", min_value=0)
    price_to = col5.number_input(label="Price to", min_value=0)
    category = col6.selectbox("Category", options=CATEGORIES)

    # Submit button for the form
    btn_submit = st.form_submit_button("Submit")

# Data retrieval and visualization if the form is submitted
try:
    if btn_submit:
        token_data = requests.request(
            method="POST",
            url=f"{DATA_API_DOMAIN}/token",
            data={
                "content-type": "multipart/form-data",
                'username': username,
                'password': password
            }

        )

        token_data.raise_for_status()
        token_data = token_data.json()

        # Getting data based on user inputs

        df = get_data(
            params={
                "query": query,
                "date_from": start_date,
                "date_to": end_date
            },
            token_data=token_data
        )

        # Preprocessing data based on price range inputs
        if not (price_from == 0.0 and price_to == 0.0):
            df = preprocess_data(
                market_df=df,
                price_from=price_from,
                price_to=price_to,
                category=category
            )

        # Displaying data frame
        st.dataframe(df)

        # Setting up columns for different plots
        fig_col1, fig_col2 = st.columns(2)

        # Creating and displaying a scatter plot
        fig_col1.markdown("## Scatter plot for price")
        fig1 = px.scatter(
            data_frame=df,
            x="date_added",
            y="price",
            hover_data="title"
        )
        fig_col1.write(fig1)

        # Creating and displaying a histogram
        fig_col2.markdown("## Price Histogram")
        fig2 = px.histogram(
            data_frame=df,
            x="price"
        )
        fig_col2.write(fig2)

        # Creating and displaying a pie chart
        pie_chart = px.pie(
            data_frame=df,
            names="place",
        )
        pie_chart.update_traces(textposition='inside')
        pie_chart.update_layout(uniformtext_minsize=12, uniformtext_mode='hide')
        st.write(pie_chart)
except InvalidAuthData:
    st.write("Auth data is invalid!")

except requests.exceptions.HTTPError as err:
    st.write(f"Something wrong with API connection!\n\nError: {err.response.json()}")

except KeyError as err:
    st.write(f"Wrong query name! Try again: {err}")
