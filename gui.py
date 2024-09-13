"""
Description: This file hosts the web GUI for the Facebook Marketplace Scraper.
Date Created: 2024-01-24
Date Modified: 2024-09-11
Author: Harminder Nijjar (v1.0.0)
Modified by: SPolton
Version: 1.5.7
Usage: streamlit run gui.py
"""

import streamlit as st
import time, logging
from sys import stdout

from api_utils import *
from notify import send_ntfy

from cities import CITIES
from models import CATEGORIES, SORT, CONDITION


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

st_logger = logging.getLogger("gui")
st_logger.setLevel(logging.INFO)


# Keep state across re-execution.
state = st.session_state
if "results" not in state:
    st_logger.debug("Init state.")
    state.results = []
    state.params = None
    state.scheduled = False
    state.frequency = 300  # 5 Minutes
    state.duration = 0
    state.cancel_pressed = False
else:
    if state.scheduled and state.duration > 0:
        # Clear countdown_timer from terminal
        stdout.write(f"\rCanceled.{" "*30}\r")
    st_logger.debug("Rerun: State is already defined.")


def start_schedule(frequency=None):
    """Set state 'scheduled' to True and 'duration' to frequency input."""
    if not frequency:
        frequency = state.frequency
    if not state.scheduled:
        st_logger.debug("Creating cancel button for schedule.")
        state.cancel_pressed = cancel.button("Cancel Schedule")
    state.scheduled = True
    state.frequency = frequency
    state.duration = frequency
    st_logger.info(f"Schedule set for duration {state.duration}")

def stop_schedule():
    """Set state 'scheduled' to False, 'duration' to 0, and clear cancel button."""
    state.scheduled = False
    state.duration = 0
    cancel.empty()
    st_logger.debug("Schedule Stopped.")

def countdown_timer(countdown_message):
    """
    Sets state.duration equal to state.frequency and clears
    the countdown message, then enters a loop that decrements
    state.duration to 0 and updates the countdown message.
    Returns when state 'duration' reaches 0.
    \nFunction copied and modified from:
    https://github.com/wftanya/facebook-marketplace-scraper/commits/main/gui.py
    """
    st_logger.debug("Starting countdown timer:")
    countdown_message.empty()
    while state.duration > 0:
        mins, secs = divmod(state.duration, 60)
        timeformat = '{:02d}:{:02d}'.format(mins, secs)
        time_message = f"Time until next auto scrape: {timeformat}"
        countdown_message.text(time_message)
        stdout.write(f"\r{time_message}")
        stdout.flush()
        time.sleep(1)
        state.duration -= 1
    stdout.write(f"\rComplete!{" "*len(time_message)}\n")


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
    st_logger.info(f"Recieved {len(results)} results.")
    return results

def notify_new(results, ntfy_topic, notify_limit=None):
    """
    Send a ntfy notification per result containing 'is_new' = True.
    """
    order_to_priority = {1:5, 2:4, 3:4, 4:3, 5:3}
    new_count = 0
    for i, item in enumerate(results):
        if item.get("is_new"):
            new_count += 1

            # Limit notifications
            if notify_limit is None or new_count <= notify_limit:
                order = item.get("order", i + 1)
                priority = order_to_priority.get(order, 2)

                # Attempt to filter some listings that appear as "new"
                # because of it replacing the spot of sold listings.
                if priority > 2 or order < len(results)/2:
                    title = f"New Listing: {item.get("price")}"
                    message = f"{item.get("title")}, {item.get("url")}"
                    send_ntfy(ntfy_topic, message, title, priority, link=item.get("url"), img=item.get("image"))

    if notify_limit and new_count > notify_limit:
        title = "Additional New Listings"
        message = f"View {new_count-notify_limit} more in streamlit."
        send_ntfy(ntfy_topic, message, title, priority=2, tags="chart_with_upwards_trend")
    
    st_logger.info(f"Found {new_count} new results.")
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
            st.error(f"Error displaying listing {i+1}: {e}")
        finally:
            if i+1 < len(results):
                st.write("----")
    
    mes_parts = []
    if len(results) > 0:
        mes_parts.append(f"Total results: {len(results)}")
    if new_count > 0:
        mes_parts.append(f"New results: {new_count}")
    if mes_parts:
        mes_info = ", ".join(mes_parts)
        message.info(mes_info)
        st_logger.info(f"Display: {mes_info}")

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
    show_new = st.checkbox("Track New Listings", value=True)
    ntfy_topic = None
    if show_new:
        ntfy_topic = st.text_input("ntfy Topic", value="new_fb_listing_test", disabled=not show_new).strip()
with col[1]:
    set_schedule = st.checkbox("Schedule")
    if set_schedule:
        frequency = st.number_input("Frequency in seconds", min_value=5, format="%d", value=60, disabled=not set_schedule)

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
    st_logger.info("Submit pressed.")
    # Get params and encode the url for api
    state.params = format_crawl_params(city, category, query, sort,
                                min_price, max_price, condition_values)
    state.results = find_results(state.params, message, show_new)
    notify_new(state.results, ntfy_topic, 2)
    
    if set_schedule:
        start_schedule(frequency)
    else:
        stop_schedule()

elif state.cancel_pressed:
    st_logger.info("Cancel Pressed.")
    stop_schedule()

results_container = st.expander("Results", True)
with results_container:
    display_results(state.results, message)

# Scheduled task
while state.scheduled:
    countdown_timer(countdown_message) # Wait for timer to finish.
    
    countdown_message.text("Scraping...")
    results = find_results(state.params, message, show_new)
    new_count = notify_new(results, ntfy_topic, 4)

    start_schedule()
    if len(results) > 0 and new_count > 0:
        # Rerun to keep results display updated.
        state.results = results
        st.rerun()