from typing import Dict, List, Optional
import pandas as pd
import numpy as np

def calculate_historical_volatility(df, column_name='Close'):
    """
    Calculate the historical volatility of the closing prices for each month across all available data.

    Args:
        df (pd.DataFrame): DataFrame containing stock data with 'Date' and 'Close' prices.
        column_name (str): Name of the column containing the close prices. Default is 'Close'.
    
    Returns:
        pd.DataFrame: A DataFrame containing the historical volatility for each month and each stock.
    """
    # Ensure the Date column is a datetime type
    df['Date'] = pd.to_datetime(df['Date'])

    # Calculate the daily logarithmic returns
    df['Log Returns'] = np.log(df[column_name] / df[column_name].shift(1))
    
    # Sort data to ensure chronological order
    df.sort_values('Date', inplace=True)
    
    # Create a period column for grouping by month
    df['YearMonth'] = df['Date'].dt.to_period('M')

    # Group data by ticker and YearMonth, then calculate the standard deviation of the log returns
    results = []
    grouped = df.groupby(['ticker', 'YearMonth'])
    for (name, year_month), group in grouped:
        vol = group['Log Returns'].std()
        results.append({'Name': name[0], 'YearMonth': str(year_month), 'Monthly Volatility': vol})

    return pd.DataFrame(results)

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
    df['%K'] = ((df['Close'] - df['lowest_low']) / 
            (df['highest_high'] - df['lowest_low']).replace(0, np.nan)) * 100

    # Calculate %D as 3-period SMA of %K
    df['%D'] = df['%K'].rolling(window=3).mean()

    # Determine overbought/oversold status using numpy where
    df['Status'] = np.where(df['%K'] > 80, 'Overbought',
                            np.where(df['%K'] < 20, 'Oversold', 'Neutral'))

    return df[['%K', '%D', 'Status']]

def calculate_mfi(data, period=14):
    """
    Calculate the Money Flow Index (MFI).

    Args:
        data (pd.DataFrame): DataFrame containing 'High', 'Low', 'Close' and 'Volume' columns.
        period (int): Number of periods to use in the calculation (default is 14).

    Returns:
        pd.Series: A series containing the Money Flow Index.
    """
    # Typical Price
    data['Typical_Price'] = (data['High'] + data['Low'] + data['Close']) / 3

    # Raw Money Flow
    data['Raw_Money_Flow'] = data['Typical_Price'] * data['Volume']

    # Money Flow Ratio
    data['Up_Down'] = data['Typical_Price'].diff()
    data['Positive_Flow'] = data.apply(lambda x: x['Raw_Money_Flow'] if x['Up_Down'] > 0 else 0, axis=1)
    data['Negative_Flow'] = data.apply(lambda x: x['Raw_Money_Flow'] if x['Up_Down'] < 0 else 0, axis=1)

    # Sum over the periods
    data['Positive_Flow_Sum'] = data['Positive_Flow'].rolling(window=period).sum()
    data['Negative_Flow_Sum'] = data['Negative_Flow'].rolling(window=period).sum()

    # Money Flow Ratio
    data['Money_Flow_Ratio'] = data['Positive_Flow_Sum'] / data['Negative_Flow_Sum']

    # Money Flow Index
    data['MFI'] = 100 - (100 / (1 + data['Money_Flow_Ratio']))

    return data['MFI']

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
    

    return rsi_values.values


def calculate_annual_cagr(df: pd.DataFrame) -> Dict[str, Dict[int, Optional[float]]]:
    """
        Calculates the annual Compound Annual Growth Rate (CAGR) for each stock ticker in the DataFrame.

        Parameters:
            df (pd.DataFrame): A DataFrame containing columns 'Date', 'ticker', and 'Close', where:
                - 'Date' is the date of the stock price
                - 'ticker' is the stock ticker symbol
                - 'Close' is the closing price of the stock on that date

        Returns:
            Dict[str, Dict[int, Optional[float]]]: A dictionary with stock tickers as keys and another dictionary as values,
            where the inner dictionaries map a year to the CAGR for that year. If CAGR cannot be calculated for a year due
            to insufficient data or other issues, the value is None.
    """
    # Ensure 'Date' is in datetime format
    df['Date'] = pd.to_datetime(df['Date'])
    df['Year'] = df['Date'].dt.year  # Extract year for grouping

    # Dictionary to store CAGR results by ticker
    cagr_results = {}

    for ticker in df['ticker'].unique():
        # Filter data for the current ticker and sort it
        ticker_data = df[df['ticker'] == ticker].sort_values(by='Date')

        # Dictionary to store annual CAGR
        annual_cagr = {}

        # Group data by year
        for year, year_data in ticker_data.groupby('Year'):
            if len(year_data) < 2:
                # Not enough data points in the year to calculate CAGR
                annual_cagr[year] = None
                continue

            # Calculate initial and final values
            initial_value = year_data['Close'].iloc[0]
            final_value = year_data['Close'].iloc[-1]
            # Calculate time delta in years
            delta_years = (year_data['Date'].iloc[-1] - year_data['Date'].iloc[0]).days / 365.25

            # Calculate CAGR if possible
            if delta_years > 0 and initial_value > 0:
                cagr = (final_value / initial_value) ** (1 / delta_years) - 1
                annual_cagr[year] = cagr
            else:
                annual_cagr[year] = None

        cagr_results[ticker] = annual_cagr

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

