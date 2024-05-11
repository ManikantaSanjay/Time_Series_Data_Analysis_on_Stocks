import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import stock_metrics as sm
import connection as conn
import fetcher as ft
import helper
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()



# Assuming you have already calculated your ratios and stored them in suitable variables

# Initialize Dash app
app = dash.Dash(__name__)

# Define the layout of the Dash app
app.layout = html.Div([
    # Dropdown for selecting a stock ticker
    dcc.Dropdown(
        id='ticker-dropdown',
        options=[
            {'label': 'Apple', 'value': 'AAPL'},
            {'label': 'Amazon', 'value': 'AMZN'},
            {'label': 'Google', 'value': 'GOOG'},
            {'label': 'Microsoft', 'value': 'MSFT'},
            # Add more options for other stocks as needed
        ],
        value='AAPL',  # Default value
        clearable=False,
    ),
    # Graph to display stock and RSI data
    dcc.Graph(id='stock-graph'),
    dcc.Graph(id='stochastic-graph'),
    # Separate Graph to display MACD and Signal line
    dcc.Graph(id='macd-graph'),
    dcc.Graph(id='cagr-graph'), 
    dcc.Graph(id='price-mfi-graph'),
])

@app.callback(
    Output('stochastic-graph', 'figure'),
    [Input('ticker-dropdown', 'value')]
)

def update_stochastic_graph(selected_ticker):
    client = conn.connect_to_mongodb(os.getenv("URI"))
    df = ft.fetch_data(client, os.getenv("DATABASE_NAME"), os.getenv("COLLECTION_NAME"), ticker=selected_ticker)
    df1 = sm.calculate_stochastic_oscillator(df)

    df1['Date'] = df['Date']

    # Create traces for the stock data
    close_trace = go.Scatter(
        x=df['Date'],
        y=df['Close'],
        mode='lines',
        name='Closing Prices'
    )

    # Create traces for %K and %D
    k_trace = go.Scatter(
        x=df1['Date'],
        y=df1['%K'],
        mode='lines',
        name='%K',
        line=dict(color='blue'),
        yaxis = 'y2'
    )

    d_trace = go.Scatter(
        x=df1['Date'],
        y=df1['%D'],
        mode='lines',
        name='%D',
        line=dict(color='orange'),
        yaxis = 'y3'
    )

    # Mark overbought and oversold areas
    overbought_trace = go.Scatter(
        x=df['Date'][df1['Status'] == 'Overbought'],
        y=df['Close'][df1['Status'] == 'Overbought'],
        mode='markers',
        name='Overbought',
        marker=dict(color='red', size=10)  # Increase marker size for visibility
    )

    oversold_trace = go.Scatter(
        x=df['Date'][df1['Status'] == 'Oversold'],
        y=df['Close'][df1['Status'] == 'Oversold'],
        mode='markers',
        name='Oversold',
        marker=dict(color='green', size=10)  # Increase marker size for visibility
    )

    # Set up the layout
    layout = go.Layout(
        title=f'Stochastic Oscillator for {selected_ticker}',
        xaxis=dict(title='Date', tickformat='%Y-%m-%d'),
        yaxis=dict(title='Price'),
        yaxis2=dict(
            title='K ratio',
            overlaying='y',
            side='right',
            range=[0, 100]  # Set the range to keep the RSI values visible
        ),
        yaxis3=dict(
            title='D ratio',
            overlaying='y',
            side='right',
            range=[0, 100]  # Set the range to keep the RSI values visible
        ),
        legend=dict(x=0, y=1),
        hovermode='closest'  # Enable hover for better interaction
    )

    fig = {'data': [close_trace, k_trace, d_trace, overbought_trace, oversold_trace], 'layout': layout}
    return fig

@app.callback(
    Output('price-mfi-graph', 'figure'),
    [Input('ticker-dropdown', 'value')]
)

def update_graph(selected_ticker):
    # Fetch data
    client = conn.connect_to_mongodb(os.getenv("URI"))
    df = ft.fetch_data(client, os.getenv("DATABASE_NAME"), os.getenv("COLLECTION_NAME"), ticker=selected_ticker)
    df['MFI'] = sm.calculate_mfi(df)

    # Detect divergences
    df = helper.detect_divergences(df)

    # Create traces for the stock data
    price_trace = go.Scatter(
        x=df['Date'],
        y=df['Close'],
        mode='lines',
        name='Close Price'
    )

    # Create MFI trace
    mfi_trace = go.Scatter(
        x=df['Date'],
        y=df['MFI'],
        mode='lines',
        name='Money Flow Index',
        yaxis='y2'
    )

    # Highlight bullish divergences
    bull_div_trace = go.Scatter(
        x=df[df['Bull_Div']]['Date'],
        y=df[df['Bull_Div']]['Close'],
        mode='markers',
        marker=dict(color='green', size=10),
        name='Bullish Divergence'
    )

    # Highlight bearish divergences
    bear_div_trace = go.Scatter(
        x=df[df['Bear_Div']]['Date'],
        y=df[df['Bear_Div']]['Close'],
        mode='markers',
        marker=dict(color='red', size=10),
        name='Bearish Divergence'
    )

    # Layout with overbought and oversold lines
    layout = go.Layout(
        title=f'MFI and Closing Prices for {selected_ticker}',
        xaxis=dict(title='Date'),
        yaxis=dict(title='Close Price'),
        yaxis2=dict(
            title='MFI',
            overlaying='y',
            side='right',
            range=[0, 100]
        ),
        shapes=[
            {'type': 'line', 'xref': 'paper', 'x0': 0, 'x1': 1, 'yref': 'y2', 'y0': 80, 'y1': 80, 'line': {'color': 'red', 'width': 1, 'dash': 'dash'}},
            {'type': 'line', 'xref': 'paper', 'x0': 0, 'x1': 1, 'yref': 'y2', 'y0': 20, 'y1': 20, 'line': {'color': 'green', 'width': 1, 'dash': 'dash'}},
        ],
        legend=dict(x=0, y=1),
        hovermode='closest'
    )

    fig = {'data': [price_trace, mfi_trace, bull_div_trace, bear_div_trace], 'layout': layout}
    return fig

