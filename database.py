"""
Description: Save results per search criteria using SQLalchemy and SQLite
Date Created: 2024-09-01
Date Modified: 2024-09-11
Author: SPolton
Modified By: SPolton
Version: 1.6.0
Credit: The initial implementation of database.py was assisted by ChatGPT 4o Mini
"""

from os import getenv
from dotenv import load_dotenv
from logging import getLogger

from sqlalchemy import create_engine, inspect, delete, update
from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer,
    String, Text, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.sql import func

load_dotenv()
DATABASE = getenv("DATABASE", "static/search_results.db")
DATABASE_URL = f"sqlite:///{DATABASE}"
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)
session = Session()

logger = getLogger(__name__)

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
    order = Column(Integer)
    url = Column(Text)
    title = Column(String)
    price = Column(String)
    location = Column(String)
    image = Column(Text)
    is_new = Column(Boolean, default=True)
    timestamp = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("search_id", "url", name="uix_search_id_url"),
    )
    
    search_criteria = relationship("SearchCriteria", back_populates="results")

    def __repr__(self):
        return (f"<Listing(search_id={self.search_id}, order={self.order},\tis_new={self.is_new}, price='{self.price}',\ttitle='{self.title}')>")
    
    def to_dict(self):
        """Convert the Listing object to a dictionary."""
        json_friendly_time = self.timestamp.astimezone().strftime("%y-%m-%d %H:%M:%S%z %Z")
        return {
            "id": self.id,
            "search_id": self.search_id,
            "order": self.order,
            "url": self.url,
            "title": self.title,
            "price": self.price,
            "location": self.location,
            "image": self.image,
            "is_new": self.is_new,
            "timestamp": json_friendly_time
        }


def init_db():
    """Create tables in the database if they don't exist."""
    logger.debug("init database.")
    Base.metadata.create_all(engine)
    inspector = inspect(engine)
        
    # Check if tables are available
    if "search_criteria" not in inspector.get_table_names():
        raise RuntimeError("Table 'search_criteria' is not available.")
    if "results" not in inspector.get_table_names():
        raise RuntimeError("Table 'results' is not available.")
    
def wipe_database():
    """Wipes the entire database by dropping all tables."""
    try:
        Base.metadata.drop_all(engine)
        logger.info("All tables have been dropped from the database.")
    except Exception as e:
        logger.error(f"An error occurred while wiping the database: {e}")

def get_or_insert_search_criteria(city, category, query):
    """Retrieve existing search criteria or create new if not found."""
    search_criteria = session.query(SearchCriteria).filter_by(
        city = city,
        category = category,
        query = query
    ).first()
    
    if search_criteria is None:
        search_criteria = SearchCriteria(
            city = city,
            category = category,
            query = query
        )
        session.add(search_criteria)
        session.commit()
    
    return search_criteria.id

def insert_new_results(search_id, results):
    """Insert new results into the database."""
    existing_urls = {listing.url for listing in session.query(Listing.url).filter_by(search_id=search_id).all()}

    # Filter out results with URLs that already exist
    new_results = [
        Listing(
            search_id = search_id,
            order = index + 1,
            url = listing.get("url"),
            title = listing.get("title"),
            price = listing.get("price"),
            location = listing.get("location"),
            image = listing.get("image"),
            is_new = True,
        )
        for index, listing in enumerate(results)
        if listing.get("url") not in existing_urls
    ]

    # Bulk insert new results
    try:
        if new_results:
            logger.info(f"Bulk inserting {len(new_results)} results.")
            session.bulk_save_objects(new_results)
            session.commit()
        else:
            logger.info("No new results to insert.")
    except Exception as e:
        session.rollback()  # Rollback the transaction on error
        logger.error(f"An error occurred during bulk insertion: {e}")


def set_all_not_new(search_id):
    """Update all records with the given search_id to set is_new = False."""
    try:
        logger.debug(f"set_all_not_new: Performing bulk update on search_id {search_id}")

        # Perform a bulk update of results.
        stmt = (
            update(Listing)
            .where(Listing.search_id == search_id)
            .values(is_new=False)
        )
        engine_result = session.execute(stmt)
        session.commit()
        logger.info(f"Updated {engine_result.rowcount} listings with is_new = False.")

    except Exception as e:
        session.rollback()
        logger.error(f"An error occurred while updating listing 'is_new' records: {e}")

def remove_stale_results(search_id, results):
    """Remove listings that are no longer present in the latest results."""
    try:
        latest_urls = {listing.get("url") for listing in results}

        # Perform a bulk delete of stale results.
        stmt = delete(Listing).where(
            Listing.search_id == search_id,
            ~Listing.url.in_(latest_urls)
        )
        engine_result = session.execute(stmt)
        session.commit()
        logger.info(f"Deleted {engine_result.rowcount} stale listings.")

    except Exception as e:
        session.rollback()  # Rollback the transaction on error
        logger.error(f"An error occurred while removing stale listings: {e}")

def get_results(search_id):
    """Retrieve existing results for a given search_id."""
    results = session.query(Listing).filter_by(search_id=search_id).order_by(Listing.order).all()
    logger.debug(f"get_results: returning {len(results)} results for search_id {search_id}.")
    return [listing.to_dict() for listing in results]

def get_new_results(search_id):
    """Identify and return new results labled as 'new' in the database for a given search_id."""
    new_results = session.query(Listing).filter_by(search_id=search_id, is_new=True).order_by(Listing.order).all()
    logger.debug(f"get_new_results: returning {len(new_results)} results for search_id {search_id}.")
    return [listing.to_dict() for listing in new_results]


def print_database():
    """Print the 'search_criteria' and 'results' tables to the terminal."""
    print("\nsearch_criteria table:")
    search_criteria_rows = session.query(SearchCriteria).all()
    if search_criteria_rows:
        for entry in search_criteria_rows:
            print(entry)
    else:
        print("No entries found in 'search_criteria' table.")
    
    print("\nresults table:")
    results = session.query(Listing).order_by(Listing.search_id, Listing.order).all()
    if results:
        for listing in results:
            print(listing)
    else:
        print("No entries found in 'results' table.")

if __name__ == "__main__":
    init_db()
    # wipe_database()
    # init_db()
    print_database()
