"""
Description: This file hosts the web GUI for the Facebook Marketplace Scraper.
Date Created: 2024-01-24
Date Modified: 2024-09-10
Author: Harminder Nijjar (v1.0.0)
Modified by: SPolton
Version: 1.5.4
Usage: steamlit run gui.py
"""

import streamlit as st
import time

from api_utils import *
from notify import send_ntfy

from cities import CITIES
from models import CATEGORIES, SORT, CONDITION


# Keep state across re-execution.
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

def countdown_timer(countdown_message):
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


def find_results(params, message=st.empty(), show_new=False):
    """Call API for listings and return the results."""
    results = []
    if params:
        message.info("Attempting to find listings...")
        
        try:
            if show_new:
                results = get_crawl_results(params, API_URL_CRAWL_NEW)
            else:
                results = get_crawl_results(params, API_URL_CRAWL)
            message.info(f"Number of results: {len(results)}")

        except RuntimeError as e:
            message.error(str(e))
    return results

def notify_new(results, ntfy_topic, notify_limit=None):
    """Send a notification per result containing 'is_new' = True."""
    new_count = 0
    for i, item in enumerate(results):
        if item.get("is_new"):
            new_count += 1
            if notify_limit is not None and new_count > notify_limit:
                break
            title = f"New Listing: {item.get("price")}"
            message = f"{item.get("title")}"
            send_ntfy(ntfy_topic, message, title, link=item.get("url"), img=item.get("image"))
    return new_count

def display_results(results, message=st.empty()):
    """List all the results and update info message with total."""
    new_count = 0
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
                    new_count += 1
                    st.header("New!")
                st.write(item.get("price"))
                st.write(item.get("location"))
                st.write(item.get("url"))
                if timestamp := item.get("timestamp"):
                    st.write(f"Found at: {timestamp}")

        except Exception as e:
            st.error(f"Error displaying listing {i}: {e}")
        finally:
            st.write("----")
    
    mes_parts = []
    if len(results) > 0:
        mes_parts.append(f"Total results: {len(results)}")
    if new_count > 0:
        mes_parts.append(f"New results: {new_count}")
    if mes_parts:
        mes_info = ", ".join(mes_parts)
        message.info(mes_info)

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

col = st.columns(2)
with col[0]:
    show_new = st.checkbox("Lable New Listings", value=True)
    ntfy_topic = None
    if show_new:
        ntfy_topic = st.text_input("ntfy Topic", value="new_fb_listing", disabled=not show_new).strip()
with col[1]:
    set_schedule = st.checkbox("Schedule")
    if set_schedule:
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
    stop_schedule()
    # Get params and encode the url for api
    state.params = format_crawl_params(city, category, query, sort,
                                min_price, max_price, condition_values)
    state.results = find_results(state.params, message, show_new)
    notify_new(state.results, ntfy_topic, 3)
    if set_schedule and not state.scheduled:
        start_schedule(state.frequency)

elif state.cancel_pressed:
    stop_schedule()

results_container = st.container()
with results_container:
    results_container.empty()
    display_results(state.results, message)

# Scheduled task
while state.scheduled:
    do_task = countdown_timer(countdown_message)
    if do_task:
        state.results = find_results(state.params, message, show_new)
        new_count = notify_new(state.results, ntfy_topic)

        if new_count > 0:
            with results_container:
                results_container.empty()
                display_results(state.results, message)

    if state.scheduled:
        state.duration = state.frequency