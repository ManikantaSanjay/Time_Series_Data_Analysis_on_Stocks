from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from pymongo import MongoClient
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
URI = 'Enter your URI here'
DATABASE_NAME = 'stock_database'
COLLECTION_NAME = 'stock_data'

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

def fetch_data(client: MongoClient) -> pd.DataFrame:
    """Fetch stock data from MongoDB and convert to a pandas DataFrame."""
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    documents = list(collection.find({}))
    all_data_rows = []

    for document in documents:
        for data in document.get('data', []):
            data['ticker'] = document.get('ticker', 'Unknown')
            all_data_rows.append(data)

    df = pd.DataFrame(all_data_rows)
    return df


def calculate_historical_volatility(df, column_name='Close'):
    """
    Calculate the historical volatility of the closing prices for each month in the last quarter.

    Args:
        df (pd.DataFrame): DataFrame containing stock data with 'Date' and 'Close' prices.
        column_name (str): Name of the column containing the close prices. Default is 'Close'.
    
    Yields:
        pd.DataFrame: A DataFrame containing the historical volatility for each month and each stock.
    """
    # Ensure the Date column is a datetime type
    df['Date'] = pd.to_datetime(df['Date'])

    # Filter the last quarter months based on the maximum date in the DataFrame
    max_date = df['Date'].max()
    start_of_last_quarter = pd.Timestamp(max_date.year, max_date.month - 2, 1) if max_date.month > 2 else pd.Timestamp(max_date.year - 1, 10, 1)

    # Filter data to get the last quarter
    last_quarter_data = df[df['Date'] >= start_of_last_quarter]

    # Calculate the daily logarithmic returns
    last_quarter_data['Log Returns'] = np.log(last_quarter_data[column_name] / last_quarter_data[column_name].shift(1))
    
    # Sort data to ensure chronological order
    last_quarter_data.sort_values(['ticker', 'Date'], inplace=True)
    
    # Create a period column for grouping
    last_quarter_data['YearMonth'] = last_quarter_data['Date'].dt.to_period('M')

    # Loop through each group and yield results
    grouped = last_quarter_data.groupby(['ticker', 'YearMonth'])
    for (name, year_month), group in grouped:
        vol = group['Log Returns'].std()
        yield {'Name': name, 'YearMonth': str(year_month), 'Monthly Volatility': vol}

def calculate_stochastic_oscillator(df, periods=14):
    """
    Calculate the Stochastic Oscillator for the DataFrame.

    Args:
        df (pd.DataFrame): DataFrame containing the stock data with 'High', 'Low', and 'Close' prices.
        periods (int): Number of periods to use for calculating the oscillator. Default is 14.

    Returns:
        pd.DataFrame: DataFrame with additional columns for %K, %D, and overbought/oversold status.
    """
    # Calculate the rolling minimum and maximum
    df['lowest_low'] = df['Low'].rolling(window=periods).min()
    df['highest_high'] = df['High'].rolling(window=periods).max()

    # Calculate %K
    df['%K'] = ((df['Close'] - df['lowest_low']) / (df['highest_high'] - df['lowest_low'])) * 100

    # Calculate %D as 3-period SMA of %K
    df['%D'] = df['%K'].rolling(window=3).mean()

    # Determine overbought/oversold status using numpy where
    df['Status'] = np.where(df['%K'] > 80, 'Overbought',
                            np.where(df['%K'] < 20, 'Oversold', 'Neutral'))

    return df[['%K', '%D', 'Status']]

