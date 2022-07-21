# Alpaca-py

[![Downloads](https://pepy.tech/badge/alpaca-py/month)](https://pepy.tech/project/alpaca-py)
[![Python Versions](https://img.shields.io/pypi/pyversions/alpaca-py.svg?logo=python&logoColor=white)](https://pypi.org/project/alpaca-py)
[![GitHub](https://img.shields.io/github/license/alpacahq/alpaca-py?color=blue)](https://github.com/alpacahq/alpaca-py/blob/master/LICENSE.md)
[![PyPI](https://img.shields.io/pypi/v/alpaca-py?color=blue)](https://pypi.org/project/alpaca-py/)
### About

Alpaca-py provides an interface for interacting with the various REST and WebSocket endpoints Alpaca offers.
You can access both historical and live market data for equities and cryptocurrencies via the Market Data API. 
You can place trades for both crypto and equities through a uniform interface. Alpaca-py also offers the ability
to manage your Broker API account by creating accounts, managing funds, and more. 

Learn more about the API products [Alpaca]((https://alpaca.markets/)) offers.

**Note: AlpacaPy is in the very early stages of alpha development and is not production ready. Currently AlpacaPy
interfaces with only the Market Data API, however the other APIs are coming soon.**

### Installation

Alpaca-py is supported on Python 3.8+.  You can install Alpaca-py using pip.

Run the following command in your terminal.

```shell
  pip install alpaca-py
```


### Dev setup

This project is managed via poetry so setup should be just running `poetry install`.

This repo is using [`pre-commit`](https://pre-commit.com/) to setup some checks to happen at commit time to keep the
repo clean. To set these up after you've run `poetry install` just run `poetry run pre-commit install` to have
pre-commit setup these hooks



