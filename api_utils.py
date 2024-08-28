"""
Description: Functions to help with connecting to the API
Date Created: 2024-08-27
Date Modified: 2024-08-27
Author: SPolton
Modified by: SPolton
"""


import os
import requests

from dotenv import load_dotenv
from urllib.parse import urlencode
from models import CONDITION

load_dotenv()
HOST = os.getenv('HOST', "127.0.0.1")
PORT = int(os.getenv('PORT', 8000))

API_URL_BASE = f"http://{HOST}:{PORT}"
API_URL_CRAWL = API_URL_BASE + "/crawl_facebook_marketplace"


def format_crawl_params(city, category, query=None, sort=None, min_price=None,
                     max_price=None, condition_values=None):
    """
    Returns the unencoded params needed for api crawl, based on user query.
    """
    terms = []
    if query:
        terms.append(f"query={query}")
    if sort:
        terms.append(f"sortBy={sort}")
    if min_price and min_price > 0:
        terms.append(f"minPrice={min_price}")
    if max_price:
        terms.append(f"maxPrice={max_price}")

    if condition_values:
        conditions = []
        for i, is_selected in enumerate(condition_values):
            if is_selected:
                cond = CONDITION[i].replace(" ", "_").lower() # For URL
                conditions.append(cond)

        if len(conditions) > 0:
            cond = ",".join(conditions)
            terms.append(f"itemCondition={cond}")

    params = {
        "city": city,
        "category": category,
        "query": "&".join(terms)
    }
    return params


def get_crawl_results(params):
    """
    Attempts to conncet to the API and return the results.
    Throws: RuntimeError
    """
    encoded_params = urlencode(params)
    url = f"{API_URL_CRAWL}?{encoded_params}"

    try:
        print(f"\nRequest URL: {url}\n")
        res = requests.get(url, timeout=60)
        res.raise_for_status()  # Throw exception if response not OK
        return res.json()

    except requests.exceptions.HTTPError as e:
        detail = None
        try:
            detail = res.json().get("detail")
        except ValueError:  # JSON decode error
            detail = "No additional details available."
        raise RuntimeError(f"An error occured within the backend API." \
                           f"\n\n{e}\n\nDetails: {detail}")
    except requests.exceptions.ConnectionError as e:
        raise RuntimeError(f"Could not establish a connection to the API." \
                           f"The sever might be down.\n\n{e}")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"There was a problem with the request.\n\n{e}")