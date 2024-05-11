import pandas as pd
import talib

## Helper functions
def detect_divergences(df: pd.DataFrame) -> pd.DataFrame:
    """
    Identifies potential bullish and bearish divergences in a DataFrame based on closing prices and the Money Flow Index (MFI).

    Parameters:
        df (pd.DataFrame): A DataFrame that must include the following columns:
            - 'Close': the closing prices of the stock.
            - 'MFI': the Money Flow Index values.

    Returns:
        pd.DataFrame: The original DataFrame augmented with the following columns:
            - 'Price_High': The highest closing price over a rolling window.
            - 'MFI_High': The highest MFI value over the same rolling window.
            - 'Price_Low': The lowest closing price over the same rolling window.
            - 'MFI_Low': The lowest MFI value over the same rolling window.
            - 'Bull_Div': Boolean indicating a bullish divergence.
            - 'Bear_Div': Boolean indicating a bearish divergence.

    Notes:
        - Bullish divergence is detected when the price makes a new low that is not mirrored by a new low in the MFI.
        - Bearish divergence is detected when the price makes a new high that is not mirrored by a new high in the MFI.
    """
    # Ensure 'Close' and 'MFI' columns are present
    if 'Close' not in df.columns or 'MFI' not in df.columns:
        raise ValueError("DataFrame must contain 'Close' and 'MFI' columns")

    # Calculate rolling highs and lows for price and MFI
    df['Price_High'] = df['Close'].rolling(window=14, min_periods=1).max()
    df['MFI_High'] = df['MFI'].rolling(window=14, min_periods=1).max()
    df['Price_Low'] = df['Close'].rolling(window=14, min_periods=1).min()
    df['MFI_Low'] = df['MFI'].rolling(window=14, min_periods=1).min()

    # Detect bullish and bearish divergences
    df['Bull_Div'] = (df['Close'] == df['Price_Low']) & (df['MFI'] != df['MFI_Low'])
    df['Bear_Div'] = (df['Close'] == df['Price_High']) & (df['MFI'] != df['MFI_High'])

    return df

def detect_candlestick_patterns(df):
    """
    This function detects various candlestick patterns in a DataFrame and returns
    the DataFrame with additional columns for each pattern.

    Args:
    df (pandas.DataFrame): A DataFrame with columns 'Open', 'High', 'Low', 'Close'.

    Returns:
    pandas.DataFrame: The original DataFrame with additional boolean columns for each detected pattern.
    """
    # Ensure the column names match expected pattern by TA-Lib
    open_prices = df['Open']
    high_prices = df['High']
    low_prices = df['Low']
    close_prices = df['Close']
    
    # Detect patterns
    df['Doji'] = talib.CDLDOJI(open_prices, high_prices, low_prices, close_prices)
    df['Hammer'] = talib.CDLHAMMER(open_prices, high_prices, low_prices, close_prices)
    df['Hanging_Man'] = talib.CDLHANGINGMAN(open_prices, high_prices, low_prices, close_prices)
    df['Bullish_Engulfing'] = talib.CDLENGULFING(open_prices, high_prices, low_prices, close_prices) > 0  # Bullish if positive
    df['Bearish_Engulfing'] = talib.CDLENGULFING(open_prices, high_prices, low_prices, close_prices) < 0  # Bearish if negative
    df['Morning_Star'] = talib.CDLMORNINGSTAR(open_prices, high_prices, low_prices, close_prices)
    df['Evening_Star'] = talib.CDLEVENINGSTAR(open_prices, high_prices, low_prices, close_prices)
    
    # Convert numeric results to boolean (0 is no pattern, anything else is a pattern detected)
    for col in ['Doji', 'Hammer', 'Hanging_Man', 'Morning_Star', 'Evening_Star']:
        df[col] = df[col] != 0
    
    return df
