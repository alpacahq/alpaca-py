# Linda Bradford Raschke (LBR)'s Anti Setup Algo Trading Bot

## Overview

This is a **production-ready algorithmic trading bot** that implements **Linda Raschke's LBR 3/10 Anti setup** strategy on the **Magnificent 7** stocks (AAPL, MSFT, NVDA, GOOGL, AMZN, META, TSLA) using **AWS Lambda** for serverless execution and **[Alpaca's Trading API](https://app.alpaca.markets/account/login)** for live market data and order execution.

The bot runs automatically **every weekday at 9:30 AM ET** (market open) on Lambda, scans for valid setups using technical indicators (MACD, ADX, EMA, ATR), and executes equal-weighted rebalancing across selected symbols with **risk management via ATR-based trailing stops**.

**Note:** This is an educational implementation of Raschke's discretionary trading approach. It is not investment advice and comes with no performance guarantees.

## How It Works

```
CloudWatch (9:30 AM ET, Mon–Fri)
    ↓
Lambda Handler
    ├─ Get market clock (paper vs live)
    ├─ Build target portfolio (signal scan: LBR 3/10 + 6-rule filter)
    ├─ Fetch current account state (positions, buying power)
    ├─ Rebalance (sell excess, buy new)
    ├─ Place ATR-based trailing stop orders
    └─ Log portfolio to DynamoDB
    ↓
Alpaca's Trading API (paper or live trading)
    ├─ Market orders (regular hours)
    └─ Trailing stop-loss orders
```

### LBR Signal Logic (6 Rules)

The bot filters the Magnificent 7 through 6 sequential rules:

1. **Minimum bars** (≥31): Need sufficient price history for indicators
2. **ADX filter** (ADX ≤ 32 AND not rising): Reject strong trends (Raschke's anti-trend logic)
3. **Trend filter** (Close > EMA(20)): Price above 20-bar EMA
4. **Signal crossover** (signal line crossed zero from below in last 16 bars): MACD trend change
5. **Pullback** (MACD ≤ signal + 0.5×ATR): Wait for retracement
6. **Hook** (histogram rising): Histogram reversal confirms setup

**Selected symbols** → equal-weight allocation across portfolio.

### Risk Management

- **Entry**: Market order during regular hours (9:30 AM – 4:00 PM ET)
- **Exit**: ATR-based trailing stop
  - Stop = entry − ATR(14) × 1.5
  - Target = entry + ATR(14) × 1.5
  - Trail percentage = ATR × 1.5 / entry price

### Data & Time

- **Candles**: 120 daily bars (~6 months) for indicator calculation
- **Execution**: Every weekday 9:30 AM ET via CloudWatch
- **Paper Trading**: Default; switch to live by updating `ALPACA_PAPER_TRADE` in `serverless.yml`

## Features

- ✅ **Fully serverless**: Zero manual intervention; AWS handles scheduling
- ✅ **Single-instance execution**: Lambda reserved concurrency = 1 prevents duplicate trades / race conditions
- ✅ **Automated rebalancing**: Sell losers, buy new setups daily
- ✅ **Risk-based stops**: ATR dynamically scales stops to volatility
- ✅ **State persistence**: DynamoDB tracks portfolio across invocations
- ✅ **Secure secrets**: SSM Parameter Store holds API keys (never in code)
- ✅ **Reproducible**: `uv.lock` pinned dependencies; layer size validated

## Prerequisites

### 1. Tools

- **uv** (Python package manager): [https://astral.sh/uv](https://astral.sh/uv)
- **Node.js** v18+ (for Serverless Framework)
- **AWS CLI** v2: [https://aws.amazon.com/cli](https://aws.amazon.com/cli)

### 2. Accounts & Credentials


| Service        | What You Need          | How to Get                                                                                 |
| -------------- | ---------------------- | ------------------------------------------------------------------------------------------ |
| **Alpaca**     | API Key ID + Secret    | [Alpaca's Dashboard](https://app.alpaca.markets/account/login) → Dashboard → API Keys (use **paper** by default) |
| **AWS**        | Access Key ID + Secret | [aws.amazon.com](https://aws.amazon.com) → IAM → Users → Create programmatic access        |
| **Serverless** | Free account           | [app.serverless.com](https://app.serverless.com) → Sign up (required for v4 deploys)       |


### 3. AWS Permissions

Your IAM user needs these minimum permissions:

```
cloudformation:*
lambda:*
s3:*
iam:*
logs:*
dynamodb:*
ssm:GetParameter
events:*
```

For a quick start, attach `**AdministratorAccess**`; for production, scope to the list above.

## Installation & Deployment

> **First time?** Run through [`docs/PRE-DEPLOYMENT.md`](docs/PRE-DEPLOYMENT.md) before starting. It covers AWS account creation, IAM setup, and a pre-flight checklist that catches common failures early.

### Step 1 — Verify Local Tooling

```bash
uv --version        # Should print 0.x.x
uv python list      # Confirm 3.12.x appears
node --version      # Should be v18+
aws --version       # Should be aws-cli/2.x.x
```

### Step 2 — Install Python Dependencies

```bash
uv sync
```

This reads `pyproject.toml` and creates `.venv/` managed by `uv`. Do not manually activate it; `uv run` uses it automatically.

### Step 3 — Install Serverless Framework

```bash
npm ci
```

This installs the exact Serverless v4 version from `package-lock.json`. Do **not** use `npm install -g serverless` (bypasses lock file).

### Step 4 — Run Tests Locally

```bash
uv run pytest tests/ -v
```

All 17 tests must pass.

### Step 5 — Configure AWS Credentials

```bash
aws configure
```

When prompted:

```
AWS Access Key ID:     <your key ID>
AWS Secret Access Key: <your secret>
Default region name:   us-east-2
Default output format: json
```

Verify with:

```bash
aws sts get-caller-identity
```

### Step 6 — Store Alpaca Keys in AWS SSM

```bash
# Paper trading (default)
aws ssm put-parameter \
  --name /alpaca/ALPACA_API_KEY \
  --value "PK_PAPER_..." \
  --type SecureString

aws ssm put-parameter \
  --name /alpaca/ALPACA_SECRET_KEY \
  --value "..." \
  --type SecureString
```

**Parameter names must match exactly.** Typos here are the #1 deployment failure.

Verify:

```bash
aws ssm get-parameter --name /alpaca/ALPACA_API_KEY --with-decryption --query Parameter.Value
aws ssm get-parameter --name /alpaca/ALPACA_SECRET_KEY --with-decryption --query Parameter.Value
```

### Step 7 — Log in to Serverless Framework

```bash
npx serverless login
```

This opens a browser to authenticate. You only need to do this once per machine. Your `org` name is already set in `serverless.yml`.

### Step 8 — Build the Lambda Layer

AWS Lambda has a **250 MB unzipped size limit** on layers. This project's dependencies exceed that if built naively, so we exclude:

- `boto3`, `botocore`, `s3transfer` (~80 MB): already in Lambda Python 3.12 runtime
- `llvmlite`, `numba` (~145 MB): LLVM compiler backends pulled in as transitive dependencies; not needed at runtime

Run this before **every** `serverless deploy`:

```bash
# 1. Clear previous layer build
find layer/python -mindepth 1 -delete 2>/dev/null; echo "layer/python cleared"

# 2. Export dependencies (no hashes for clean filtering)
uv export --no-dev --no-hashes --format requirements-txt -o requirements-lambda.txt

# 3. Filter out runtime packages + heavy optionals
grep -vE "^(boto3|botocore|s3transfer|numba|llvmlite)==" requirements-lambda.txt \
  > requirements-lambda-layer.txt

# 4. Install Linux wheels
uv pip install \
  -r requirements-lambda-layer.txt \
  --target ./layer/python \
  --python-platform linux \
  --python 3.12

# 5. Clean up transitive numba/llvmlite if pip re-installed them
find layer/python/numba -mindepth 1 -delete 2>/dev/null; rmdir layer/python/numba 2>/dev/null || true
find layer/python/llvmlite -mindepth 1 -delete 2>/dev/null; rmdir layer/python/llvmlite 2>/dev/null || true

# 6. Verify size
du -sh layer/python
# Expected: ~115 MB. If ≥250 MB, steps 3–5 failed; re-check and retry.
```

### Step 9 — Deploy to AWS

```bash
npx serverless deploy
```

A successful deploy prints:

```
✔ Service deployed to stack algo-trading-alpaca-dev (103s)
functions:
  trading-bot: algo-trading-alpaca-dev-trading-bot (23 kB)
layers:
  alpacaDeps: arn:aws:lambda:us-east-2:xxxxxxxxxxxx:layer:alpacaDeps:1
```

**Function package should be < 50 kB** (just `main.py` + `alpaca_broker.py`). If several MB, `package.patterns` exclusions in `serverless.yml` are not working.

### Step 10 — Smoke Test

```bash
npx serverless invoke --function trading-bot --log
```

Check CloudWatch Logs for:

- No auth or import errors
- `"Market is closed — skipping run."` (if outside market hours)
- MACD signal scores logged for all 7 symbols (if market is open)

## Redeploying

**After code changes** (`main.py`, `alpaca_broker.py`, or `serverless.yml`):

```bash
npx serverless deploy
```

**After dependency changes** (`pyproject.toml`):

1. Rebuild the layer (Step 8 above)
2. Redeploy: `npx serverless deploy`

## Switching to Live Trading

⚠️ **WARNING: Live trading risks real money. Understand the strategy and risks before proceeding.**

### 1. Generate Live Keys

In [Alpaca's Dashboard](https://app.alpaca.markets/account/login):

- API Keys → Live → Generate key pair
- Copy **Key ID** and **Secret Key**

### 2. Update SSM

```bash
aws ssm put-parameter \
  --name /alpaca/ALPACA_API_KEY \
  --value "PK_LIVE_..." \
  --type SecureString --overwrite

aws ssm put-parameter \
  --name /alpaca/ALPACA_SECRET_KEY \
  --value "..." \
  --type SecureString --overwrite
```

### 3. Update `serverless.yml`

```yaml
provider:
  environment:
    ALPACA_PAPER_TRADE: "False"  # Change from "True"
```

### 4. Redeploy

```bash
npx serverless deploy
```

## Monitoring & Logs

### View Recent Trades

```bash
aws logs tail /aws/lambda/algo-trading-alpaca-dev-trading-bot --follow
```

### Check DynamoDB Portfolio

```bash
aws dynamodb get-item \
  --table-name algotrading-portfolios \
  --key '{"accountHash": {"S": "HASH_HERE"}}'
```

(Find `accountHash` in CloudWatch logs.)

## Architecture

For detailed system design, see:

- `**architecture/architecture-infra.mmd**`: AWS infrastructure (Lambda, DynamoDB, SSM, EventBridge)
- `**architecture/architecture-flow.mmd**`: Execution flow and algorithm logic (handler → signal scan → 6 rules → rebalance → ATR stops)

## Educational Notebook

`notebooks/ibr_algorithm_walkthrough.ipynb` walks through the LBR signal logic step-by-step with live Alpaca data — covering all 9 sections from data fetching through ATR stop placement.

**Google Colab:** Upload the notebook and set `ALPACA_API_KEY` / `ALPACA_SECRET_KEY` in Secrets (left sidebar).

**Local Jupyter:**

```bash
jupyter notebook notebooks/ibr_algorithm_walkthrough.ipynb
```

Setup instructions are included in the notebook itself.

## Project Structure

```
.
├── main.py                          # Lambda handler + core logic
├── alpaca_broker.py                 # Alpaca's Trading API wrapper
├── tests/                           # pytest suite (17 tests)
├── serverless.yml                   # Infrastructure-as-code (Lambda, DynamoDB, IAM)
├── pyproject.toml                   # Python dependencies
├── package.json / package-lock.json # Serverless Framework version
├── uv.lock                          # Pinned dependency lock file
├── docs/
│   └── PRE-DEPLOYMENT.md            # Pre-flight checklist (run before deploying)
├── architecture/
│   ├── architecture-infra.mmd       # AWS infrastructure diagram
│   └── architecture-flow.mmd        # Execution flow and algorithm logic
└── notebooks/
    └── ibr_algorithm_walkthrough.ipynb # Educational walkthrough
```

## Troubleshooting


| Error                                                        | Cause                                     | Fix                                                          |
| ------------------------------------------------------------ | ----------------------------------------- | ------------------------------------------------------------ |
| `Unzipped size must be smaller than 262144000 bytes` (layer) | `llvmlite` or `boto3` in layer            | Re-run Step 8; confirm `du -sh layer/python` ≈ 115 MB        |
| `Function code combined with layers exceeds 262144000`       | `node_modules` or `.venv` in function zip | Confirm `package.patterns` in `serverless.yml` excludes them |
| `InvalidClientTokenId`                                       | AWS credentials stale                     | `aws configure` with fresh keys                              |
| `Parameter /alpaca/... not found`                            | SSM param name typo or not created        | Re-run Step 6 with exact names                               |
| `"Market is closed"` in logs but it's 10 AM ET               | Timezone or market status logic           | Check `alpaca_broker.py` clock parsing                       |
| `"No symbol selected"` every run                             | No setups passing the 6 rules             | Review MACD/ADX/EMA logic; check indicator parameters        |


## Customization

### Change Trading Symbols

Edit `main.py`:

```python
MAGNIFICENT_7 = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA"]
# → Replace with your symbols
```

### Adjust LBR Indicator Parameters

```python
LBR_FAST   = 3    # SMA fast period
LBR_SLOW   = 10   # SMA slow period
LBR_SIGNAL = 16   # SMA signal period
ADX_PERIOD = 14
EMA_PERIOD = 20
ATR_PERIOD = 14
```

### Change Execution Schedule

Edit `serverless.yml`:

```yaml
functions:
  trading-bot:
    events:
      - schedule:
          rate: cron(30 14 ? * MON-FRI *)  # 14:30 UTC = 9:30 AM ET
          # Change to: cron(0 15 ? * MON-FRI *) for 3 PM ET, etc.
```

### Modify Stop/Target Multipliers

```python
ATR_STOP_MULTIPLIER  = 1.5   # stop = entry - (ATR_14 * 1.5)
RISK_REWARD_RATIO    = 1.0   # target = entry + (risk * 1.0)
```

## References

### Linda Raschke's LBR Strategy

- **Book**: *Street Smarts* (1996), Chapter 9
- **Website**: [lindaraschke.net](https://lindaraschke.net/)
- **Philosophy**: Anti-trend pullback setup; high win rate, small R multiples

### Alpaca's Trading API Docs

- [alpaca-py GitHub](https://github.com/alpacahq/alpaca-py)
- [Alpaca's Trading API Reference](https://alpaca.markets/docs/api-references/trading-api/)
- [Paper Trading Guide](https://alpaca.markets/docs/trading/paper-trading/)

### AWS Lambda & Serverless

- [AWS Lambda Pricing](https://aws.amazon.com/lambda/pricing/) (free tier covers this bot)
- [Serverless Framework Docs](https://www.serverless.com/framework/docs)

## Disclaimers

Alpaca and AWS are not affiliated and neither are responsible for the liabilities of the other.

Please note that this article is for general informational purposes only and is believed to be accurate as of the posting date but may be subject to change. The examples above are for illustrative purposes only.

This article is for general informational and educational purposes only. It is believed to be accurate as of the posting date but may be subject to change. All examples are for illustrative purposes only. The information presented is educational in nature and is not tailored to any individual’s financial situation. Readers are responsible for evaluating whether any strategy or approach is appropriate for their circumstances.

This article was commissioned and compensated by Alpaca. The content was developed for informational purposes and reflects an educational comparison of publicly available information. Compensation was provided for content creation and distribution.

Nothing in this article constitutes investment, legal, or tax advice, nor does it constitute a recommendation or endorsement by Alpaca. Any third-party descriptions, comparisons, platform features, statements, or images are provided by such third parties, have not been independently verified by Alpaca, and do not constitute a recommendation or endorsement by Alpaca.

Investing and trading involve risk, including the potential loss of principal. Past performance (whether actual or backtested) is not indicative of future results. No investment strategy is guaranteed to achieve its objectives. Diversification does not ensure a profit or protect against loss. Investors should consider their investment objectives and risks carefully before investing.

Past hypothetical backtest results do not guarantee future returns, and actual results may vary from the analysis.

Securities brokerage services are provided by Alpaca Securities LLC (dba "Alpaca Clearing"), member [FINRA](https://www.finra.org/?ref=alpaca.markets)/[SIPC](https://www.sipc.org/?ref=alpaca.markets), a wholly-owned subsidiary of AlpacaDB, Inc. Technology and services are offered by AlpacaDB, Inc.

Options trading is not suitable for all investors due to its inherent high risk, which can potentially result in significant losses. Please read [Characteristics and Risks of Standardized Options](https://www.theocc.com/company-information/documents-and-archives/options-disclosure-document?ref=alpaca.markets) before investing in options.

This is not an offer, solicitation of an offer, or advice to buy or sell securities or open a brokerage account in any jurisdiction where Alpaca Securities is not registered or licensed, as applicable.
