import os
import re

from dateparser import parse
from typing import List

from dotenv import load_dotenv

import requests
from urllib.parse import urlencode, urlunparse
from bs4 import BeautifulSoup, Tag

load_dotenv()

MAIN_URL = str(os.getenv("MAIN_URL")) or None
PARSER = str(os.getenv("PARSER")) or None
REGEX_PATTERN = r"^(\d{1,3}(?: \d{3})*) .*$"


def parse_one_page(url: str, find_category: bool):
    """
    Parsing page from OLX to get separate cards of advertisement

    :param url: link for OLX page of advertisements
    :type url: str

    :returns: tuple of list of bs4.Tag`s and url to the next page
    :rtype: tuple(list(bs4.Taf), str)
    """

    response = requests.get(
        url=url,
    )

    soup = BeautifulSoup(
        response.text,
        features=PARSER
    )

    if find_category:

        all_categories = soup.find_all(
            "li",
            attrs={
                "class": "css-szrfjb"
            }
        )

        category_hrefs = []
        max_quantity_ind = 0
        max_quantity = 0

        for ind, cat in enumerate(all_categories):
            quantity_adverts = cat.a.span.text
            advert_title = cat.a.text.removesuffix(quantity_adverts)

            quantity_adverts = quantity_adverts.replace("\xa0", "")

            href = cat.a.get("href")

            if (q := int(quantity_adverts)) > max_quantity:
                max_quantity = q
                max_quantity_ind = ind

            category_hrefs.append((advert_title, href))

        return [], category_hrefs[max_quantity_ind]

    all_ads = soup.find_all(
        attrs={
            "data-cy": re.compile("l-card")
        }
    )

    next_page = soup.find(
        attrs={
            "data-testid": re.compile("pagination-forward")
        }
    )

    href = next_page.get("href")

    return all_ads, href


def parse_advertisement(advert_card: Tag) -> dict:
    """
    Parses the content of a single advertisement card from OLX and extracts various details such as the title, URL,
    price, place of advertisement, query made, and the date the advertisement was added.

    :param advert_card: The advertisement card to be parsed, represented as a bs4 Tag object
    :type advert_card: bs4.Tag

    :returns: A dictionary containing information extracted from the advertisement card. The keys in the dictionary
    are:
    - "title": The title of the advertisement (str)
    - "url": The URL of the advertisement (str)
    - "price": The price mentioned in the advertisement, if available, otherwise 0 (int)
    - "place": The place where the advertisement was posted (str)
    - "query": A placeholder for the query that retrieved this advertisement, to be filled
    in later stages (None initially)
    - "date_added": The date when the advertisement was added, parsed into a datetime object (datetime)

    :rtype: dict
    """

    advert_info = {
        "title": None,
        "url": None,
        "price": None,
        "place": None,
        "query": None,
        "date_added": None,

    }

    href = advert_card.find("a", class_="css-rc5s2u").get("href")

    top_block = advert_card.find(
        "div",
        attrs={
            "class": re.compile("css-u2ayx9")
        }
    )

    bottom_block = advert_card.find(
        "div",
        class_="css-odp1qd"
    )

    for tag in top_block:
        if tag.name == "h6":
            advert_info["title"] = tag.text.strip()
            continue

        if tag.name == "p":
            try:
                parsed_price = re.match(REGEX_PATTERN, tag.text.strip()).group(1)
            except AttributeError:
                print(f"Incorrect or absence of price field for advertisement!\nFor title: {advert_info['title']} ")

                advert_info["price"] = 0
                continue

            parsed_price = parsed_price.replace(" ", "")
            advert_info["price"] = int(parsed_price)
            continue

    advert_geo_info = bottom_block.p.text.split("-")
    place, pub_date = advert_geo_info[:-1], advert_geo_info[-1]

    advert_info["place"] = " ".join(place).strip()
    advert_info["date_added"] = parse(pub_date)
    advert_info["url"] = "https://" + MAIN_URL + href

    return advert_info


def parse_full_request(
        netloc: str,
        query: str,
        limit: int = 1,
        price_from: float = .0,
        price_to: float = .0
) -> List[dict]:
    """
    Retrieves a list of advertisements from OLX based on the specified query and filters.
    It paginates through the results up to the defined limit, extracting data from each advertisement encountered.

    :param netloc: The network location (hostname) of the OLX site to query.
    :type netloc: str

    :param query: The search query string to be used in searching for advertisements on OLX.
    :type query: str

    :param limit: The maximum number of pages to retrieve and parse. Defaults to 1.
    :type limit: int

    :param price_from: The minimum price filter for the advertisements. Defaults to 0.0.
    :type price_from: float

    :param price_to: The maximum price filter for the advertisements. Defaults to 0.0.
    :type price_to: float

    :returns: A list of dictionaries, where each dictionary contains information about
    a single advertisement retrieved from the OLX site, including details such as the title,
    URL, price, location, query, and date added.
    :rtype: list[dict]
    """
    advertisements = []

    scheme = 'https'
    path = "q-" + query
    query_params = {
        'search[filter_float_price:from]': price_from,
        'search[filter_float_price:to]': price_to
    }

    query_string = urlencode(query_params)
    next_page = urlunparse((scheme, netloc, path, '', query_string, ''))

    count = 0
    find_category = True
    global_tag = ''

    while next_page and limit > count:
        try:
            all_ads, next_page = parse_one_page(
                url=next_page,
                find_category=find_category
            )
        except AttributeError:
            print("Max page retrieved!")
            break

        if isinstance(next_page, tuple):
            tag, next_page = next_page
            global_tag = tag
            next_page = f"{scheme}://" + MAIN_URL + next_page
        else:
            next_page = f"{scheme}://" + MAIN_URL + next_page

        if all_ads:
            for advert in all_ads:
                advert_data = parse_advertisement(advert)
                advert_data["query"] = query
                advert_data["tag"] = global_tag
                advertisements.append(advert_data)

        count += 1

        if count >= 1:
            find_category = False

    return advertisements
