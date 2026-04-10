# Pre-Deployment Checklist

Complete every item below **before** running any deploy command from the project `README.md`.
Each section maps to a real failure mode encountered during deployment.

---

## What gets provisioned automatically

You do **not** need to set up Lambda, DynamoDB, S3, CloudFormation, or CloudWatch manually in the AWS Console. Serverless Framework creates all of them automatically when you run `serverless deploy`.

| Resource | How it's created | Defined in |
|----------|-----------------|------------|
| **Lambda function** `trading-bot` | CloudFormation | `serverless.yml` functions block |
| **DynamoDB table** `algotrading-portfolios` | CloudFormation | `serverless.yml` resources block |
| **Lambda layer** `alpacaDeps` (Python dependencies) | CloudFormation | `serverless.yml` layers block |
| **CloudWatch cron** (9:30 AM ET, Mon–Fri) | CloudFormation | `serverless.yml` schedule event |
| **IAM execution role** for Lambda | CloudFormation | `serverless.yml` iamRoleStatements |
| **S3 bucket** for deployment artifacts | Serverless Framework (automatic) | no config needed |
| **CloudWatch Log Group** for Lambda logs | AWS Lambda (automatic) | created on first invocation |

The only things you must set up manually are:
- **AWS CLI credentials** — so Serverless Framework can talk to your AWS account (Section 2 below)
- **Serverless Framework account** — required by v4 to authenticate deploys (Section 6 below)
- **SSM parameters** for your Alpaca API keys — so the Lambda can read them at runtime (Section 3 below)

---

## 1. Local tooling

| # | Check | Command |
|---|-------|---------|
| 1.1 | uv is installed | `uv --version` → should print `0.x.x` |
| 1.2 | Python 3.12 is available to uv | `uv python list` → confirm `3.12.x` appears |
| 1.3 | Node.js is installed (required by Serverless) | `node --version` → `v18` or later |
| 1.4 | npm is installed | `npm --version` |
| 1.5 | AWS CLI is installed | `aws --version` → `aws-cli/2.x.x` |

---

## 2. AWS account and credentials setup

### 2a. Create an AWS account (if you don't have one)

