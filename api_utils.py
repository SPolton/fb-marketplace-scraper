"""
Description: Functions to help with connecting to the API
Date Created: 2024-08-27
Date Modified: 2024-09-11
Author: SPolton
Modified by: SPolton
Version: 1.4.1
"""

import requests, logging

from os import getenv
from dotenv import load_dotenv
from urllib.parse import urlencode
from models import CONDITION

load_dotenv()
HOST = getenv('HOST', "127.0.0.1")
PORT = int(getenv('PORT', 8000))

API_URL_BASE = f"http://{HOST}:{PORT}"
API_URL_CRAWL = API_URL_BASE + "/crawl_marketplace"
API_URL_CRAWL_NEW = API_URL_CRAWL + "/new_results"

logger = logging.getLogger(__name__)

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


def get_crawl_results(params, api_url=API_URL_CRAWL):
    """
    Attempts to conncet to the API and return the results.
    Throws: RuntimeError
    """
    encoded_params = urlencode(params)
    url = f"{api_url}?{encoded_params}"

    try:
        logger.info(f"Request URL:\n{url}\n")
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
                           f" The sever might be down.\n\n{e}")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"There was a problem with the request.\n\n{e}")