# Define callback to update the main stock data and RSI graph
@app.callback(
    Output('stock-graph', 'figure'),
    [Input('ticker-dropdown', 'value')]
)
def update_stock_graph(selected_ticker):
    client = conn.connect_to_mongodb(os.getenv("URI"))
    df = ft.fetch_data(client, os.getenv("DATABASE_NAME"), os.getenv("COLLECTION_NAME"), ticker=selected_ticker)
    df['RSI'] = sm.calculate_rsi(df)

    # Create traces for closing prices and RSI
    traces = [
        go.Scatter(
            x=df['Date'],
            y=df['Close'],
            mode='lines',
            name='Closing Prices'
        ),
        go.Scatter(
            x=df['Date'],
            y=df['RSI'],
            mode='lines',
            name='RSI',
            yaxis='y2'  # Use secondary y-axis for RSI
        ),
    ]

    layout = go.Layout(
        title=f'Closing Prices and RSI for {selected_ticker}',
        xaxis=dict(title='Date'),
        yaxis=dict(title='Price'),
        yaxis2=dict(
            title='RSI',
            overlaying='y',
            side='right',
            range=[0, 100]  # Set the range to keep the RSI values visible
        ),
        shapes=[
            # Line Horizontal Upper Bound (RSI=70)
            {
                'type': 'line',
                'xref': 'paper',
                'x0': 0,
                'x1': 1,
                'yref': 'y2',
                'y0': 70,
                'y1': 70,
                'line': {
                    'color': 'red',
                    'width': 2,
                    'dash': 'dashdot',
                },
            },
            # Line Horizontal Lower Bound (RSI=30)
            {
                'type': 'line',
                'xref': 'paper',
                'x0': 0,
                'x1': 1,
                'yref': 'y2',
                'y0': 30,
                'y1': 30,
                'line': {
                    'color': 'green',
                    'width': 2,
                    'dash': 'dashdot',
                },
            }
        ],
        legend=dict(x=0, y=1)
    )

    return {'data': traces, 'layout': layout}

# Define callback for updating MACD and Signal Line Graph
@app.callback(
    Output('macd-graph', 'figure'),
    [Input('ticker-dropdown', 'value')]
)
def update_macd_graph(selected_ticker):
    client = conn.connect_to_mongodb(os.getenv("URI"))
    df = ft.fetch_data(client, os.getenv("DATABASE_NAME"), os.getenv("COLLECTION_NAME"), ticker=selected_ticker)
    results_df = sm.calculate_macd(df)

    # Create traces for MACD and Signal line
    traces = [
        go.Scatter(
            x=df.index,
            y=results_df['MACD'],
            mode='lines',
            name='MACD'
        ),
        go.Scatter(
            x=df.index,
            y=results_df['Signal_line'],
            mode='lines',
            name='Signal Line'
        )
    ]

    layout = go.Layout(
        title=f'MACD and Signal Line for {selected_ticker}',
        xaxis=dict(title='Date'),
        yaxis=dict(title='MACD Value'),
        legend=dict(x=0, y=1)
    )

    return {'data': traces, 'layout': layout}

@app.callback(
    Output('cagr-graph', 'figure'),  # Specify the Output component and property
    [Input('ticker-dropdown', 'value')]  # Specify the Input component and property
)
def update_cagr_graph(selected_ticker):
    client = conn.connect_to_mongodb(os.getenv("URI"))
    df = ft.fetch_data(client, os.getenv("DATABASE_NAME"), os.getenv("COLLECTION_NAME"), ticker=selected_ticker)
    cagr_data = sm.calculate_annual_cagr(df)  # Assuming calculate_cagr is imported from stock_metrics

    # Prepare the data for the bar graph
    # Initialize lists to hold the graph data
    years = []
    cagrs = []
    text_labels = []
    
    # Assuming `cagr_data[selected_ticker]` gives us a dictionary of {year: cagr}
    annual_data = cagr_data.get(selected_ticker, {})
    for year, cagr in annual_data.items():
        if cagr is not None:
            years.append(year)
            cagrs.append(cagr)
            text_labels.append(f"{cagr:.2%}")

    bars = [go.Bar(
        x=years,
        y=cagrs,
        text=text_labels,
        textposition='auto'
    )]

    # Configure the layout of the graph
    layout = go.Layout(
        title=f'Compound Annual Growth Rate (CAGR) for {selected_ticker}',
        xaxis=dict(title='Year'),
        yaxis=dict(title='CAGR (%)', tickformat='%'),
        legend=dict(x=0, y=1)
    )

    return {'data': bars, 'layout': layout}

# Run the Dash app
if __name__ == '__main__':
    app.run_server(debug=True)
