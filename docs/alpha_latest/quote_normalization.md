# Quote Normalisation and TTL

When presenting quotes from the Finnhub `quote` endpoint, normalise the fields and apply a time-to-live (TTL) to ensure freshness.

## Field Mapping

The Finnhub `quote` endpoint returns an object with the following fields:

| Finnhub Field | Description                           | Normalised Field           |
|--------------|---------------------------------------|-----------------------------|
| `c`          | Current price                         | **last_price** – use this as the displayed price. |
| `d`          | Change from previous close            | **change** – the dollar change compared with the previous close. |
| `dp`         | Percent change from previous close    | **percent_change** – calculate `dp`/100 and include a `%` sign in the display. |
| `h`          | High price of the current day         | **day_high** – the intraday high used in the “Day L–H” display. |
| `l`          | Low price of the current day          | **day_low** – the intraday low used in the “Day L–H” display. |
| `o`          | Open price of the current day         | **day_open** – the opening price (not shown by default). |
| `pc`         | Previous close price                  | **prev_close** – used for computing change and percent change if needed. |
| `t`          | Timestamp of the last quote (seconds) | **provider_timestamp** – convert this Unix timestamp to ISO-8601. |

Volume is **not provided** by the `quote` endpoint. To display volume, call the Finnhub `stock/candle` endpoint with an appropriate resolution and use the final bar’s volume (`v`) field.

## Time Zone Handling

- Convert `provider_timestamp` to the time zone of the instrument’s primary exchange. If that time zone is unknown, default to the user’s time zone (America/Vancouver).
- Format the “as of” line as `HH:mm TZ` (e.g. `14:35 EDT` or `11:35 PDT`) using the 24-hour clock. Include the time zone abbreviation.

## TTL (Time to Live)

- A quote is **fresh** if the current time minus `provider_timestamp` is ≤ **10 seconds**. Use fresh quotes for default limit prices and display them without warning.
- If the quote is older than 10 seconds but less than 60 seconds, label it as “stale” and prompt the user to refresh or accept the risk.
- For quotes older than 60 seconds, do not use the price for sizing or order creation; instruct the user to fetch a new quote.

## Display Template

Use the following template for quotes:

```
SYMBOL — $last_price (±percent_change% today) · Vol volume · Day day_low–day_high · as of HH:mm TZ
```

Replace the placeholders with the normalised fields. Round prices to two decimal places and percentages to two decimal places. Display the plus or minus sign based on the sign of `percent_change`.

## Example

If Finnhub returns:

```json
{ "c": 210.50, "dp": 1.23, "h": 212.34, "l": 209.87, "t": 1695209700 }
```

and the exchange is in New York (EDT), then the normalised quote should be presented as:

```
AAPL — $210.50 (+1.23% today) · Vol n/a · Day 209.87–212.34 · as of 15:35 EDT
```

because the volume is not available and the timestamp converts to 15:35 EDT on 20 September 2025.
