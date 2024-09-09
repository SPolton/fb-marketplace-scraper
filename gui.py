"""
Description: This file hosts the web GUI for the Facebook Marketplace Scraper.
Date Created: 2024-01-24
Date Modified: 2024-09-09
Author: Harminder Nijjar (v1.0.0)
Modified by: SPolton
Version: 1.5.1
Usage: steamlit run gui.py
"""

import streamlit as st
import time

from api_utils import *
from notify import send_ntfy

from cities import CITIES
from models import CATEGORIES, SORT, CONDITION


# Keep state until a button is pressed to change the state.
state = st.session_state
if "results" not in state:
    state.results = []
    state.params = None
    state.scheduled = False
    state.frequency = 60
    state.duration = 0
    state.cancel_pressed = False


def start_schedule(frequency):
    """Set state 'scheduled' to True and 'duration' to frequency input."""
    state.scheduled = True
    state.duration = frequency
    state.cancel_pressed = cancel.button("Cancel Schedule")

def stop_schedule():
    """Set state 'scheduled' to False and 'duration' to 0."""
    state.scheduled = False
    state.duration = 0
    cancel.empty()

def countdown_timer():
    """
    Enters a loop that decrements state 'duration' to 0 and updates the countdown message.
    Returns True when state 'duration' reaches 0 and 'scheduled' is True, returns False otherwise.
    Function copied and modified:
    https://github.com/wftanya/facebook-marketplace-scraper/commits/main/gui.py
    """
    countdown_message.empty()
    while state.duration > 0:
        mins, secs = divmod(state.duration, 60)
        timeformat = '{:02d}:{:02d}'.format(mins, secs)
        countdown_message.text(f"Time until next auto scrape: {timeformat}")
        time.sleep(1)
        state.duration -= 1
    if state.scheduled:
        countdown_message.text("Scraping...")
        return True
    else:
        countdown_message.empty()
        return False


def find_results(params):
    """Call API for listings and save results to state."""
    if params:
        state.results = []
        message.info("Attempting to find listings...")
        
        try:
            if new_only:
                state.results = get_crawl_results(params, API_URL_CRAWL_NEW)
            else:
                state.results = get_crawl_results(params, API_URL_CRAWL)
            message.info(f"Number of results: {len(state.results)}")

        except RuntimeError as e:
            message.error(str(e))

def display_results(results):
    """Show the results saved in state."""
    if len(results) > 0:
        message.info(f"Number of results: {len(results)}")

    # Iterate over the session results to display each item.
    for i, item in enumerate(results):
        try:
            st.header(item.get("title"))
            col = st.columns(2)
            with col[0]:
                if img_url := item.get("image"):
                    st.image(img_url)
            with col[1]:
                if item.get("is_new"):
                    st.header("New!")
                    mes = f"New listing: {item.get("price")}, {item.get("location")}\n'{item.get("title")}'\n{item.get("url")}"
                    send_ntfy("new_fb_listing", mes)
                st.write(item.get("price"))
                st.write(item.get("location"))
                st.write(item.get("url"))

        except Exception as e:
            st.error(f"Error displaying listing {i}: {e}")
        finally:
            st.write("----")


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

col = st.columns(3)
with col[0]:
    new_only = st.checkbox("New Listings Only")
with col[1]:
    set_schedule = st.checkbox("Schedule")
if set_schedule:
    with col[2]:
        state.frequency = st.number_input("Schedule Frequency (s)", min_value=5, format="%d", value=60, disabled=not set_schedule)

col = st.columns(4)
with col[0]:
    submit_pressed = st.button("Submit", disabled=error_present)
with col[1]:
    cancel = st.empty()
    if state.scheduled:
        state.cancel_pressed = cancel.button("Cancel Schedule")
    else:
        state.cancel_pressed = False

countdown_message = st.empty()
message = st.empty()

# If a button is clicked.
if submit_pressed:
    # Get params and encode the url for api
    state.params = format_crawl_params(city, category, query, sort,
                                min_price, max_price, condition_values)
    find_results(state.params)
    if set_schedule and not state.scheduled:
        start_schedule(state.frequency)
    elif not set_schedule:
        stop_schedule()
elif state.cancel_pressed:
    stop_schedule()

display_results(state.results)

# Scheduled task
while state.scheduled:
    do_task = countdown_timer()
    if do_task:
        #find_results(state.params)
        if state.scheduled:
            state.duration = state.frequency