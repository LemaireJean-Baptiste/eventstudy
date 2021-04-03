import numpy as np
import requests
import json

#Work in progress

def price(tickers: list):
    prices = dict()
    api_key = "demo"
    def url(ticker):
        return f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&outputsize=full&apikey={api_key}'

    tickers = np.unique(np.array(tickers))

    for ticker in tickers:
        r = requests.get(url(ticker))
        for date, prices in r.json["Time Series (Daily)"]:
            