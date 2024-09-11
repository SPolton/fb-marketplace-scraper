# facebook-marketplace-scraper

<p align="center">
  <img src="static/preview.jpg">
</p>

<h3 align="center">
  An open-source Python program to scrape Facebook Marketplace using Playwright, BeautifulSoup, and FastAPI with a Streamlit GUI.
<h3 align="center">

```diff
Use the software provided at your own risk. I cannot be held responsible for any potential consequences, including potential bans from Meta.
```

Overview
========

This open-source program uses Python to scrape data from Facebook Marketplace. A Streamlit web GUI allows for various search parameters to be submitted to the backend API. The program uses Playwright to navigate the Facebook Marketplace website and BeautifulSoup to extract relevant data. It then sends and displays the results in the Streamlit web GUI.

GUI Features:
--------

- Enter search parameters and press the submission button to start scraping. 
- Display Per Listing: Title, image, price, location, item URL, and New.
- Set scheduled auto scrape, see time until auto scrape, and cancel schedule.

Search parameters:
- City: Select from a list of supported cities.
- Category: Select one of the marketplace product categories, or generic search.
- Query: Enter key words to search for. Available when the "Search" category is selected.
- Sort By: Select how to sort the results.
- Price Range: Set the min and max price.
- Condition: Checkboxes for the item condition.

Search settings:
- Track new Listings: Checkbox for API to track new results using a database.
- ntfy Topic: Send push notifications to this nfty topic.
- Schedule: Checkbox to set auto scrape every set time.
- Frequency: The time (in seconds) before each auto scrape.

API:
--------

- IP information retrieval.
- Root: Displays a welcome message.
- Data scraping: Parameters include city, category, and query

### Customization

This program can be customized to your personal/organizational needs.
- Streamlit GUI
- Playwright
- BeautifulSoup
- SQLAlchemy
  
### Language:

- [Python](https://www.python.org/)

### Requirements:

See requirements.txt
- Python 3.x
- Playwright
- Streamlit
- BeautifulSoup
- SQLAlchemy
  
### Modules:

app.py:
- FastAPI for API creation
- Playwright for web crawling
- BeautifulSoup for HTML parsing
- JSON for data formatting
- Uvicorn for running the server

Database.py:
- SQLite database for tracking listings.
- SQLAlchemy for managing the SQLite database.
  
### Implementation

- Browser automation and data scraping using Playwright
- HTML content parsing with BeautifulSoup
- Data returned in JSON format
- Application server run using Uvicorn


Database Schema:
--------

- Tables: search_criteria, results
- The database is primarily used by the API for tracking new listings.

##### search_criteria:

- Description: Stores criteria used for searching.

- Columns:
  - id (Integer, Primary Key)
  - city (String)
  - category (String)
  - query (String)
  - timestamp (DateTime): The Datetime when created (default is current time).

- Relationships:
    results (One-to-Many): Relationship to Listing table. A single search criteria can be associated with multiple listings.

##### results:

- Description: Stores individual search results associated with specific search criteria.

- Columns:
  - id (Integer, Primary Key)
  - search_id (Integer, Foreign Key): Foreign key referencing search_criteria.id.
  - order (Integer): Order of the listing within the search results.
  - url (Text): URL of the listing.
  - title (String)
  - price (String)
  - location (String)
  - image (Text): URL to the image of the listing.
  - is_new (Boolean, Default=True): Track whether the listing is new.
  - timestamp (DateTime): The timestamp when the listing was added (default is current time).

- Constraints:
  - Unique constraint on search_id and url to ensure that the same URL does not appear more than once for a given search criteria.

  Relationships:
  - search_criteria (Many-to-One): Relationship to SearchCriteria table. Each listing is associated with one search criteria.
