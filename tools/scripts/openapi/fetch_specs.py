"""Fetch pinned OpenAPI specifications from their official sources."""

import argparse
import json
import os
import tempfile
import urllib.request
from pathlib import Path

TRADING_SPEC_URL = "https://docs.alpaca.markets/openapi/trading-api.json"
MARKET_DATA_SPEC_URL = "https://docs.alpaca.markets/openapi/market-data-api.json"
BROKER_SPEC_URL = "https://docs.alpaca.markets/openapi/broker-api.json"
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SPECS = {
    "trading": (
        TRADING_SPEC_URL,
        REPOSITORY_ROOT / "tools/openapi/specs/trading-api.json",
    ),
    "market-data": (
        MARKET_DATA_SPEC_URL,
        REPOSITORY_ROOT / "tools/openapi/specs/market-data-api.json",
    ),
    "broker": (
        BROKER_SPEC_URL,
        REPOSITORY_ROOT / "tools/openapi/specs/broker-api.json",
    ),
}
# docs.alpaca.markets rejects the default urllib user agent with HTTP 403.
USER_AGENT = "alpaca-py-openapi-fetch"


def _download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def _normalize_openapi_spec(content: bytes) -> bytes:
    """Validate the document and re-serialize it so spec bumps stay reviewable.

    Alpaca publishes the specs minified; pinning them verbatim would make every
    upstream change a single-line diff. Key order is preserved so generated code
    ordering keeps following the published document.
    """
    document = json.loads(content)
    if not isinstance(document, dict):
        raise ValueError("OpenAPI specification must be a JSON object")

    version = document.get("openapi")
    if not isinstance(version, str) or not version.startswith("3."):
        raise ValueError("OpenAPI specification must use version 3.x")

    return json.dumps(document, indent=2, ensure_ascii=False).encode("utf-8") + b"\n"


def fetch_spec(url: str, destination: Path) -> bool:
    """Fetch a spec atomically, returning whether its content changed."""
    content = _normalize_openapi_spec(_download(url))

    if destination.exists() and destination.read_bytes() == content:
        return False

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=destination.parent,
            prefix=f"{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            # Assign before write/flush/fsync. delete=False means a failure
            # there would otherwise leave the partial file in the checkout.
            temporary_path = Path(temporary_file.name)
            temporary_file.write(content)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())

        temporary_path.replace(destination)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", choices=SPECS)
    args = parser.parse_args()

    url, destination = SPECS[args.spec]
    changed = fetch_spec(url, destination)
    status = "Updated" if changed else "Unchanged"
    print(f"{status}: {destination.relative_to(REPOSITORY_ROOT)}")


if __name__ == "__main__":
    main()
