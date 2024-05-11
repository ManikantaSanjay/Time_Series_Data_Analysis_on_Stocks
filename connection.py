from pymongo import MongoClient
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def connect_to_mongodb(uri: str) -> MongoClient:
    """Create a new MongoDB client and connect to the server."""
    client = MongoClient(uri)
    try:
        client.admin.command('ping')
        logging.info("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        logging.error(f"Failed to connect to MongoDB: {e}")
        raise
    return client