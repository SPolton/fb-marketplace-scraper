"""
Description: This file contains the GUI code for Passivebot's Facebook Marketplace Scraper.
Date Created: 2024-01-24
Date Modified: 2024-08-18
Author: Harminder Nijjar
Modified by: SPolton
Version: 1.1.0
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

API_BASE_URL = f"http://{HOST}:{PORT}/crawl_facebook_marketplace"

# Create a title for the web app.
st.title("Facebook Marketplace Scraper")

# Take user input for the city, category, and various queries.
city_id = st.selectbox("City", CITIES.keys(), 0)
city = CITIES[city_id]

category_id = st.selectbox("Category", CATEGORIES, 0)
category = category_id.replace(" ","").lower()

query = st.text_input("Query", "iPhone")

sort_id = st.selectbox("Sort By", SORT.keys(), 2)
sort = SORT[sort_id]

max_price = st.number_input("Max Price", min_value=0, format="%d", value=1000)

# Create columns for checkboxes and display
# columns = st.columns(len(CONDITION))
# checkbox_values = []
# for i, condition in enumerate(CONDITION):
#     with columns[i]:
#         checkbox_values.append(st.checkbox(condition))

# Create a button to submit the form.
submit = st.button("Submit")

# If the button is clicked.
if submit:
    params = {
        "city": city,
        "category": category,
        "query": f"query={query}&sortBy={sort}&maxPrice={max_price}"
    }

    # Encode the parameters
    encoded_params = urlencode(params)
    url = f"{API_BASE_URL}?{encoded_params}"

    print(f"\nRequesting URL: {url}\n")
    st.info(f"Request URL: {url}")
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
