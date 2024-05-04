"""
Description: This file contains the code for Passivebot's Facebook Marketplace Scraper API.
Date: 2024-01-24
Author: Harminder Nijjar
Version: 1.0.0.
Usage: python app.py
"""

import os
import time
import uvicorn

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup, element
from fastapi import HTTPException, FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from models import CITIES, FBClassBullshit, MARKETPLACE_URL, INITIAL_URL

# Create an instance of the FastAPI class.
app = FastAPI()
# Configure CORS
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/")
def root() -> Response:
    """Homepage"""
    return Response(
        "Welcome to Passivebot's Facebook Marketplace API. "
        "Documentation is currently being worked on along with the API. "
        "Some planned features currently in the pipeline are a "
        "ReactJS frontend, MongoDB database, and Google Authentication."
    )


@app.get("/crawl_facebook_marketplace")
def crawl_facebook_marketplace(city: str, query: str, max_price: int) -> JSONResponse:
    """Get fb marketplace listing information"""

    # If the city is not in the cities dictionary...
    if city not in CITIES:
        city = city.capitalize()
        # Raise an HTTPException.
        raise HTTPException(
            404,
            f"{city} is not a city we are currently supporting on the Facebook Marketplace. \
                Please reach out to us to add this city in our directory.",
        )
    inputs = (city, query, max_price)
    # Define the URL to scrape.
    marketplace_url = MARKETPLACE_URL.format(*inputs)
    # Get listings of particular item in a particular city for a particular price.
    # Initialize the session using Playwright.
    with sync_playwright() as p:
        # Open a new browser page.
        browser = p.firefox.launch(headless=False)
        page = browser.new_page()
        # Navigate to the URL.
        page.goto(INITIAL_URL)
        # Wait for the page to load.
        time.sleep(2)

        if user := page.wait_for_selector('input[name="email"]'):
            user.fill(os.environ["FB_USER"])
        if pw := page.wait_for_selector('input[name="pass"]'):
            pw.fill(os.environ["FB_PW"])

        time.sleep(2)
        if login := page.wait_for_selector('button[name="login"]'):
            login.click()

        time.sleep(2)
        page.goto(marketplace_url)

        # Wait for the page to load.
        time.sleep(2)
        for _ in range(10):
            page.keyboard.press("End")
            time.sleep(2)
        html = page.content()
        soup = BeautifulSoup(html, "html.parser")
        parsed = []
        listings: list[element.Tag] = soup.find_all(
            "div", class_=FBClassBullshit.LISTINGS.value
        )
        for i, listing in enumerate(listings):
            result: dict[str, str | list[str] | None] = {
                "image": None,
                "title": None,
                "price": None,
                "post_url": None,
                "location": None,
            }
            # Text Elements
            for item in (
                FBClassBullshit.TITLE,
                FBClassBullshit.LOCATION,
                FBClassBullshit.PRICE,
            ):
                if html_text := listing.find("span", item.value):
                    result[item.name.lower()] = html_text.text

            # Get the item image.
            if image := listing.find("img", class_=FBClassBullshit.IMAGE.value):
                if isinstance(image, element.Tag):
                    result["image"] = image.get("src")

            # Get the item URL.
            if post_url := listing.find("a", class_=FBClassBullshit.URL.value):
                if isinstance(post_url, element.Tag):
                    result["post_url"] = post_url.get("href")

            # Append the parsed data to the list.
            if any(result.values()):
                parsed.append(result)
            else:
                print(f"Couldn't parse listing number {i}")
                with open("docs/failed_listing.html", "a", encoding="utf-8") as file:
                    if listing.string:
                        file.write(listing.string)
                        file.write("\n------------------\n")
        # Close the browser.
        browser.close()
        return JSONResponse(parsed)


@app.get("/return_ip_information")
def return_ip_information() -> JSONResponse:
    """Does exactly what you'd think it'd do"""
    response = {
        "ip_address": "",
        "country": "",
        "location": "",
        "isp": "",
        "hostname": "",
        "type": "",
        "version": "",
    }
    # Initialize the session using Playwright.
    with sync_playwright() as p:
        # Open a new browser page.
        browser = p.chromium.launch()
        page = browser.new_page()
        # Navigate to the URL.
        page.goto("https://www.ipburger.com/")
        # Wait for the page to load.
        time.sleep(5)
        # Get the HTML content of the page.
        html = page.content()
        # Beautify the HTML content.
        soup = BeautifulSoup(html, "html.parser")
        # Find the IP address.
        if ip_address := soup.find("span", id="ipaddress1"):
            response["ip_address"] = ip_address.text
        # Find the country.
        if country := soup.find("strong", id="country_fullname"):
            response["ip_address"] = country.text
        # Find the location.
        if location := soup.find("strong", id="location"):
            response["ip_address"] = location.text
        # Find the ISP.
        if isp := soup.find("strong", id="isp"):
            response["ip_address"] = isp.text
        # Find the Hostname.
        if hostname := soup.find("strong", id="hostname"):
            response["ip_address"] = hostname.text
        # Find the Type.
        if ip_type := soup.find("strong", id="ip_type"):
            response["ip_address"] = ip_type.text
        # Find the version.
        if version := soup.find("strong", id="version"):
            response["ip_address"] = version.text
        # Close the browser.
        browser.close()
        # Return the IP information as JSON.
        return JSONResponse(response)


if __name__ == "__main__":
    # Run the app.
    uvicorn.run(
        # Specify the app as the FastAPI app.
        "app:app",
        host="127.0.0.1",
        port=8000,
    )
