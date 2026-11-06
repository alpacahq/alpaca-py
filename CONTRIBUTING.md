# Contributing

Thanks for helping improve Alpaca-py. By participating, you agree to follow our [Code of Conduct](./CODE_OF_CONDUCT.md).

## Choose the right channel

- **Library / SDK issues:** Bugs, feature requests, or questions specific to this SDK → [GitHub Issues](https://github.com/alpacahq/alpaca-py/issues/new/choose).
- **Security vulnerabilities:** Do not report them publicly. Follow the private reporting process in our [Security Policy](./SECURITY.md).
- **Alpaca API bugs:** Bugs in the Alpaca API itself, its OpenAPI specs, or its documentation → [alpacahq/alpaca-api](https://github.com/alpacahq/alpaca-api/issues/new/choose).
- **Community:** API feature requests, general questions, and dashboard bugs → [Alpaca Community Forum](https://forum.alpaca.markets/) or [Slack](https://alpaca.markets/slack).
- **Account help:** Questions about your account, funding, or orders → [Support request](https://alpaca.markets/support/request).
- **Outages:** Service status and incident updates → [Status page](https://status.alpaca.markets/).

Please do not include credentials, account details, request or trace IDs, or other sensitive information in an issue, discussion, pull request, test, or example.

## Contribution policy

### Contributions we welcome

Focused contributions are welcome when they improve this SDK, including:

- bug fixes and compatibility improvements;
- support for documented Alpaca API capabilities;
- focused tests and reliability improvements;
- documentation and examples; and
- maintainability improvements that preserve public behavior.

### Discuss substantial changes first

Open an issue before investing in a substantial SDK design, new dependency, broad refactor, or third-party integration. Early discussion helps confirm that the proposal fits the SDK's scope and avoids duplicated or unusable work.

Bugs in the Alpaca API itself, its OpenAPI specs, or its documentation must be fixed upstream, not patched in this SDK. Report them in [alpacahq/alpaca-api](https://github.com/alpacahq/alpaca-api/issues/new/choose). API feature requests, general questions, and dashboard bugs belong on the [Alpaca Community Forum](https://forum.alpaca.markets/) or [Slack](https://alpaca.markets/slack). Contributions that add support for already documented API capabilities are welcome after the SDK design is agreed with maintainers.

### Out of scope

This repository does not accept:

- trading strategies, algorithm design, or investment advice;
- bugs in the Alpaca API, its OpenAPI specs, or docs.alpaca.markets;
- API feature requests, dashboard bugs, or outage reports;
- questions that aren't about this SDK, including questions about your account, funding, or orders;
- credentials, private account data, request or trace IDs, or other secrets;
- referral links or promotional content; or
- unapproved integrations with third-party products or services.

Contributions that add or promote third-party products or services, including provider-specific clients, API calls, hosted endpoints, referral links, or promotional content, require prior written approval from Alpaca before implementation. Open an issue describing the technical scope; repository maintainers will coordinate the necessary internal review and confirm whether the proposal may proceed. Contributors do not need to identify or contact internal approvers.

Using an ordinary open-source dependency or improving generic interoperability does not by itself make a contribution a provider-specific integration. Maintainers will explain when a proposal falls outside this policy. A pull request that proceeds without the required approval may be closed as out of scope, so open an issue first if you are unsure whether a proposal qualifies.

## License and contribution terms

The project is licensed under the [Apache License 2.0](./LICENSE). Subject to its full terms, the license permits use, reproduction, modification, and distribution of the software. It does not grant permission to use Alpaca trade names, trademarks, service marks, or product names except as described in the license.

Unless you explicitly state otherwise, a contribution intentionally submitted for inclusion in this project is provided under Apache-2.0 without additional terms, as described in Section 5 of the license. This project does not currently require a separate Contributor License Agreement (CLA) or Developer Certificate of Origin (DCO) sign-off.

## Contribution workflow

1. Search existing issues and pull requests.
2. Open an issue first for work described under [Discuss substantial changes first](#discuss-substantial-changes-first).
3. Fork the repository and create a focused branch.
4. Make the change in hand-written source files.
5. Add focused tests for new or changed behavior and update relevant documentation.
6. Run the relevant checks listed below.
7. Open a focused pull request, explain why the change is needed, and respond to review feedback.

Use clear, descriptive commit messages and pull request titles. Conventional Commits are not required, and contributors do not need to squash commits before opening a pull request. Maintainers use GitHub's squash-merge workflow for the final merge.

## Prerequisites

- Python 3.11 or newer, as declared in [`pyproject.toml`](./pyproject.toml).
- [Poetry](https://python-poetry.org/) for dependency and environment management.
- `make` for the repository's documented convenience targets.

## Setup and checks

Install the project and its development dependencies, then install the repository's pre-commit hooks:

```bash
poetry install
poetry run pre-commit install
```

Run the standard checks from the repository root:

```bash
make lint
make test
make generate
```

Format changed SDK and test files with Black before running the lint check:

```bash
poetry run black alpaca/ tests/
```

`make generate` validates the Sphinx HTML build and doctests with warnings treated as errors. It does not generate committed SDK source. There is no numeric coverage threshold, but changed behavior must have focused tests.

## Testing and financial safety

- Default repository tests and CI must never place live orders or depend on Alpaca credentials. They must be deterministic and use mocks, fakes, or synthetic fixtures for API behavior.
- Opt-in live probes under [`tests/live`](./tests/live) require `--run-live` or `ALPACA_RUN_LIVE=1`. Current probes are read-only and default to Trading paper and Broker sandbox.
- Future mutative live probes must use the `live_mutative` marker, require `--allow-mutative`, and never target Trading live or Broker production.
- Runnable trading examples must use paper trading by default and require an explicit user choice before targeting live trading.
- Real credentials, account identifiers, account data, and production payloads must never appear in tests, fixtures, examples, or committed logs and artifacts. Remove request and trace IDs from public or committed material; share private diagnostics only through Alpaca Support channels when needed.

## Coding Guidelines

### Formatting

This repository uses [Black](https://github.com/psf/black) as its formatter and style enforcer:

```bash
poetry run black alpaca/ tests/
```

Match the surrounding style in files outside Black's configured scope. The repository does not enforce `isort` as a separate check.

### Models

We use [Pydantic](https://docs.pydantic.dev/) for response models and request objects. New response models should extend `alpaca.common.models.ValidateBaseModel` and add Pydantic validation when needed so model instances remain in a consistent state.

New request models, such as `GetNewThingRequest`, should extend `alpaca.common.requests.NonEmptyRequest`. It extends `ValidateBaseModel` and provides `to_request_fields`, which omits unset values and converts fields into safe HTTP request values.

### Request methods

Request methods follow a simple formula. For example, the Trading API method `remove_asset_from_watchlist_by_id` calls `DELETE /v2/watchlists/{watchlist_id}/{symbol}`.

1. Every URL parameter becomes a full method parameter. This example has `watchlist_id` and `symbol`.
2. Non-path request parameters should use a dedicated class that extends `alpaca.common.requests.NonEmptyRequest`. This includes query parameters for GET requests and payload fields for POST, PATCH, PUT, or DELETE requests. The request object centralizes validation and lets future optional fields be added without changing the method signature. If this DELETE endpoint accepted a payload, its final method parameter would use a request type such as `RemoveAssetFromWatchlistRequest`.
3. Use an obvious method name where possible, such as `create_order` or `get_clock`. For endpoints with multiple URL parameters, especially in the Broker module, use one of these patterns: `{verb}_{noun}_by_{value}`, `{verb}_{noun1}_{preposition}_{noun2}`, or `{verb}_{noun1}_for_{noun2}_by_{value}`.

For the example, use the semantic verb `remove`, identify asset and watchlist as the nouns, then add `by_id` because `watchlist_id` selects the watchlist:

```python
def remove_asset_from_watchlist_by_id(
    self, watchlist_id: Union[UUID, str], symbol: str
) -> Union[Watchlist, RawData]:
```

Apply these conventions to new methods. Existing public names must go through compatibility review and the documented deprecation process before they are renamed.

### Deprecations

Deprecate a method or function with `typing_extensions.deprecated` (PEP 702) rather than a manual `warnings.warn` call. The decorator emits the runtime `DeprecationWarning`, attributed to the caller's line. It also lets tools flag calls before the code runs: Pylance shows them struck through, mypy reports them with `--enable-error-code deprecated`, and pyright reports them when `reportDeprecated` is enabled. Import it under a private name so `from alpaca.<module> import *` doesn't re-export it, and add a `.. deprecated:: <version>` directive to the docstring so the API reference shows it.

```python
from typing_extensions import deprecated as _deprecated

@_deprecated("old_method is deprecated and will be removed in a future version. Please use `new_method` instead")
def old_method(self) -> None:
    """
    .. deprecated:: 0.45.0
        Please use `new_method` instead.
    """
```

`@deprecated` does not apply to enum members. To deprecate one, give the enum `alpaca._deprecating_enum.DeprecatingEnumMeta` as its metaclass and pass a `deprecations={member_name: message}` mapping, as `ActivityType` in `alpaca/trading/enums.py` does.

To deprecate a model field, use Pydantic's `Field(deprecated="...")` and keep the field's existing type and default. Pydantic warns when the field is read and stays silent during parsing and serialization, as `Asset.easy_to_borrow` in `alpaca/trading/models.py` does.

## Checking backward compatibility

Before merging changes that touch the public SDK surface, compare this branch against a
published `alpaca-py` release:

```shell
# Latest version on PyPI (quiet: breakings + summary only)
make check-api-breakage

# Explicit baseline (recommended when reviewing a known release)
make check-api-breakage AGAINST=0.43.5

# Full progress + AexPy view + additive enum/model lists
make check-api-breakage VERBOSE=1

# Keep AexPy / contract JSON artifacts for inspection
make check-api-breakage AGAINST=0.43.5 WORKDIR=/tmp/aexpy-alpaca

# Baseline against a fetched remote ref (e.g. origin/master) instead of a release
make check-api-breakage BASELINE_REF=origin/master WORKDIR=/tmp/aexpy-alpaca
```

The target runs `tools/scripts/compare_api_breakage.py`, which:

1. Builds a wheel from the current tree and obtains the baseline wheel, downloaded
   from PyPI (`--against`), or built from a git ref in a throwaway worktree and cached
   under the workdir by commit SHA (`--baseline-ref`)
2. Runs [AexPy](https://github.com/StardustDL/aexpy) for API-level removals and
   signature changes. AexPy ranks a new optional parameter on a method as breaking
   because a subclass override with the old signature would reject it; callers are
   unaffected, so the script counts those as compatible and lists them under
   `VERBOSE=1`
3. Snapshots public enum membership (`name -> value`) and public Pydantic model field
   contracts (type, requiredness, aliases), then reports removals and value/contract
   changes as breaking
4. Compares public callable return annotations when AexPy left the resolved return
   type empty. A resolved change AexPy ranked compatible is checked again only for
   `dict` / `Mapping` / `MutableMapping` keys and for a dropped `RawData` or
   `List[RawData]` member: AexPy treats every generic argument as covariant, so
   `Mapping[Base, V]` -> `Mapping[Sub, V]` would otherwise pass even though
   `result[base_key]` no longer type-checks. Equivalent spellings
   (`List` / `list`, reordered unions, `Optional[X]` / `X | None`) are ignored.
   A narrower return, such as dropping `| None` or returning a subclass
   (`Account` -> `AccountExtended`, also inside `List[...]`), does not fail the
   check. Neither does a `None` return that gains a value: type checkers reject
   using a `None` result, so callers could only discard it.
   These compatible changes are listed under `VERBOSE=1`. Dropping `RawData`
   (`dict[str, Any]`) or `List[RawData]` (`list[dict[str, Any]]`) is breaking, also
   inside a generic such as `Iterator[...]` and when AexPy ranked the change
   compatible, because that means `raw_data=True` stopped being honored. Any other
   change to an existing annotation is breaking.

The Makefile target is quiet by default. Useful flags on the script itself:

| Flag | Effect |
| --- | --- |
| `--against VERSION` | Baseline PyPI version (default: latest) |
| `--baseline-ref GITREF` | Baseline a git ref (e.g. `origin/master`) instead of a release; mutually exclusive with `--against` |
| `--workdir DIR` | Persist wheels and JSON reports (and cache the `--baseline-ref` wheel) |
| `--verbose` | Progress, full AexPy view, additive enum/model changes (Makefile: `VERBOSE=1`) |
| `--fail-on-breaking` | Exit `1` when breakings are reported (Makefile always passes this) |
| `--fail-on-unknown` | Also fail on AexPy "unknown" ranks (mostly alias retargets) |
| `--skip-contracts` | Skip enum/model contract snapshots; AexPy only |

AexPy alone can report noisy `Change alias` findings when a type moves between modules
while remaining importable from the same public path. Treat the enum and model contract
section as the practical backward-compatibility gate for those migrations.

#### Iterating against a git ref

`--baseline-ref` (Makefile `BASELINE_REF=`) builds the baseline wheel from a git ref
in a detached worktree, so you can diff against unreleased code. Pair it with a
persistent `WORKDIR`: the baseline wheel is cached by the ref's commit SHA and reused
across reruns, so only the current-tree wheel rebuilds each iteration (and the cache
refreshes automatically when the ref advances to a new commit).

Fetch first (`git fetch origin`) and baseline the remote-tracking ref. A stale local
`master` makes `git merge-base` land on the old tip, so upstream API changes in
between are reported as this branch's breakages. Fork contributors should fetch
`upstream` and use `upstream/master` in place of `origin/master`.

```shell
# Everything on your branch vs the fetched default branch
make check-api-breakage BASELINE_REF=origin/master WORKDIR=/tmp/aexpy-alpaca

# Only what the branch adds on top of the fetched default branch: baseline the
# merge-base so shared history is excluded and you see just this branch's new breakages
make check-api-breakage BASELINE_REF=$(git merge-base origin/master HEAD) WORKDIR=/tmp/aexpy-alpaca
```
