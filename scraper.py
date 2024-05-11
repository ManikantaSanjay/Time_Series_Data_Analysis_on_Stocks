import yfinance as yf
import datetime
from pymongo import MongoClient
from typing import List, Dict, Optional
from pymongo.collection import Collection
from pymongo.database import Database

from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Setup MongoDB client
def setup_mongodb(connection_string: str, db_name: str, collection_name: str) -> Collection:
    """Establishes a connection to the MongoDB and returns the collection handle."""
    client = MongoClient(connection_string)
    db: Database = client[db_name]
    collection: Collection = db[collection_name]
    return collection

# Fetch stock data from Yahoo Finance
def fetch_stock_data(tickers: List[str], start_date: datetime.datetime, end_date: datetime.datetime) -> None:
    """Fetches stock data for given tickers from Yahoo Finance and stores it in MongoDB."""
    for ticker in tickers:
        data = yf.download(ticker, start=start_date, end=end_date)
        data_dict: List[Dict] = data.reset_index().to_dict("records")
        collection.update_one({"ticker": ticker}, {"$set": {"data": data_dict}}, upsert=True)

# Example usage
if __name__ == "__main__":
    # MongoDB setup
    collection = setup_mongodb(os.getenv("MONGO_CONN_STRING"), os.getenv("DATABASE_NAME"), os.getenv("COLLECTION_NAME"))
    
    # Define the ticker symbols for the companies
    tickers = ['AAPL', 'GOOG', 'MSFT', 'AMZN']
    
    # Get today's date
    today = datetime.datetime.now()
    
    # Calculate the date 5 years ago
    start_date = today - datetime.timedelta(days=5 * 365)
    
    # Fetch data and store in MongoDB
    fetch_stock_data(tickers, start_date, today)

