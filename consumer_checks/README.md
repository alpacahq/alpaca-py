# Consumer checks

SDK code written the way users write it, frozen against the last release, so a
change in the SDK that would break users fails here before it ships.

`make check-api-breakage` compares declared signatures and types. These checks
cover what that cannot see: what the SDK sends over the wire and what it returns
at runtime (concrete types, field values, DataFrame shapes, raised exceptions).

## Modes

| Command | What runs | Network | Fails on |
|---|---|---|---|
| `make consumer-typecheck` | mypy over `scenarios/` | No | Renamed or removed imports, parameters, attributes |
| `make consumer-replay` | Scenarios against recorded responses | No (blocked) | Any change in requests sent, output snapshot, or scenario assertions |
| `make consumer-live` | Scenarios against the paper API, current SDK | Paper API | Scenario assertions only (live data changes) |
| `make consumer-record` | Scenarios with no recording yet, against the paper API with `alpaca-py==$(cat BASELINE)` | Paper API | Writes `recordings/` |
| `make consumer-migrate` | Old-format recordings replayed with `alpaca-py==$(cat BASELINE)` | No (blocked) | Rewrites them in the current format |
| `make consumer-refresh` | Snapshots re-taken from the stored responses | No (blocked) | Rewrites snapshots after a `poetry.lock` change |
| `make consumer-coverage` | Public client methods with no recorded scenario | No | `covers` naming a method that no longer exists |
| `make consumer-surface` | Public surface new since `BASELINE` that no recorded scenario exercises | No | New parameters, request or response fields nothing exercises |
| `make consumer-surface-baseline` | Writes `surface_baseline.json` from the `BASELINE` release | No | — |

`make consumer-check` runs the typecheck and replay steps, like CI on every PR.
CI adds `--consumer-strict`, so a scenario without a recording fails there,
unless it is listed in `recording_allowlist.txt`.

Replay snapshots depend on pandas, numpy and pydantic, so your poetry env must
match `poetry.lock`, as CI's does: run `poetry install` after pulling. When a
replay fails and your versions differ from the recording's, the failure says
so first.

## The freeze rule

This only catches breaks if the scenarios and recordings are **not** edited to
match the SDK change being made. So:

- Adding a scenario (and its new recording file) is always fine.
- Changing or deleting an existing recording needs the **`sdk-breaking`** PR
  label. CI enforces this (`consumer-freeze` job).
- Scenario code is frozen too: each recording stores a hash of the scenario
  and of everything in `scenarios/` it uses (helpers, module constants, the
  `ctx.<name>` members of `Context`). Replay fails if any of that changed, so
  editing a scenario forces its recording to change, which needs the label.
  Code a scenario does not use does not affect its hash.
- Deleting or renaming a scenario fails replay while its old recording is still
  there (`recordings with no scenario`). Removing that recording needs the
  label, like any other recording change.
- A labeled PR must say in its description and release notes what breaks for
  users and how to migrate.

## When a replay fails

1. **Request differs** (`request #N differs from the recording`): the SDK now
   sends something different, such as a renamed query parameter, a different
   date or enum encoding, or a different path. Usually a bug. If it is intended
   and the API accepts it, re-record with the label.
2. **Output differs** (`SDK output differs from the recording`): a model field
   was renamed, retyped, or dropped, an enum changed, or a DataFrame changed
   shape or dtypes. If intended, refresh the snapshot with the label:
   `make consumer-replay ARGS="--consumer-update-snapshots -k <name>"`.
   A new model field alone is not a break: replay passes and warns `new model
   fields not in the snapshot yet`. Refresh the snapshot at the next baseline
   bump to start protecting it.
3. **Scenario assertion fails**: the behavior a user depends on changed.
   Requests include headers: auth header names (values are never stored, only
   the `Authorization` scheme), `Content-Type`, `Accept` and `User-Agent` (with
   version numbers masked). A switch from `APCA-API-*` headers to
   `Authorization: Bearer`, or a dropped `Content-Type`, fails here.
4. **`replay mode blocks real network access`**: the SDK no longer sends HTTP
   through `requests`. Teach `_harness.py` the new transport. That is a harness
   change, not a scenario change, and needs no label.
5. **`recording format N is older than M`**: the harness changed how it stores
   recordings. Run `make consumer-migrate` (offline, no keys): it replays the
   stored responses with the `BASELINE` release and rewrites each recording in
   the current format. It refuses scenarios edited since they were recorded;
   re-record those. Migrated recordings keep only `Content-Type` from response
   headers until they are re-recorded. The rewrite changes recordings, so the PR
   needs the label; say it is a format migration.

## Adding a scenario

Add a function to a module in `scenarios/` (or a new module):

