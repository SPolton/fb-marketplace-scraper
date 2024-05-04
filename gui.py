"""Cool GUI I didn't write :D"""

import streamlit as st
import requests

from models import CITIES

API_URL = "http://127.0.0.1:8000/crawl_facebook_marketplace" \
            "?city={0}&query={1}&max_price={2}"
# Create a title for the web app.
st.title("Passivebot's Facebook Marketplace Scraper")

# Take user input for the city, query, and max price.
city = st.selectbox("City", CITIES, 0)
query = st.text_input("Query", "Macbook Pro")
max_price = st.text_input("Max Price", "1000")
max_price = max_price.strip(",")
# Create a button to submit the form.
submit = st.button("Submit")

# If the button is clicked.
if submit:
    inputs = [city, query, max_price]
    url = API_URL.format(*inputs)
    res = requests.get(url, timeout=9999)

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
