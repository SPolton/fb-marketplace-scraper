"""
Description: This file contains the code for Passivebot's Facebook Marketplace Scraper API.
Date Created: 2024-01-24
Date Modified: 2024-08-25
Author: Harminder Nijjar
Modified by: SPolton
Version: 1.3.1
Usage: python app.py
"""


import os       # Used to get the environment variables.
import time     # Used to add a delay to the script.
import uvicorn  # Used to run the API.
import logging  # For terminal info and debugging

from bs4 import BeautifulSoup, element          # Used to parse the HTML.
from dotenv import load_dotenv                  # Used to load username and password securely
from playwright.sync_api import sync_playwright # Used to crawl the Facebook Marketplace.
from playwright._impl._errors import TimeoutError

from fastapi import FastAPI, Response, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from models import FBClassBullshit, MARKETPLACE_URL

# Retrieve sensitive data from environment variables
load_dotenv()
FB_USER = os.getenv('FB_USER')
FB_PASSWORD = os.getenv('FB_PASSWORD')
HOST = os.getenv('HOST', "127.0.0.1")
PORT = int(os.getenv("PORT", 8000))

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


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

# Route to the root endpoint.
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
def crawl_facebook_marketplace(city: str, category: str, query: str) -> JSONResponse:
    """
    Attempts to scrape Facebook Marketplace for listing information.
    Returns: A JSON Response containing a list of dictionaries.
    """
    # logger.debug(f"Params: {city}, {category}, {query}")
    
    # Define the URL to scrape.
    inputs = (city, category, query)
    marketplace_url = MARKETPLACE_URL.format(*inputs)
    logger.info(f"Marketplace URL: {marketplace_url}")

    # Testing gui, remove later
    if category=="test":
        time.sleep(1)
        return JSONResponse([{
            "image": None,
            "title": "Test",
            "price": "$100",
            "post_url": None,
            "location": city,
        }])

    # Get listings based on the results from the url query.
    try:
        # Initialize the session using Playwright.
        with sync_playwright() as p:
            # Open a new browser page.
            logger.debug("Opening browser")
            browser = p.firefox.launch(headless=False)
            page = browser.new_page()

            logger.debug(f"Opening {marketplace_url}")
            page.goto(marketplace_url)

            # Attempt login if prompted
            logged_in = None
            login_attempts = 0
            while login_attempts < 3 and page.locator("div#loginform").is_visible():
                login_attempts += 1
                logged_in = False
                logged_in = attempt_login(page)
                logger.debug(f"login status: {logged_in}")
                page.wait_for_load_state("networkidle")
            
            if not logged_in and login_attempts >= 3:
                logger.error("Could not login after 3 attempts.")
                raise HTTPException(401, "Failed to login to Facebook")
            
            logger.info("Finished login step.")

            if not logged_in:
                # close potential login popup
                page.wait_for_load_state("networkidle")
                close_button = page.query_selector('div[aria-label="Close"][role="button"]')
                if close_button.is_visible():
                    close_button.click()
                    logger.debug("Closed Login Popup.")
            
            # TODO: Other popups are preventing scrolling.
            # i.e. "Allow facebook.com to send notifications" popup

            # Scroll down page to load more listings
            for _ in range(10):
                page.keyboard.press("End")
                logger.debug("Scroll...")
                page.wait_for_load_state()

            page.wait_for_load_state("networkidle")
            html = page.content()
            soup = BeautifulSoup(html, "html.parser")

            # Parse the listings
            listings: list[element.Tag] = soup.find_all(
                "div", class_=FBClassBullshit.LISTINGS.value
            )
            parsed_json = parse_listings(listings)

            logger.debug("Closing browser and returning JSON\n")
            browser.close()
            return JSONResponse(parsed_json)
        
    except Exception as e:
        logger.critical("Fatal crash when parsing browser page\n", exc_info=True)
        raise HTTPException(500, f"Unexpected crash during parsing. {e}")


def attempt_login(page):
    """
    Attempts to enter login info into the form. Assumes that the form exists,
    else, will timeout in 2 seconds.
    Returns: True if the login actions happened sucessfully, False otherwise.
    """
    logger.info("Attempting to login...")
    try:
        page.locator("div#loginform").wait_for(timeout=2000, state="visible")
        # Playwright auto-waits before doing actions.
        page.locator('input[name="email"]').fill(FB_USER)
        page.locator('input[name="pass"]').fill(FB_PASSWORD)
        page.locator('button[name="login"]').click()
        return True
    
    except TimeoutError as timeout:
        logger.warning(f"Timeout on login attempt. {timeout}")
    return False


def parse_listings(listings):
    """
    Parses a list of HTML listings and extracts relevant information.
    Returns: A list of dictionaries, each containing the listing data.
    """
    logger.info("Parsing listings...")
    parsed = []
    for i, listing in enumerate(listings):
        result: dict[str, str | list[str] | None] = {
            "image": None,
            "title": None,
            "price": None,
            "post_url": None,
            "location": None,
        }
        # Get the text Elements
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
                url_part = post_url.get("href")
                url_clean = url_part.split("/?")[0]
                result["post_url"] = f"https://www.facebook.com{url_clean}/"

        # Append the parsed data to the list.
        if any(result.values()):
            logger.debug(f"Found listing {i}: {result['title']}")
            parsed.append(result)
        else:
            logger.warning(f"Couldn't parse listing number {i}")
            with open("docs/failed_listing.html", "a", encoding="utf-8") as file:
                if listing.string:
                    logger.debug(f"Listing text: {listing.string}")
                    file.write(listing.string)
                    file.write("\n------------------\n")
                else:
                    logger.debug(f"Listing {i} has no text")

    logger.info(f'Parsed {len(parsed)} listings.')
    return parsed


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
        browser = p.firefox.launch()
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
        host = HOST,
        port = PORT,
        log_level = "debug"
    )
