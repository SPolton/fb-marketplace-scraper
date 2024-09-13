"""
Description: This file contains the code for Passivebot's Facebook Marketplace Scraper API.
Date Created: 2024-01-24
Date Modified: 2024-09-09
Author: Harminder Nijjar (v1.0.0)
Modified by: SPolton
Version: 1.5.1
Usage: python app.py
"""

import json, logging, os, time, uvicorn

from os import getenv
from dotenv import load_dotenv
from bs4 import BeautifulSoup, element

from fastapi import FastAPI, Response, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from playwright.sync_api import sync_playwright
from playwright._impl._errors import TimeoutError

from database import *
from models import FBClassBullshit, MARKETPLACE_URL

# Retrieve sensitive data from environment variables
load_dotenv()
FB_USER = getenv('FB_USER')
FB_PASSWORD = getenv('FB_PASSWORD')
HOST = getenv('HOST', "127.0.0.1")
PORT = int(getenv("PORT", 8000))

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


@app.get("/crawl_marketplace")
def crawl_marketplace(city: str, category: str, query: str) -> JSONResponse:
    """
    Attempts to scrape Facebook Marketplace for listing information.
    Returns: A JSON Response containing a list of dictionaries.
    Throws: HTTPException 500 on RuntimeError.
    """
    try:
        results = crawl_marketplace_logic(city, category, query)
        return JSONResponse(results)
    except AssertionError as e:
        raise HTTPException(401, str(e))
    except RuntimeError as e:
        raise HTTPException(500, str(e))
    except Exception as e:
        logger.critical("", exc_info=True)
        raise HTTPException(500, str(e))


@app.get("/crawl_marketplace/new_results")
def crawl_marketplace_new_results(city: str, category: str, query: str) -> JSONResponse:
    """
    Attempts to scrape Facebook Marketplace for new listings.
    Results are compared to the previous results.
    Returns: A JSON Response containing a list of new listings.
    Throws: HTTPException 500 on RuntimeError
    """
    try:
        logger.debug("Entering crawl_marketplace_new_listings")
        results = crawl_marketplace_logic(city, category, query)

        if len(results) > 0 and category != "test":
            search_id = get_or_insert_search_criteria(city, category, query)
            logger.info(f"Accessing database with search_id {search_id}")

            remove_stale_results(search_id, results)
            insert_new_results(search_id, results)
            new_results = get_new_results(search_id)
            db_results = get_results(search_id)
            set_all_not_new(search_id)

            logger.info(f"Found {len(new_results)} new listings.")
            return JSONResponse(db_results)
        return JSONResponse(results)
    
    except AssertionError as e:
        raise HTTPException(401, str(e))
    except RuntimeError as e:
        raise HTTPException(500, str(e))
    except Exception as e:
        logger.critical("", exc_info=True)
        raise HTTPException(500, str(e))


