# Time_Series_Data_Analysis_on_Stocks
## Description:
This repository is dedicated to performing exploratory time series data analysis on daily stock prices of key tech companies: Apple, Microsoft, Google, and Amazon, over a span of 5 years. 

Version 2 : Update -  The project includes features for fetching real-time stock data using Yahoo Finance API, storing it in MongoDB, and performing various statistical and financial analyses. Additionally, it now features an interactive web-based dashboard built with Dash that allows for dynamic visualization and deeper analysis of stock data.

## 🛠 Libraries Used
* Pandas - For data manipulation and analysis
* Numpy - Support for large, multi-dimensional arrays and matrices
* Seaborn & Matplotlib - For plotting graphs for data visualization
* MongoDB - Used for storing fetched stock data
* yfinance - Used to fetch live stock data
* Dash: Used for building web-based application dashboards.
* TA-Lib: For calculating technical indicators
* Plotly: For creating interactive plots.

## 🗂 Dataset

Explore the historical and the most recent stock data:

Historical Data: Navigate to the link to view the .csv files for each company https://github.com/ManikantaSanjay/Time_Series_Data_Analysis_on_Stocks/tree/main/individual_stocks_5yr :link:

Real-time Data: Data is fetched daily using the yfinance library and stored in MongoDB

## 📊  Tasks Performed

#### Task 1 : Analysing the Closing Price of all the stocks

#### Task 2 : Analysing the Total Volume of stocks being traded each day

#### Task 3 : Analysing the Daily Price Change in stock.

#### Task 4 : Analysing the Monthly Mean of Close Column.

#### Task 5 : Analysing the Correlation between the Stock Prices of these Tech companies. 

#### Task 6 : Analysing the Daily Return of Each Stock & Their Co-Relation

#### Task 7 : Value at Risk Analysis for Apple Stocks

#### Task 8 : Fetch and Update Stock Data Daily: Script to fetch daily stock data from Yahoo Finance and update the MongoDB database.

#### Task 9: Advanced Financial Calculations:
* Stochastic Oscillator and RSI (Relative Strength Index) calculations to measure stock momentum.
* Historical Volatility analysis of closing prices for each month.
* CAGR (Compound Annual Growth Rate) to measure the mean annual growth rate of investment.
* MACD (Moving Average Convergence Divergence) to reveal changes in the strength, direction, momentum, and duration of a trend in a stock's price.
* Advanced Candlestick pattern detection for strategic trading insights.
* Analysis of Money Flow Index (MFI) to identify overbought or oversold conditions.
* Detection of divergences between price movements and MFI, highlighting potential reversal points.
  

## ⚙ Setup and Installation
Ensure you have Python and MongoDB installed on your system. Install the necessary Python libraries using:

```bash
pip install pandas numpy seaborn matplotlib pymongo yfinance dash plotly talib
python dashboard.py
```


Feel free to fork this repository or contribute by providing suggestions to improve the analysis or adding new features to enhance the stock data exploration.

## Add a star 🌟 to the repo if u like it. 😃 Thank You !!