def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    Calculate the Relative Strength Index (RSI) for each ticker in the DataFrame.

    Args:
        df (pd.DataFrame): DataFrame containing stock data with 'Close', 'Date', and 'ticker' columns.
        period (int): The number of days to use for calculating the RSI, typically 14.

    Returns:
        pd.DataFrame: DataFrame with the RSI values added as a new column.
    """
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values(by=['ticker', 'Date'])

    # Function to calculate RSI for a single series
    def rsi_calc(x):
        delta = x.diff()
        gain = (delta.where(delta > 0, 0)).fillna(0)
        loss = (-delta.where(delta < 0, 0)).fillna(0)

        avg_gain = gain.rolling(window=period, min_periods=1).mean()
        avg_loss = loss.rolling(window=period, min_periods=1).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        rsi = rsi.replace([np.inf, -np.inf], np.nan)  # Handle infinite values
        return rsi

    # Group by ticker and apply RSI calculation
    rsi_values = df.groupby('ticker')['Close'].apply(rsi_calc)
    
    # Since rsi_values is a Series with a MultiIndex (Date, ticker), we need to re-align it with the original DataFrame
    # Here we directly assign the values to the 'RSI' column of df
    df['RSI'] = rsi_values.values  # This directly aligns values by position, avoiding index compatibility issues

    return df



def calculate_cagr(df: pd.DataFrame) -> Dict[str, Optional[float]]:
    """
    Calculate the Compound Annual Growth Rate (CAGR) for each ticker.

    Args:
        df (pd.DataFrame): DataFrame containing stock data with 'Close', 'Date', and 'ticker' columns.

    Returns:
        Dict[str, Optional[float]]: A dictionary with tickers as keys and their CAGR as values.
    """
    df['Date'] = pd.to_datetime(df['Date'])
    cagr_results = {}

    for ticker in df['ticker'].unique():
        ticker_data = df[df['ticker'] == ticker]
        ticker_data = ticker_data.sort_values(by='Date')
        initial_value = ticker_data['Close'].iloc[0]
        final_value = ticker_data['Close'].iloc[-1]
        start_date = ticker_data['Date'].iloc[0]
        end_date = ticker_data['Date'].iloc[-1]
        delta_years = (end_date - start_date).days / 365.25

        if delta_years > 0 and initial_value > 0:
            cagr = (final_value / initial_value) ** (1 / delta_years) - 1
            cagr_results[ticker] = cagr
        else:
            cagr_results[ticker] = None

    return cagr_results

def calculate_macd(df, column_name='Close', slow_period=26, fast_period=12, signal_period=9):
    """
    Calculate the Moving Average Convergence Divergence (MACD) for each ticker in a given DataFrame.

    Args:
        df (pd.DataFrame): DataFrame containing stock data with 'Date', 'Close' prices, and 'ticker'.
        column_name (str): Name of the column which contains the stock closing prices. Default is 'Close'.
        slow_period (int): Number of periods for the slow EMA. Default is 26.
        fast_period (int): Number of periods for the fast EMA. Default is 12.
        signal_period (int): Number of periods for the signal line EMA. Default is 9.

    Returns:
        pd.DataFrame: DataFrame containing the MACD line, Signal line, and ticker for each group.
    """
    # Convert 'Date' to datetime and set it as index if it's part of the DataFrame
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)

    # Prepare a list to collect each group's DataFrame
    results = []

    # Group by 'ticker' and calculate MACD for each
    for ticker, group in df.groupby('ticker'):
        # Calculate the Fast and Slow EMAs
        group['EMA_fast'] = group[column_name].ewm(span=fast_period, adjust=False).mean()
        group['EMA_slow'] = group[column_name].ewm(span=slow_period, adjust=False).mean()

        # Calculate the MACD line
        group['MACD'] = group['EMA_fast'] - group['EMA_slow']

        # Calculate the Signal line
        group['Signal_line'] = group['MACD'].ewm(span=signal_period, adjust=False).mean()

        # Retain ticker information in the results
        group['Ticker'] = ticker

        # Collect results
        results.append(group[['MACD', 'Signal_line', 'Ticker']])
    
    # Concatenate all results into a single DataFrame
    result_df = pd.concat(results)
    return result_df

# # Main execution
# if __name__ == "__main__":
#     client = connect_to_mongodb(URI)
#     df = fetch_data(client)
#     print(df.columns)
    
#     cagr_results = calculate_cagr(df)

#     # df is your DataFrame loaded with your stock data
#     rsi_df = calculate_rsi(df)
#     print(rsi_df)
    
#     monthly_volatilities = calculate_historical_volatility(df)
    

#     for result in monthly_volatilities:
#         print(result)

#     for ticker, cagr in cagr_results.items():
#         if cagr is not None:
#             logging.info(f"The CAGR for {ticker} is: {cagr:.2%}")
#         else:
#             logging.info(f"The CAGR for {ticker} is not calculable.")

#     # Group by 'ticker' and apply the calculation
#     result_dfs = []
#     for ticker, group in df.groupby('ticker'):
#         group = calculate_stochastic_oscillator(group)
#         group['Ticker'] = ticker  # Add ticker information to distinguish results
#         result_dfs.append(group)

#     # Combine all results
#     full_results = pd.concat(result_dfs)

#     # Print or analyze results
#     print(full_results)


    
#     macd_df = calculate_macd(df, 'Close', 26, 12, 9)
#     print(macd_df)