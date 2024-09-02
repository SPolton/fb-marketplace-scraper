"""
Description: Save results per search criteria using SQLalchemy and SQLite
Date Created: 2024-09-01
Date Modified: 2024-09-01
Author: SPolton
Modified By: SPolton
Version: 1.4.1
Credit: The initial implementation of database.py was assisted by ChatGPT 4o Mini
"""

from os import getenv
from dotenv import load_dotenv

import sqlite3
from sqlalchemy import create_engine, inspect, Boolean, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func

load_dotenv()
DATABASE = getenv("DATABASE", "search_results.db")
DATABASE_URL = f"sqlite:///{DATABASE}"
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()

class SearchCriteria(Base):
    __tablename__ = "search_criteria"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    city = Column(String)
    category = Column(String)
    query = Column(String)
    timestamp = Column(DateTime, server_default=func.now())
    
    results = relationship("Listing", back_populates="search_criteria")

    def __repr__(self):
        return f"<SearchCriteria(id={self.id}, city={self.city}, category={self.category}, query={self.query})>"

class Listing(Base):
    __tablename__ = "results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    search_id = Column(Integer, ForeignKey("search_criteria.id"))
    url = Column(Text, unique=True)
    title = Column(String)
    price = Column(String)
    location = Column(String)
    image = Column(Text)
    # is_new = Column(Boolean, default=True)
    timestamp = Column(DateTime, server_default=func.now())
    
    search_criteria = relationship("SearchCriteria", back_populates="results")

    def __repr__(self):
        return (f"<Listing(id={self.id}, search_id={self.search_id}, price='{self.price}',\ttitle='{self.title}', location='{self.location}')>")


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


def print_database():
    print("\nsearch_criteria table:")
    search_criteria_rows = session.query(SearchCriteria).all()
    if search_criteria_rows:
        for entry in search_criteria_rows:
            print(entry)
    else:
        print("No entries found in 'search_criteria' table.")
    
    print("\nresults table:")
    results = session.query(Listing).all()
    if results:
        for listing in results:
            print(listing)
    else:
        print("No entries found in 'results' table.")

if __name__ == "__main__":
    init_db()
    print_database()
