# AlpacaPy

### Dev setup

This project is managed via poetry so setup should be just running `poetry install`.

This repo is using [`pre-commit`](https://pre-commit.com/) to setup some checks to happen at commit time
to keep the repo clean. To set these up after you've run `poetry install` just run `poetry run pre-commit
install` to have pre-commit setup these hooks


**Note: AlpacaPy is in the very early stages of alpha development and is not production ready. Currently AlpacaPy interfaces with only the Market Data API, however the other APIs are coming soon.**

## Basic Example Use Cases
**Requesting Historical Market Data**

To retrieve historical market data, you’ll need to instantiate a historical data client with your API keys. There are many different methods that allow you to access various stock and crypto data. To see the full range of data types available, read the [API reference for market data](https://alpaca.markets/docs/python-sdk/api_reference/data_api.html). In this example, we will query daily bar data for Apple Inc (AAPL) between January 1st 2021 and December 31st 2021. Then we will convert the data to a dataframe and print it out to the console.

```python
from alpaca.data.historical import HistoricalDataClient
from alpaca.common.time import TimeFrame

API_KEY = 'api-key'
SECRET_KEY = 'secret-key'

client = HistoricalDataClient(API_KEY, SECRET_KEY)

bars = client.get_bars("AAPL", TimeFrame.Day, "2021-01-01", "2021-12-31")

print(bars.df)


#             open      high      low   close     volume  trade_count        vwap
# timestamp
# 2021-01-04  133.56  133.6116  126.760  129.41  143302687      1310228  129.732580
# 2021-01-05  128.98  131.7400  128.430  131.01   97667342       707584  130.717944
# 2021-01-06  127.53  131.0499  126.382  126.60  155104120      1202580  128.350036
# 2021-01-07  128.38  131.6300  127.860  130.92  109581117       718363  130.153889
# 2021-01-08  132.50  132.6300  130.230  132.05  105158675       800071  131.565744
# ...            ...       ...      ...     ...        ...          ...         ...
# 2021-12-27  177.10  180.4200  177.070  180.33   74912939       629431  179.056944
# 2021-12-28  180.20  181.3300  178.530  179.29   79103863       631316  179.707003
# 2021-12-29  179.30  180.6300  178.140  179.38   62325973       491576  179.455692
# 2021-12-30  179.59  180.5700  178.090  178.20   59770632       498613  179.374495
# 2021-12-31  178.00  179.2300  177.260  177.57   64038680       451478  177.800285

# [252 rows x 7 columns]
```

**Subscribing to Live Market Data**

Live market data is available for both crypto and stocks via websocket interfaces. Keep in mind live stock data is only available during market hours on trading days, whereas live crypto data is available 24/7. In this example, we will subscribe to live quote data for Bitcoin (BTCUSD). To do so, first we will need to create an instance of the CryptoDataStream client with our API keys. Then we can create an asynchronous callback method to handle our live data as it is available.

```python
from alpaca.data.live import CryptoDataStream

API_KEY = 'api-key'
SECRET_KEY = 'secret-key'

client = CryptoDataStream(API_KEY, SECRET_KEY)

# handler function will receive data as the data arrives
async def handler(data):
    print(data)

# subscribe to quote data for BTCUSD
client.subscribe_quotes(handler, "BTCUSD")

# start websocket client
client.run()
```