```python
@scenario(covers=["StockHistoricalDataClient.get_stock_bars"])
def my_case(ctx: Context) -> Dict[str, Any]:
    bars = ctx.stock_data.get_stock_bars(StockBarsRequest(...))
    assert isinstance(bars, BarSet)          # what a user relies on
    return {"bars": bars, "df": bars.df}     # outputs to snapshot
```

- Use only public imports, and only API that exists in the `BASELINE` release,
  unless you set `since` (next section).
- Use fixed dates and explicit `start`/`end`. Use `ctx.unique_id("label")` for
  anything random, and `ctx.sleep()` when polling.
- Clean up paper account state (cancel orders) in a `finally`.
- Shared helpers can live in a `scenarios/_name.py` module (skipped when loading
  scenarios). They are part of the hash of every scenario that calls them.
- Record it: `make consumer-record` records every scenario that has no
  recording yet and leaves the others alone.

For behavior the API cannot be made to show on demand (429, 5xx, a non-JSON
error page), pass `stub_responses=[{"status": 429, "json": {...}}, ...]` to
`@scenario`. Those responses are served in order instead of calling the API,
in every mode, and recording needs no keys. The requests the SDK sends,
including how many times it retries, are still frozen. See
`scenarios/errors_stubbed.py`.

## API that is not released yet: `since`

