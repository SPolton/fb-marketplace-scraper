"""
Description: This file hosts the web GUI for the Facebook Marketplace Scraper.
Date Created: 2024-01-24
Date Modified: 2024-08-25
Author: Harminder Nijjar
Modified by: SPolton
Version: 1.3.3
Usage: steamlit run gui.py
"""

import os
import streamlit as st
import requests

from dotenv import load_dotenv
from urllib.parse import urlencode

from cities import CITIES
from models import CATEGORIES, SORT, CONDITION

load_dotenv()
HOST = os.getenv('HOST', "127.0.0.1")
PORT = int(os.getenv('PORT', 8000))

API_URL_BASE = f"http://{HOST}:{PORT}"
API_URL_CRAWL = API_URL_BASE + "/crawl_facebook_marketplace"


def api_crawl_params():
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


# Keep results in session until "submit" is pressed again.
state = st.session_state
if "results" not in state:
    state.results = []

# Create a title for the web app.
st.title("Facebook Marketplace Scraper")

# init to None to avoid undefined NameError
city = category = query = sort = min_price = max_price = None
error_present = False

# Take user input for the city, category, and various queries.
col = st.columns(2)
with col[0]:
    city_name = st.selectbox("City", CITIES.keys(), 0)
    city = CITIES[city_name]

with col[1]:
    category_id = st.selectbox("Category", CATEGORIES, 0)
    category = category_id.replace(" ","").lower() # For URL

# Only relevent for searches
if category == "search":
    query = st.text_input("Query", "iPhone")

sort_id = st.selectbox("Sort By", SORT.keys(), 3)
sort = SORT[sort_id]

col = st.columns(2)
with col[0]:
    # Price inputs in drawer
    with st.expander("Price"):
        p_col = st.columns(2)
        with p_col[0]:
            min_price = st.number_input("Min Price", min_value=0, format="%d", value=0)
        with p_col[1]:
            max_price = st.number_input("Max Price", min_value=0, format="%d", value=None)
        if max_price and max_price < min_price:
            error_present = True
            st.error("Max Price less than Min price.")

with col[1]:
    # Contition checkboxes in drawer
    condition_values = []
    with st.expander("Condition"):
        for i, condition in enumerate(CONDITION):
            condition_values.append(st.checkbox(condition))

# Button to submit the form.
submit = st.button("Submit", disabled=error_present)
message = st.empty()

# If the button is clicked.
if submit:
    message.info("Attempting to find listings...")

    # Encode the parameters
    encoded_params = urlencode(api_crawl_params())
    url = f"{API_URL_CRAWL}?{encoded_params}"

    try:
        print(f"\nRequest URL: {url}\n")
        res = requests.get(url, timeout=60)

        # Throw exception if response not OK
        res.raise_for_status()

        # Save results in session
        state.results = res.json()
        message.info(f"Number of results: {len(state.results)}")

    except requests.exceptions.HTTPError as e:
        message.error(f"An error occured within the backend API.\n\n{e}")
        # Separate incase of invalid json
        detail = res.json().get("detail")
        st.error(f"Details: {detail}")

    except requests.exceptions.ConnectionError as e:
        message.error(f"Could not establish a connection to the API. \
                        The sever might be down.\n\n{e}")
    except requests.exceptions.RequestException as e:
        message.error(f"There was a problem with the request.\n\n{e}")


# Show the number of listings
if len(state.results) > 0:
    message.info(f"Number of results: {len(state.results)}")

# Iterate over the session results to display each item.
for i, item in enumerate(state.results):
    try:
        st.header(item.get("title"))
        col = st.columns(2)
        with col[0]:
            if img_url := item.get("image"):
                st.image(img_url, width=200)
        with col[1]:
            st.write(item.get("price"))
            st.write(item.get("location"))
            if url := item.get('post_url'):
                st.write(url)

    except Exception as e:
        st.error(f"Error displaying listing {i}: {e}")
    finally:
        st.write("----")
