"""
Description: This file hosts the web GUI for the Facebook Marketplace Scraper.
Date Created: 2024-01-24
Date Modified: 2024-08-25
Author: Harminder Nijjar (v1.0.0)
Modified by: SPolton
Version: 1.3.4
Usage: steamlit run gui.py
"""

import streamlit as st

from api_utils import *

from cities import CITIES
from models import CATEGORIES, SORT, CONDITION


def display_results(results):
    # Show the number of listings
    if len(results) > 0:
        message.info(f"Number of results: {len(results)}")

    # Iterate over the session results to display each item.
    for i, item in enumerate(results):
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

# with st.expander("Schedule"):
#     col = st.columns(2)
#     with col[0]:
#         frequency = st.number_input("Frequency in minutes", min_value=1, format="%d", value=1)
#     with col[1]:
#         ntfy = st.text_input("ntfy topic")

submit = st.button("Submit", disabled=error_present)

message = st.empty()

# If the button is clicked.
if submit:
    state.results = []
    message.info("Attempting to find listings...")

    # Get params and encode the url for api
    params = format_crawl_params(city, category, query, sort,
                                 min_price, max_price, condition_values)
    
    try:
        state.results = get_crawl_results(params)
        message.info(f"Number of results: {len(state.results)}")
    except RuntimeError as e:
        message.error(str(e))


display_results(state.results)