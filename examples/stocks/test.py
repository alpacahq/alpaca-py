from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.data.requests import StockAuctionsRequest, StockBarsRequest
from alpaca.data.enums import DataFeed
from alpaca.data.timeframe import TimeFrame
import os
from datetime import datetime

client = StockHistoricalDataClient(
    api_key=os.getenv("ALPACA_API_KEY"),
    secret_key=os.getenv("ALPACA_SECRET_KEY"),
    raw_data=False,
)

auctions = client.get_stock_auction(
    request_params=StockAuctionsRequest(
        symbol_or_symbols=["SPY", "AAPL"],
        start=datetime(2023, 1, 1),
        feed=DataFeed.SIP,
    )
)

# bars = client.get_stock_bars(
#     request_params=StockBarsRequest(
#         symbol_or_symbols=["SPY"],
#         start=datetime(2023, 1, 1),
#         feed=DataFeed.SIP,
#         timeframe=TimeFrame.Hour,
#     )
# )

print(auctions.df)
# print(bars.df)


