<!-- GPT-USAGE-HEADER:v1
Type: reference documentation (not executable code).
Rules: Treat as docs; do not run as code. Obey the action schemas in ./01-unified-instruction-set.md.
-->
Alpha – Trade Execution & Alpaca Integration

Alpha executes trades through the Alpaca brokerage API (via the alpaca-py library), enabling it to place and manage orders programmatically in both paper trading and live trading modes. Alpha is configured to follow all of Alpaca’s rules and best practices for order placement, ensuring that trades are executed correctly and that risk controls (like stop-losses) are in place. This section details how Alpha places orders, handles common issues, and manages the trading environment:

Placing Orders

Alpha supports various order types to accommodate different trading scenarios and strategy needs. When submitting orders, Alpha always provides the required parameters and double-checks them for correctness to avoid rejections. The supported order types include:

Market, Limit, Stop, and Stop-Limit Orders – For basic buy/sell operations: Alpha provides the symbol (ticker), side (buy or sell), and type of order, along with exactly one of either qty (quantity of shares) or notional (dollar amount to trade). By rule, one of these must be specified but not both. If the order is a limit order, Alpha will include a limit_price. If it’s a stop (market stop) order, Alpha includes a stop_price. For a combined stop-limit order, both limit_price and stop_price are provided. Alpha ensures stop prices are placed at a sensible level – Alpaca requires that for buy stop orders, the stop_price is at least $0.01 above the current bid (and conversely, for sell stop orders, at least $0.01 below the current ask). This prevents stop orders from triggering instantly. Alpha automatically checks the current price and will adjust or reject a stop order if it would violate this rule.

Bracket Orders – Alpha uses bracket orders to simultaneously set profit-target and stop-loss exit orders at the moment of entry. To do this, Alpha sets order_class to "bracket" and attaches two additional parameters: a take_profit object (with a specified limit_price for the profit-taking order) and a stop_loss object (with a stop_price for the protective stop-loss order). When Alpha places a bracket order, it effectively sends one primary order (e.g., a buy) and instructs Alpaca to create the linked take-profit and stop-loss orders if that primary order fills. Alpha (in conjunction with the Alpaca-actions proxy if used) will pre-check that the stop-loss price is valid and not too close to current prices (to avoid immediate trigger as noted above). With bracket orders, once the primary entry fills, the profit and stop orders become active OCO (One-Cancels-Other) orders – meaning if one executes, the other is automatically canceled. If the entry does not fill or is canceled, neither child order will execute. This ensures built-in risk management, as every position opened with a bracket has a predefined exit strategy.

Trailing Stop Orders – For trades where Alpha wants to let profits run while still protecting from reversal, it can use trailing stop orders. A trailing stop order dynamically adjusts its stop price as the market moves favorably. When placing a trailing stop, Alpha sets type="trailing_stop" and specifies exactly one of the following: trail_price (a fixed dollar amount by which the stop trails the price) or trail_percent (a percentage by which the stop trails). Alpha does not set a static limit_price or stop_price on these orders, because Alpaca’s system will manage the stop price automatically. For example, if Alpha sets a trail of $1 on a long position, for every $1 increase in the stock’s price, the stop-loss price will move up by $1, but if the stock price falls, the stop price remains at its last level – thereby “trailing” the price at a fixed distance. Trailing stops are useful for capturing gains in a trending move without having to pick an exact exit price. Alpha uses them either as part of trade management (manually converting a normal stop to a trailing stop once a trade is in profit) or as an initial order type if the strategy calls for it.

Throughout the order placement process, Alpha populates any other required fields (such as time-in-force, e.g., tif="day" for day orders unless otherwise specified). It logs the order details in the journal (including order IDs and confirmations from Alpaca). If Alpaca returns an order ID and status, Alpha will monitor that order for execution and then manage any subsequent steps (like placing protective stops if not using a bracket, or recording fills and slippage).

Typical Errors and Avoidance

While interacting with Alpaca’s API, certain common errors can occur if requests are improperly formed or if system limits are hit. Alpha anticipates and avoids these issues by validating inputs and following best practices. Some typical errors and how Alpha handles them:

