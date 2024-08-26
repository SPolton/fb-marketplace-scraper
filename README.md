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
### Overview
This open-source program uses Python to scrape data from Facebook Marketplace. A Streamlit web GUI allows for various search parameters to be submitted to the backend API. The program uses Playwright to navigate the Facebook Marketplace website and BeautifulSoup to extract relevant data. It then sends and displays the results in the Streamlit web GUI.

### GUI Features:
- Enter search parameters and press the submission button to start scraping. 
- Displays: Titles, images, prices, locations, and item URLs.

Search parameters:
- City: Select from a list of supported cities.
- Category: Select one of the marketplace product categories, or generic search.
- Query: Enter key words to search for. Available when the "Search" category is selected.
- Sort By: Select how to sort the results.
- Price Range: Set the min and max price.
- Condition: Checkboxes for the item condition.

### API:
- IP information retrieval.
- Root: Displays a welcome message.
- Data scraping: Parameters include city, category, and query

### Customization
This program can be customized to your personal/organizational needs.
- Streamlit GUI
- Playwright
- BeautifulSoup
  
### Language: 
- [Python](https://www.python.org/)
  
### Flow diagrams:

### Requirements:
- Python 3.x
- Playwright
- Streamlit
- BeautifulSoup
  
### Modules:
- Playwright for web crawling
- BeautifulSoup for HTML parsing
- FastAPI for API creation
- JSON for data formatting
- Uvicorn for running the server
  
### Implementation
- Browser automation and data scraping using Playwright
- HTML content parsing with BeautifulSoup
- Data returned in JSON format
- Application server run using Uvicorn