A scenario for API that only exists on `master` sets the first release that
will have it: `@scenario(covers=[...], since="0.46.0")`. Until `BASELINE`
reaches that release, the scenario is recorded and refreshed with this
checkout's SDK instead of the release, so new API is protected from the PR that
adds it. `make consumer-record`, `consumer-migrate` and `consumer-refresh` run
two passes, one with the `BASELINE` release and one with the checkout, and each
pass skips the other's scenarios. When `BASELINE` reaches the release, the
baseline workflow re-records them with it; until then replay warns that they
should be. `scenarios/stock_data_pagination.py` is an example (#877).

## Keeping the checks up to date

| Change | What happens |
|---|---|
| New public method or client | CI fails (`check_coverage.py --strict`) until it has a recorded scenario, or an entry with a reason in `coverage_allowlist.txt`. Use `since` if it is not released yet. |
| New parameter, request field or response field | CI fails (`check_surface.py --strict`) until a recorded scenario passes the parameter, sets the field, or sees the response field with a value; or a pattern with a reason in `surface_allowlist.txt`. |
| Intended break | Replay fails; update the recording and add the `sdk-breaking` label (the freeze rule). |
| pandas, numpy or pydantic bump in `poetry.lock` | Replay fails and says the environment differs. Run `poetry install`, then `make consumer-refresh`. |
| Release | `.github/workflows/consumer-baseline.yaml` moves `BASELINE` to it, re-records everything, and opens a PR labeled `sdk-breaking` (a draft if a scenario failed). It can also be started by hand with a version. |
| Live data or API drift | The nightly live job opens an issue listing the failing scenarios, comments on it while it keeps failing, and closes it once it passes again. |
| A PR that changes how the SDK talks to the API (HTTP layer, auth, retries, serialization) | Add the `consumer-live` label: the live job runs on the PR's code, and again on each push while the label stays. Branches of this repository only (forks get no secrets); the result is the PR's check, no issue is opened. Runs never overlap the nightly one. |

The PR template and `CONTRIBUTING.md` repeat the first two rows for
contributors.

## Is new API exercised? The surface gate

`check_coverage.py` works per method. `check_surface.py` goes one level down,
for everything added since the `BASELINE` release:

- `_surface.py` lists the public surface as items: `client:`, `method:`,
  `param:Client.method(name)`, `request:<path>.<field>` and
  `response:<path>.<field>`. Classes are named by their public import path
  (`alpaca.data.requests.StockBarsRequest`), not their defining module, so
  moving a definition changes nothing as long as imports keep working.
- `surface_baseline.json` is that list for the `BASELINE` release. The baseline
  workflow regenerates it on each release (`make consumer-surface-baseline`).
- The gate replays every recording while `_exercised.py` watches the public
  client methods: which arguments scenarios pass, which fields they set on
  request models, and which response fields come back with a value other
  than `None`.
- New items (current minus baseline) nothing exercises fail CI, unless a
  pattern in `surface_allowlist.txt` covers them with a reason. Glob patterns
  are standing rules (Broker); exact entries must go once the item is
  exercised.

`make consumer-surface` prints the result, plus how much of the whole surface
is exercised. A response field counts only with a real value, so a field the
API fills in rarely needs a stubbed scenario or an allowlist entry. A new
endpoint behind an existing method is caught only through the parameter or
request field that selects it.

## A paper account only for these checks

Record and live modes use their own keys, `CONSUMER_TRADING_API_KEY_ID` and
`CONSUMER_TRADING_API_SECRET_KEY`, and never the `APCA_*` keys the SDK's live tests
use. Create a separate paper account for them and use it for nothing else:

- Some scenarios act on the whole account (below): they cancel every open
  order and close every position on it.
- Recordings capture the account's responses, so anything else on the account
  (orders, positions, watchlists) ends up in files that get committed.
- Two runs at once (local and the nightly job) can collide, so keep the account
  away from manual use too.

Setting the `CONSUMER_*` keys is what says the account is dedicated: there is
no separate switch, so do not put the keys of an account you use for anything
else there. Replay mode needs no keys.

## What scenarios do to the paper account

Every scenario cleans up after itself:

- `trading.limit_order_lifecycle`, `trading_positions.replace_limit_order_price`:
  a 1-share AAPL buy limit at $1.00 (never fills), replaced or canceled.
- `trading_positions.crypto_position_round_trip`: a $10 BTC/USD market buy,
  then closes exactly that quantity. It never touches other BTC holdings.
- `trading_watchlists.watchlist_lifecycle`: creates, edits and deletes its own
  `consumer-check-*` watchlist.

Account-wide, in `trading_account_wide.py`:

- `cancel_all_open_orders`: places two unfillable limit orders, then calls
  `cancel_orders()`, which cancels **every** open order on the account.
- `close_all_positions_and_cancel_orders`: buys $10 of BTC/USD, places an
  unfillable AAPL order, then calls `close_all_positions(cancel_orders=True)`,
  which closes **every** position and cancels **every** open order.
- `account_configuration_round_trip`: flips `trade_confirm_email` with
  `set_account_configurations()`, then restores the original value.

`trading_options.exercise_without_position_raises` covers
`exercise_options_position` without exercising anything: a real exercise
cannot be undone, needs market hours and settles asynchronously. It checks that
the account does not hold the contract, then that exercising it raises
`APIError`. That covers the request the SDK sends and the error users get.

Paper account ids in responses are scrubbed (`account_number`, `account_id`,
and the `id` returned by `/v2/account`), keeping UUIDs as valid UUIDs.

## What scenarios do to the Broker sandbox

Broker scenarios always construct `BrokerClient` with `sandbox=True`. Each
account is created with a synthetic identity (`consumer-check-<id>@example.com`,
555 phone, example street, tax id in the unissued 666 area) and closed before
the scenario returns. Sandbox accounts can be closed, not deleted.
`delete_account` is the deprecated name for close and is called on its own
account.

List and journal calls are filtered to an email or account id the scenario
just created. Nothing calls an unfiltered `list_accounts`, and
`get_all_accounts_positions` is not called live: that response is every
account, so `broker_events.bulk_positions_are_not_fetched_live` stubs one page.
The event streams do not end, so `broker_events.event_stream_requests` serves
one SSE event per stream. The request (path, query, `Accept: text/event-stream`)
is still the one the SDK builds.

ACH uses the public test routing number `121000248`, a fake account number, and
the owner name "Consumer Check". Journals move cash only between the two
accounts that scenario created. The rebalancing portfolio name is unique to the
run and is inactivated after the account is unsubscribed (there is no delete).
Orders are 1-share AAPL limit buys at $1, so they cannot fill.

Response fields that are personal data (`given_name`, `family_name`,
`email_address`, `tax_id`, `date_of_birth`, street address, phone, bank
numbers, and the transmitter fields on a journal) are replaced before the
recording is written. UUIDs stay valid UUIDs; other strings become `SCRUBBED`.
The account `id` is kept, because later requests use it. Later requests also
use the email and city the scenario sent, not the scrubbed response. Request
bodies are not scrubbed: replay compares them, so they must stay synthetic.

`get_cip_data_for_account_by_id` and `upload_cip_data_for_account_by_id` send
no HTTP today. Calling them records that. A later implementation that starts
calling the API changes the recording.

## Recording

`make consumer-record` and `make consumer-live` need
`CONSUMER_TRADING_API_KEY_ID` and `CONSUMER_TRADING_API_SECRET_KEY` for the paper
account, and `CONSUMER_BROKER_API_KEY` and `CONSUMER_BROKER_API_SECRET` for a
Broker sandbox (see `.env.example`). These are not the `APCA_*` or
`ALPACA_BROKER_*` keys the SDK's live tests use. Variables set in the
environment come first; otherwise they are read from the repo's `.env` (or
`CONSUMER_ENV_FILE`). The file is parsed, not executed, and only those four
variables are read. The pytest header shows where the keys came from, never
their values. A broker scenario that actually calls the sandbox fails when its
keys are missing. The preflight still exits 0 in that case, so a trading-only
re-record is not blocked; it prints that the broker keys were not found.
Stubbed broker scenarios do not need keys.

