# RSI & MACD Trading Bot with Alpaca and ChatGPT

This project is an example automated trading bot for US equities using Alpaca's Trading API, Python, and AWS EC2. It uses RSI and MACD indicators to generate buy/sell signals and is designed to run reliably in the cloud, executing trades only during US market hours.

## Overview

- **Goal:** Deploy a fully automated trading bot that uses RSI and MACD signals to trade a specified stock (default: TQQQ) on Alpaca, with risk management and cloud automation.
- **Reference:** [Alpaca RSI & MACD Bot Guide](https://alpaca.markets/learn/free-rsi-and-macd-trading-bot-with-chatgpt-and-alpaca)

## Features

- **Automated Trading:** Fetches data, computes indicators, and submits orders automatically.
- **Indicators:**
  - **RSI (14):** Entry on oversold bounce, exit on overbought retreat.
  - **MACD (12, 26, 9):** Confirms momentum shifts for entries/exits.
  - **Trend Filter:** 50/100/200-period moving averages to trade with the trend.
- **Risk Management:** Position size is limited by buying power and risk percentage (default: 2%).
- **Market Awareness:** Trades only when the market is open, sleeps or exits otherwise.
- **Cloud Automation:** Designed for AWS EC2, scheduled via cron for US market hours.

## Strategy Logic (from `strategy.py`)

- **Main Loop:** Runs only when the market is open, checks status with three key `if` statements.
- **Data:** Fetches historical bars for the target symbol at two timeframes.
- **Indicators:** Computes RSI, MACD, and moving averages.
- **Entry:** Buys if trend is bullish, RSI bounces from oversold, and MACD golden cross—all within a window.
- **Exit:** Sells if RSI retreats from overbought and MACD gives a bearish signal within a window.
- **Position Sizing:** Based on buying power and risk limits.
- **Order Execution:** Submits market orders, logs to `trade_log.txt`.
- **Scheduling:** Sleeps until the next scheduled run (e.g., top of the next hour).

## Trading Bot Scheduling Logic

The trading bot implemented in `strategy.py` is designed to execute its main trading logic **once per hour, at the top of each hour**, as long as the market is open. After each cycle, the script calculates the next top of the hour and pauses until that time. This ensures that trading decisions and data fetching are performed on an hourly basis, rather than continuously or at a higher frequency. The script checks the market status before each cycle and will only run while the market is open.

## Setup

1. **Create the EC2 instance (e.g., Ubuntu) from the AWS EC2 console.**
2. **Access your EC2 instance from your local computer using SSH:**
   ```bash
   ssh -i your-key.pem ubuntu@your-ec2-ip
   ```
3. **Create a project folder on the EC2 instance and navigate into it:**
   ```bash
   mkdir new_folder_name
   cd ./new_folder_name
   ```
4. **Create and activate a Python virtual environment:**
   ```bash
   sudo apt update
   sudo apt install python3-venv -y
   python3 -m venv venv
   source venv/bin/activate
   ```
5. **Use `svn` to download the subdirectory to EC2:**
   ```bash
   sudo apt update
   sudo apt install subversion -y
   svn export https://github.com/alpacahq/alpaca-py/trunk/examples/stocks/build_trading_bot_with_chatgpt
   ```
   **Or upload the files to EC2 from your local computer:**
   ```bash
   scp -i your-key.pem strategy.py secret.py requirements.txt ubuntu@your-ec2-ip:/home/ubuntu/new_folder_name
   ```
6. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
7. **Create your `.env` file** with your Alpaca credentials described below.
8. **Set up the cron job** as described below.
9. **(Optinal) manually run the trading bot (for testing):**
   ```bash
   /home/ubuntu/<new_folder_name>/venv/bin/python /home/ubuntu/<new_folder_name>/strategy.py
   ```
10. **Monitor logs** in `trade_log.txt`.

## Deployment & Scheduling

**Cron Job Example:**
In AWS EC2, open the crontab.
```bash
crontab -e
```
Add the following command in the crontab and save / close it
```bash
CRON_TZ=America/New_York
30 9 * * 1-5 /home/ubuntu/{new_folder_name}/venv/bin/python /home/ubuntu/{new_folder_name}/strategy.py >> /home/ubuntu/{new_folder_name}/trade_log.txt 2>&1
```
- Runs the bot at 9:30am ET on weekdays.

## Security & Environment

- **Monitor your bot and account regularly.**
- **For research/education only.** Trading is risky; test in paper mode first.
- **Never hardcode API credentials. Instead, store keys in a `.env` file on your EC2 instance:**
  The script loads these at runtime.
  ```
  # Please change the following to your own PAPER api key and secret
  # You can get them from https://app.alpaca.markets/dashboard/overview
  API_KEY = "<YOUR PAPER API KEY>"
  API_SECRET = "<YOUR PAPER API SECRET>"
  PAPER = True # True for paper trading, False for live trading
  trade_api_url = None
  trade_api_wss = None
  data_api_url = None
  stream_data_wss = None
  ```
- **Make sure to replace `your-key.pem`, `your-ec2-ip`, and `<new_folder_name>` with your actual key file, EC2 public IP, and desired folder name. The manual run path in step 9 should match your actual project directory structure.**
- In your `strategy.py` file, update any file paths that include `<new_folder_name>` (such as the path to your `.env` file) to match your actual project directory name.
  ```python
  load_dotenv(dotenv_path='/home/ubuntu/<new_folder_name>/.env')
  ```

  Replace `<new_folder_name>` with the name of your project directory in AWS EC2 instance.

## References

- [Alpaca /learn article - RSI & MACD Bot Guide](https://alpaca.markets/learn/free-rsi-and-macd-trading-bot-with-chatgpt-and-alpaca)
- [Alpaca-py SDK](https://github.com/alpacahq/alpaca-py)

---

## Disclosures

Please note that this tutorial is for general informational purposes only and is believed to be accurate as of the posting date but may be subject to change. The examples above are for illustrative purposes only.

Alpaca is not affiliated with ChatGPT or any of the companies or creators referenced in this article and is not responsible for the liabilities of the others.

Options trading is not suitable for all investors due to its inherent high risk, which can potentially result in significant losses. Please read [Characteristics and Risks of Standardized Options](https://www.theocc.com/company-information/documents-and-archives/options-disclosure-document?ref=alpaca.markets) before investing in options.

Past hypothetical backtest results do not guarantee future returns, and actual results may vary from the analysis.

Extended Hours trading has unique risks and is different from trading in the main trading session, for more information please visit our [Alpaca Extended Hours Trading Risk Disclosure](https://files.alpaca.markets/disclosures/library/ExtHrsRisk.pdf?ref=alpaca.markets).

Orders placed outside regular trading hours (9:30 a.m. – 4:00 p.m. ET) may experience price fluctuations, partial executions, or delays due to lower liquidity and higher volatility.

Orders not designated for extended hours execution will be queued for the next trading session.

Additionally, fractional trading may be limited during extended hours. For more details, please review [Alpaca Extended Hours & Overnight Trading Risk Disclosure](https://files.alpaca.markets/disclosures/library/ExtHrsOvernightRisk.pdf?ref=alpaca.markets).

All investments involve risk, and the past performance of a security, or financial product does not guarantee future results or returns. There is no guarantee that any investment strategy will achieve its objectives. Please note that diversification does not ensure a profit, or protect against loss. There is always the potential of losing money when you invest in securities, or other financial products. Investors should consider their investment objectives and risks carefully before investing.

Cryptocurrency is highly speculative in nature, involves a high degree of risks, such as volatile market price swings, market manipulation, flash crashes, and cybersecurity risks. Cryptocurrency regulations are continuously evolving, and it is your responsibility to understand and abide by them. Cryptocurrency trading can lead to large, immediate and permanent loss of financial value. You should have appropriate knowledge and experience before engaging in cryptocurrency trading. For additional information, please click [here](https://files.alpaca.markets/disclosures/library/CryptoRiskDisclosures.pdf?ref=alpaca.markets).

The Paper Trading API is offered by AlpacaDB, Inc. and does not require real money or permit a user to transact in real securities in the market. Providing use of the Paper Trading API is not an offer or solicitation to buy or sell securities, securities derivative or futures products of any kind, or any type of trading or investment advice, recommendation or strategy, given or in any manner endorsed by AlpacaDB, Inc. or any AlpacaDB, Inc. affiliate and the information made available through the Paper Trading API is not an offer or solicitation of any kind in any jurisdiction where AlpacaDB, Inc. or any AlpacaDB, Inc. affiliate (collectively, "Alpaca") is not authorized to do business.

Commission-free trading means that there are no commission charges for Alpaca self-directed individual cash brokerage accounts that trade U.S.-listed securities and options through an API. Relevant regulatory fees may apply. Commission-free trading is available to Alpaca's retail customers. Alpaca reserves the right to charge additional fees if it is determined that order flow is non-retail in nature.

Securities brokerage services are provided by Alpaca Securities LLC ("Alpaca Securities"), member [FINRA](https://www.finra.org/?ref=alpaca.markets)/[SIPC](https://www.sipc.org/?ref=alpaca.markets), a wholly-owned subsidiary of AlpacaDB, Inc. Technology and services are offered by AlpacaDB, Inc.

Cryptocurrency services are made available by Alpaca Crypto LLC ("Alpaca Crypto"), a FinCEN registered money services business (NMLS # 2160858), and a wholly-owned subsidiary of AlpacaDB, Inc. Alpaca Crypto is not a member of SIPC or FINRA. Cryptocurrencies are not stocks and your cryptocurrency investments are not protected by either FDIC or SIPC. Please see the [Disclosure Library](https://alpaca.markets/disclosures?ref=alpaca.markets) for more information.

This is not an offer, solicitation of an offer, or advice to buy or sell securities or cryptocurrencies or open a brokerage account or cryptocurrency account in any jurisdiction where Alpaca Securities or Alpaca Crypto, respectively, are not registered or licensed, as applicable.