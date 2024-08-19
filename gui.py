"""
Description: This file contains the GUI code for Passivebot's Facebook Marketplace Scraper.
Date Created: 2024-01-24
Date Modified: 2024-08-19
Author: Harminder Nijjar
Modified by: SPolton
Version: 1.3.0
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
    """Returns the unencoded params needed for api crawl, based on user query"""
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
            cond = CONDITION[i].replace(" ", "_").lower()
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
    category = category_id.replace(" ","").lower()

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

# If the button is clicked.
if submit:
    # Encode the parameters
    encoded_params = urlencode(api_crawl_params())
    url = f"{API_URL_CRAWL}?{encoded_params}"

    print(f"\nAPI URL: {url}\n")
    res = requests.get(url, timeout=60)

    try:
        res.raise_for_status()
    except requests.exceptions.HTTPError as http_err:
        st.error(f"HTTP error occurred: {http_err}")
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred: {e}")

    # Convert the response from json into a Python list.
    results = res.json()

    # Display the length of the results list.
    st.write(f"Number of results: {len(results)}")

    # Iterate over the results list to display each item.
    for item in results:
        st.header(item.get("title"))
        if img_url := item.get("image"):
            st.image(img_url, width=200)
        st.write(item.get("price"))
        st.write(item.get("location"))
        if url := item.get('post_url'):
            st.write(f"https://www.facebook.com{url}")
        st.write("----")