`make consumer-record` builds `.consumer-venv/` with the released SDK from
`BASELINE` and the third-party versions pinned in `poetry.lock` (what CI
installs, whatever your local env has), then records every scenario that has
no recording yet. Pass `ARGS="--consumer-rerecord -k <name>"` to record one
again: that changes its recording, so it needs the `sdk-breaking` label once it
is on `master`. The venv is rebuilt only when `BASELINE` or the locked versions
change. API key values are never stored: auth headers are recorded
by name only. Response headers are stored, except volatile or sensitive ones
(`Date`, `Set-Cookie`, encoding and length headers). Paper account identifiers
in responses (`account_number`, `account_id`) are scrubbed. Review the JSON
before committing anyway.

To move the baseline to a new release, update `BASELINE` and re-record
everything (`make consumer-record ARGS=--consumer-rerecord`) in one labeled PR.
After a lock change to pandas, numpy or pydantic, refresh the snapshots
offline instead: `cd consumer_checks && ../.consumer-venv/bin/python -m pytest .
--consumer-update-snapshots` (after `make consumer-migrate` has rebuilt the
venv). Only the snapshots change, not the recorded requests or responses.

## What is checked besides the happy path

- **`raw_data=True`** (`scenarios/raw_data.py`): one scenario per client family
  with the `ctx.raw_*` clients. Raw results are the API's JSON (short keys such
  as `t`/`o`, `class` instead of `asset_class`, money as strings), and users who
  opt in index them directly, so their shape is snapshotted too. A new key in
  a plain dict is additive, like a new model field.
- **Real error responses** (`scenarios/errors.py`): invalid keys, unknown order
  ids, rejected orders (insufficient buying power, sub-penny price) and an
  invalid time range. Each snapshots the exception and what `code` and
  `message` return, or that they raise: the data API sends no `code`, so
  `error.code` raises `KeyError`.
- **Retries and error mapping** (`scenarios/errors_stubbed.py`, stubbed): a 429
  then success, 429 until retries run out (4 requests), a 504 then success, a
  500 (not retried) and an HTML 502 (`code`/`message` raise `JSONDecodeError`).

Two typing gaps surfaced in 0.45.0: `get_crypto_snapshot` is typed as one
`Snapshot` but returns a dict by symbol, and raw `get_calendar` returns a list
of dicts while typed as `List[Calendar] | dict`.

## Coverage

`make consumer-coverage` counts a method as checked only when a scenario that
covers it has a recording, since replay skips scenarios without one. It also
shows how many have a scenario that is not recorded yet. Every method of
`TradingClient`, of `BrokerClient`, and of the market-data clients (stock,
crypto, options, news, screener, corporate actions) has a scenario. Market-data scenarios
are read only and use the feeds every paper account has: IEX for stocks and
`indicative` for options. Fixed past dates keep requests identical on replay.
Where data has to be current (option contracts expire), the scenario picks it
from an earlier response, such as the option chain, which replay serves back.

## Known gaps

- Only part of each request is exercised: the scenarios set about half the
  fields of the request classes they use. Most order types (stop, trailing,
  bracket, OCO, multi-leg) and options such as `sort`, `currency` and `asof`
  are not sent yet.
- OAuth (`oauth_token`) and `url_override` clients are not exercised.

- Streaming (websocket) clients have no scenarios yet. They would need their own
  record and replay transport, so for now cover them in live mode only.
- `BrokerClient` has a scenario for every public method. The event streams and
  `get_all_accounts_positions` are stubbed and recorded. The rest call the
  sandbox and are recorded with `make consumer-record` once
  `CONSUMER_BROKER_API_KEY` / `CONSUMER_BROKER_API_SECRET` are accepted by
  `https://broker-api.sandbox.alpaca.markets`. Until those recordings exist,
  `BrokerClient` stays in `coverage_allowlist.txt`, the broker globs stay in
  `surface_allowlist.txt`, and each unrecorded scenario stays in
  `recording_allowlist.txt` (strict replay skips those instead of failing).
  After recording, remove the scenario's line (the baseline workflow does this
  for the scenarios it records; replay fails on a stale line), then the
  `BrokerClient` allowlist line. Two fields new since BASELINE are still unused
  on purpose:
  `CreateAccountRequest.cash_interest` (the tier name is correspondent-specific;
  omitting it uses the default) and `Transfer.hold_until` (null unless the
  correspondent places a hold). Replace the broker globs with those two exact
  entries if a recording still does not set them.