Sign up at [aws.amazon.com](https://aws.amazon.com). The free tier covers everything this bot uses.

### 2b. Create an IAM user with programmatic access

In the AWS Console:

1. Go to **IAM → Users → Create user**
2. Attach the policy **`AdministratorAccess`** (sufficient for a personal account; see minimum permissions below if you prefer a scoped policy)
3. Go to the user → **Security credentials → Create access key** → select **"CLI"**
4. Copy the **Access Key ID** and **Secret Access Key** — the secret is only shown once

### 2c. Configure the AWS CLI

```bash
aws configure
```

Enter when prompted:

```
AWS Access Key ID:     <your key ID>
AWS Secret Access Key: <your secret>
Default region name:   us-east-2
Default output format: json
```

### 2d. Verify

```bash
aws sts get-caller-identity
```

Should return your account ID and user ARN with no errors.

> **If you see `InvalidClientTokenId`:** your credentials are missing or stale. Re-run `aws configure` and paste fresh key values. This error will also block `serverless deploy`.

### 2e. Checklist

| # | Check | Command |
|---|-------|---------|
| 2.1 | AWS CLI is authenticated | `aws sts get-caller-identity` → prints your account ID |
| 2.2 | Active region is `us-east-2` | `aws configure get region` → `us-east-2` |
| 2.3 | Your IAM identity can deploy CloudFormation | Needs `cloudformation:*`, `lambda:*`, `iam:*`, `s3:*`, `logs:*`, `ssm:GetParameter`, `dynamodb:*` |
| 2.4 | Your IAM identity can write SSM SecureString | `aws ssm put-parameter --name /test/check --value x --type SecureString && aws ssm delete-parameter --name /test/check` |

> **Minimum IAM permissions (if not using AdministratorAccess):**
>
> | Service | Why needed |
> |---------|-----------|
> | `cloudformation:*` | Serverless Framework deploys via CloudFormation |
> | `lambda:*` | Create/update the trading-bot function |
> | `s3:*` | Serverless uploads the deployment package to S3 |
> | `iam:*` | Serverless creates the Lambda execution role |
> | `logs:*` | CloudWatch Logs for the Lambda |
> | `dynamodb:*` | Create the `algotrading-portfolios` table |
> | `ssm:GetParameter` | Lambda reads Alpaca keys at runtime |
> | `events:*` | CloudWatch EventBridge cron schedule |
>
> If you are in an organisation account, confirm with your admin that CloudFormation stack creation is not blocked by an SCP.

---

## 3. Alpaca API keys

| # | Check | How |
|---|-------|-----|
| 3.1 | You have an Alpaca account | Sign up at alpaca.markets |
| 3.2 | Paper trading keys are generated | Dashboard → API Keys → Paper → generate key pair |
| 3.3 | Keys are stored in SSM under the exact parameter names below | See Step 6 in `README.md` |

Required SSM parameter names — these must match **exactly** (case-sensitive). `serverless.yml` references them by name and the deploy will fail if they differ:

```
/alpaca/ALPACA_API_KEY
/alpaca/ALPACA_SECRET_KEY
```

Verify after storing:

```bash
aws ssm get-parameter --name /alpaca/ALPACA_API_KEY --with-decryption --query Parameter.Value
aws ssm get-parameter --name /alpaca/ALPACA_SECRET_KEY --with-decryption --query Parameter.Value
```

Both should return your key values, not an error.

---

## 4. Repository state

| # | Check | Command |
|---|-------|---------|
| 4.1 | No hardcoded API keys or secrets | `grep -rn "ALPACA_API_KEY\s*=\s*[\"'][A-Z0-9]" .` → no output |
| 4.2 | `uv.lock` is committed | `git status uv.lock` → `nothing to commit` |
| 4.3 | `layer/python/` is empty or does not exist (clean build) | `ls layer/python` → empty or not found is correct |
| 4.4 | `package.json` and `package-lock.json` are committed | `git status package*.json` → nothing to commit |
| 4.5 | `node_modules/` is not committed | `git ls-files node_modules` → no output |

---

## 5. Python environment

| # | Check | Command |
|---|-------|---------|
| 5.1 | `uv sync` completes without errors | `uv sync` |
| 5.2 | All tests pass locally | `uv run pytest tests/ -v` |
| 5.3 | No import errors in main modules | `uv run python -c "import main; import alpaca_broker"` → no output |

All 17 tests must pass before deploying.

> **Do not activate a virtual environment manually.** `uv` manages `.venv` internally. All commands use `uv run` which resolves the environment automatically.

---

## 6. Serverless Framework

| # | Check | Command |
|---|-------|---------|
| 6.1 | `npm ci` completes cleanly | `npm ci` (uses pinned `package-lock.json`) |
| 6.2 | Serverless version matches `package.json` | `npx serverless --version` → should print `4.x.x` |
| 6.3 | You have a free Serverless account | Sign up at [app.serverless.com](https://app.serverless.com) if you don't have one |
| 6.4 | You are logged in to Serverless Framework | `npx serverless login` → opens browser to authenticate (once per machine) |
| 6.5 | Serverless can resolve SSM parameters | `npx serverless print` → config prints with no `${ssm:...}` placeholders remaining |

> **Serverless Framework v4 requires authentication.** Without a logged-in session, `serverless deploy` will stall waiting for login. The `org` and `app` fields in `serverless.yml` link this service to your dashboard at [app.serverless.com](https://app.serverless.com).

> **`npx serverless print` is a free dry-run.** It validates `serverless.yml` and resolves all SSM variables before any infrastructure is touched. If your SSM parameters from Section 3 are missing or misnamed, this command will catch it here.

> **Use `npm ci`, not `npm install -g serverless`.** `npm ci` installs the exact pinned version from `package-lock.json`. A global install picks up whatever the latest version is, which may behave differently.

---

## 7. Lambda layer build

AWS Lambda enforces a **250 MB unzipped size limit** on layers. This project's dependency tree exceeds that limit if built naively. Two categories of packages must be excluded:

| Package | Size | Why excluded |
|---------|------|-------------|
| `boto3`, `botocore`, `s3transfer` | ~80 MB | Pre-installed in the Lambda Python 3.12 runtime — bundling them is redundant |
| `llvmlite` | 128 MB | LLVM compiler backend used by `numba` for optional JIT — not needed at runtime |
| `numba` | 17 MB | Pulled in as a transitive dependency — not needed at runtime |

After following the layer build steps in `README.md` (Step 8), verify:

```bash
du -sh layer/python
```

Expected: **~115 MB**. If it reads 250 MB or more, `llvmlite`/`numba` were not removed — repeat the cleanup steps.

| # | Check | Command |
|---|-------|---------|
| 7.1 | Internet access available | `curl -s https://pypi.org` → any response |
| 7.2 | At least 500 MB free disk space | `df -h .` → check `Avail` column |
| 7.3 | No manually activated venv interfering | Run `deactivate` if a venv prompt is visible in your shell |
| 7.4 | Layer size is under 250 MB after build | `du -sh layer/python` → ~115 MB |

---

## 8. Live trading gate (skip if staying on paper)

Only relevant when you intend to switch `ALPACA_PAPER_TRADE` to `"False"`.

| # | Check |
|---|-------|
| 8.1 | Live trading keys are provisioned in your Alpaca account (requires identity verification) |
| 8.2 | You have reviewed the ATR-based stop parameters (`ATR_STOP_MULTIPLIER` and `RISK_REWARD_RATIO` in `main.py`) and accept the risk |
| 8.3 | You have tested the full paper flow and confirmed at least one successful trade cycle in CloudWatch Logs |
| 8.4 | You understand the Lambda fires every weekday at 9:30 AM ET and will place real orders automatically |

---

## Quick pre-flight sequence

Run these five commands in order. If all pass, you are ready to deploy (see `README.md` Step 9):

```bash
# 1. Confirm AWS identity and region
aws sts get-caller-identity
aws configure get region

# 2. Confirm SSM keys are in place
aws ssm get-parameter --name /alpaca/ALPACA_API_KEY --with-decryption --query Parameter.Value
aws ssm get-parameter --name /alpaca/ALPACA_SECRET_KEY --with-decryption --query Parameter.Value

# 3. Run all tests
uv run pytest tests/ -v

# 4. Install Serverless and log in
npm ci && npx serverless login

# 5. Dry-run config resolution
npx serverless print
```

All five must succeed with no errors before proceeding to deploy.
