"""
Description: Save results per search criteria using SQLalchemy and SQLite
Date Created: 2024-09-01
Date Modified: 2024-09-01
Author: SPolton
Modified By: SPolton
Version: dev
Credit: The initial implementation of database.py was assisted by ChatGPT 4o Mini
"""

from os import getenv
from dotenv import load_dotenv

from sqlalchemy import create_engine, inspect, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func

load_dotenv()
DATABASE_URL = getenv("DATABASE", "sqlite:///search_results.db")
engine = create_engine(DATABASE_URL, echo=True)
Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()

class SearchCriteria(Base):
    __tablename__ = "search_criteria"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    city = Column(String)
    category = Column(String)
    query = Column(String)
    search_timestamp = Column(DateTime, server_default=func.now())
    
    results = relationship("Listing", back_populates="search_criteria")

class Listing(Base):
    __tablename__ = "results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    search_id = Column(Integer, ForeignKey("search_criteria.id"))
    url = Column(Text, unique=True)
    title = Column(String)
    price = Column(String)
    location = Column(String)
    image = Column(Text)
    result_timestamp = Column(DateTime, server_default=func.now())
    
    search_criteria = relationship("SearchCriteria", back_populates="results")


def init_db():
    """Create tables in the database if they don't exist."""
    Base.metadata.create_all(engine)
    inspector = inspect(engine)
        
    # Check if tables are available
    if "search_criteria" not in inspector.get_table_names():
        raise RuntimeError("Table 'search_criteria' is not available.")
    if "results" not in inspector.get_table_names():
        raise RuntimeError("Table 'results' is not available.")

def get_or_insert_search_criteria(city, category, query):
    """Retrieve existing search criteria or create new if not found."""
    search_criteria = session.query(SearchCriteria).filter_by(
        city=city,
        category=category,
        query=query
    ).first()
    
    if search_criteria is None:
        search_criteria = SearchCriteria(
            city=city,
            category=category,
            query=query
        )
        session.add(search_criteria)
        session.commit()
    
    return search_criteria.id

def insert_results(search_id, results):
    """Insert new results into the database."""
    existing_urls = {url for url, in session.query(Listing.url).filter_by(search_id=search_id).all()}
    new_listings = []
    for listing in results:
        url = listing.get("url")
        if url not in existing_urls:
            new_result = Listing(
                search_id=search_id,
                url=url,
                title=listing.get("title"),
                price=listing.get("price"),
                location=listing.get("location"),
                image=listing.get("image")
            )
            new_listings.append(new_result)
            existing_urls.add(url)
    
    if new_listings:
        session.add_all(new_listings)
        session.commit()

def remove_stale_results(search_id, results):
    """Remove listings that are no longer present in the latest results."""
    latest_urls = {listing.get("url") for listing in results}
    stale_results = session.query(Listing).filter_by(search_id=search_id).filter(~Listing.url.in_(latest_urls)).all()
    for result in stale_results:
        session.delete(result)
    session.commit()

def get_results(search_id):
    """Retrieve existing results for a given search_id."""
    results = session.query(Listing).filter_by(search_id=search_id).all()
    return results

def get_new_results(search_id, results):
    """Identify and return new results not present in the database for a given search_id."""
    existing_results = get_results(search_id)
    
    new_results = [
        listing for listing in results
        if listing not in existing_results
    ]
    
    return new_results