def crawl_marketplace_logic(city, category, query):
    """
    Returns a list of listings
    """
    # logger.debug(f"Params: {city}, {category}, {query}")
    
    # Define the URL to scrape.
    inputs = (city, category, query)
    marketplace_url = MARKETPLACE_URL.format(*inputs)
    logger.info(f"Marketplace URL: {marketplace_url}")

    # Testing gui, remove later
    if category=="test":
        time.sleep(1)
        return [{
            "image": "https://scontent.fyyc8-1.fna.fbcdn.net/v/t45.5328-4/459002811_1615008492394078_3238608714812733174_n.jpg?stp=c0.43.261.261a_dst-jpg_p261x260&_nc_cat=111&ccb=1-7&_nc_sid=247b10&_nc_ohc=xmu2EIsIktQQ7kNvgF31Fam&_nc_ht=scontent.fyyc8-1.fna&_nc_gid=AzQb3MuKJAjgBnhI531M_H-&oh=00_AYA6PGkYXBpPw7PuF3-d_n4gp0LV7fw7qrylUGSOW47keQ&oe=66E564BA",
            "title": "Apple iPad 7th Gen",
            "price": "CA$120",
            "url": "https://www.facebook.com/marketplace/item/1029513038667252/",
            "location": city,
            "is_new": True
        }]

    # Get listings based on the results from the url query.
    try:
        # Initialize the session using Playwright.
        with sync_playwright() as p:
            # Open a new browser page.
            logger.debug("Opening browser")
            browser = p.firefox.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            load_cookies(context)

            logger.debug(f"Opening {marketplace_url}")
            page.goto(marketplace_url)

            # Listen for dialog events and handle them
            def handle_dialog(dialog):
                logger.debug(f"Dialog detected with type: {dialog.type}")
                dialog.dismiss()  # or dialog.accept() based on the scenario

            page.on("dialog", handle_dialog)

            # Attempt login if prompted
            logged_in = True
            login_attempts = 0
            while login_attempts < 3 and page.locator("div#loginform").is_visible():
                login_attempts += 1
                logged_in = False
                logged_in = attempt_login(page)
                logger.debug(f"login status: {logged_in}")
                page.wait_for_load_state("networkidle")
            
            if not logged_in and login_attempts >= 3:
                logger.error("Could not login after 3 attempts.")
                raise AssertionError("Failed to login to Facebook")
            
            logger.info("Finished login step.")

            if not logged_in:
                try:
                    # close potential login popup
                    page.wait_for_load_state("networkidle")
                    close_button = page.query_selector('div[aria-label="Close"][role="button"]')
                    if close_button.is_visible():
                        close_button.click()
                        logger.debug("Closed Login Popup.")
                except AttributeError:
                    pass
            else:
                save_cookies(context)
            
            # TODO: Other popups are preventing scrolling.
            # i.e. "Allow facebook.com to send notifications" popup

            # Scroll down page to load more listings
            for _ in range(10):
                page.keyboard.press("End")
                logger.debug("Scroll...")
                page.wait_for_load_state()

            page.wait_for_load_state()
            html = page.content()
            soup = BeautifulSoup(html, "html.parser")

            # Parse the listings
            listings: list[element.Tag] = soup.find_all(
                "div", class_=FBClassBullshit.LISTINGS.value
            )
            parsed = parse_listings(listings)

            logger.debug("Closing browser and returning JSON\n")
            browser.close()
            return parsed
        
    except Exception as e:
        logger.critical("Fatal crash when parsing browser page\n", exc_info=True)
        raise RuntimeError(f"Unexpected crash during parsing. {e}")


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
    URL is required.
    Returns: A list of dictionaries, each containing the listing data.
    """
    logger.info("Parsing listings...")
    parsed = []
    for i, listing in enumerate(listings):
        result: dict[str, str | list[str] | None] = {
            "url": None,
            "title": None,
            "price": None,
            "location": None,
            "image": None,
            "is_new": False
        }
        # Get the item URL.
        if post_url := listing.find("a", class_=FBClassBullshit.URL.value):
            if isinstance(post_url, element.Tag):
                url_part = post_url.get("href")
                url_clean = url_part.split("/?")[0]
                result["url"] = f"https://www.facebook.com{url_clean}/"
        else:
            logger.warning(f"Listing {i} URL is None")

        if result["url"] is not None:
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

            # Append the parsed data to the list.
            if any(result.values()):
                logger.debug(f"Found listing {i}: {result['title']}")
                parsed.append(result)
            else:
                logger.warning(f"Couldn't parse listing number {i}")
                if listing.string:
                    logger.debug(f"Listing {i} text: {listing.string}")
                    with open("static/failed_listing.html", "a", encoding="utf-8") as file:
                        file.write(listing.string)
                        file.write("\n------------------\n")
                else:
                    logger.debug(f"Listing {i} has no text")

    logger.info(f'Parsed {len(parsed)} listings.')
    return parsed


def save_cookies(context, file="static/cookies.json"):
    cookies = context.cookies()
    with open(file, "w") as f:
        json.dump(cookies, f)
        logger.info("Saved cookies to file.")

def load_cookies(context, file="static/cookies.json"):
    if os.path.exists(file):
        with open(file, "r") as f:
            cookies = json.load(f)
            context.add_cookies(cookies)
            logger.info("Loaded saved cookies from file to context.")
    else:
        logger.info("Cookies file not found. Proceeding without loading cookies.")


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
    # Init database
    try:
        init_db()
    except Exception as e:
        logger.warning(f"Database Error\n{e}")
    print()
    
    # Run the app.
    uvicorn.run(
        # Specify the app as the FastAPI app.
        "app:app",
        host = HOST,
        port = PORT,
        log_level = "debug"
    )