400 Bad Request – This error indicates something is wrong with the order parameters. Alpha carefully validates orders to prevent common 400 errors. For instance, Alpaca will return a 400 error if both qty and notional are provided in one order (only one should be used). Alpha will ensure it sends only one of these fields. Another case is for trailing stop orders: Alpaca requires exactly one of trail_price or trail_percent – providing zero or both will cause a 400 error. Alpha’s order builder enforces that rule. A 400 can also occur if a stop_loss.stop_price in a bracket is too close to market (e.g., not $0.01 below ask for a buy), as mentioned above. Alpha always computes a safe stop price offset to avoid immediate triggers. Additionally, Alpaca does not allow modifying a trailing stop order via API once placed (attempting a PATCH update on such an order yields 400), so Alpha either avoids that or cancels & recreates the order if a change is needed. By adhering to Alpaca’s specifications in the order format and logic, Alpha minimizes the chance of a bad request error. If a 400 error still occurs, Alpha will log the exact message from Alpaca, explain it to the user, and adjust the approach accordingly (for example, if the user input a stop too tight, Alpha will inform them of the $0.01 rule and suggest a corrected stop price).

403 Forbidden – This typically means authentication or permission issues (e.g., using the wrong API key or trying to access a protected resource). If Alpha encounters a 403, it indicates either the API keys are invalid for the attempted action (such as trying to trade in a live account with paper keys or vice versa) or the account lacks permissions (for example, attempting short sales or assets not allowed). Alpha handles this by double-checking the environment and keys. It uses the readiness check (see below) to ensure credentials are correct at startup. Should a 403 occur, Alpha will not retry blindly; it will notify the user that the request was denied and likely prompt to verify API keys and account status.

413 Payload Too Large / 414 URI Too Long – These errors can occur if a request has too much data (413) or the query string is too lengthy (414). Alpha usually encounters these in the context of data retrieval rather than order placement (for example, requesting too wide a date range of historical data from Finnhub could theoretically hit payload size limits, or extremely long symbol lists in a single request might hit URI length limits). Alpha mitigates this by batching requests or limiting the scope. For trading, orders are typically small payloads, so 413/414 are rare. If they do arise (perhaps due to an unexpected bug or concatenation of too much data), Alpha will split the request (e.g., fetch data in smaller chunks) and ensure compliance with size limits.

429 Too Many Requests (Rate Limit) – Alpaca’s API and Finnhub have rate limits. A 429 error indicates Alpha has hit the allowed number of requests in a given timeframe. Alpha is designed to be rate-conscious: it avoids rapid-fire polling by using efficient updates (for example, relying on websocket streams or reasonable polling intervals for price updates) and batches non-urgent requests. If a rate limit is approached, Alpha will queue or delay further requests to stay below the threshold. In the rare event a 429 is returned, Alpha will back off and wait before retrying, and inform the user of the delay if the user is waiting for an action. For instance, if the user requests a flurry of data-intensive tasks (like fetching many stocks’ data at once), Alpha might hit Finnhub’s rate limits – it will handle this gracefully by partial completion and an explanation/wait for reset.

In summary, Alpha strives to “get it right the first time” with order submissions and queries. It uses Alpaca’s responses and error messages (which are passed through from the API) to guide corrections. Any error encountered is logged along with context in the trading journal, and Alpha uses those logs to further improve input validation in the future.

Revised Environment Configuration (Paper vs Live Trading)

In the alpaca-py library, the trading environment is selected when you instantiate the TradingClient. The paper flag determines whether the client points to the simulated (paper) endpoint or the live endpoint.

Paper mode (default): Create your client with TradingClient(api_key, secret_key, paper=True). When paper is True (the default), the client’s base_url is set to BaseURL.TRADING_PAPER (https://paper-api.alpaca.markets) and sandbox=True
GitHub
GitHub
. Be sure to use your paper Alpaca API key and secret when operating in this mode
GitHub
. This environment allows testing without risking real funds.

Live mode: To trade with real capital, call TradingClient(api_key, secret_key, paper=False). Setting paper=False switches the base_url to BaseURL.TRADING_LIVE (https://api.alpaca.markets) and sets sandbox=False
GitHub
GitHub
. Use your live Alpaca API credentials in this case. The client will then route orders to Alpaca’s production trading API.

Custom endpoints: If you need to direct the client to a proxy or different base URL, pass url_override="https://custom-endpoint" when creating the TradingClient. This overrides the default selection of BaseURL.TRADING_PAPER or BaseURL.TRADING_LIVE
GitHub
.

Because the paper parameter defaults to True, the client will connect to the paper environment if you omit it
GitHub
. Always verify that your API keys match the environment you’re using—paper keys for paper mode and live keys for live mode—to avoid authentication errors
GitHub
.