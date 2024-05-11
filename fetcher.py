from pymongo import MongoClient
import pandas as pd

def fetch_data(client: MongoClient,db_name,collection_name,ticker=None) -> pd.DataFrame:
    """Fetch stock data from MongoDB and convert to a pandas DataFrame."""
    db = client[db_name]
    collection = db[collection_name]
    
    # Define filter based on ticker, if provided
    filter_query = {}  # Default to an empty filter
    if ticker:
        filter_query['ticker'] = ticker
    
    documents = list(collection.find(filter_query))
    all_data_rows = []

    for document in documents:
        for data in document.get('data', []):
            data['ticker'] = document.get('ticker', 'Unknown')
            all_data_rows.append(data)

    df = pd.DataFrame(all_data_rows)
    return df