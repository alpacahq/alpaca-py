#!/usr/bin/env python3
"""Paper API keys for record and live modes.

Only ``CONSUMER_TRADING_API_KEY_ID`` / ``CONSUMER_TRADING_API_SECRET_KEY`` are
read, never the ``APCA_*`` keys the SDK's live tests use: these checks need a
paper account of their own, because some scenarios cancel every open order and
close every position on it. They cover the Trading API and market data, which
authenticate with the same keys. Broker scenarios will get their own pair. Looks in the environment first, then in the repo's ``.env``
(or the file named by ``CONSUMER_ENV_FILE``, relative to the repo root).

The file is parsed, never executed, and only those key variables are read from
it. Key values are never printed.

  python consumer_checks/_dotenv.py   # exit 1 when no keys are found
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Mapping, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
KEY_PAIRS = (("CONSUMER_TRADING_API_KEY_ID", "CONSUMER_TRADING_API_SECRET_KEY"),)


@dataclass(frozen=True)
class Keys:
    # Values are left out of repr so tracebacks never show them.
    api_key: Optional[str] = field(repr=False)
    secret_key: Optional[str] = field(repr=False)
    source: str  # variable names and where they came from, never values


def env_file() -> Path:
    path = Path(os.environ.get("CONSUMER_ENV_FILE", ".env"))
    return path if path.is_absolute() else REPO_ROOT / path


def parse_env_file(path: Path) -> Dict[str, str]:
    """``KEY=value`` lines, with optional ``export``, quotes and ``# comments``."""
    values: Dict[str, str] = {}
    if not path.is_file():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export ") :].lstrip()
        name, _, value = line.partition("=")
        values[name.strip()] = _parse_value(value.strip())
    return values


def _parse_value(value: str) -> str:
    """Unquote ``"x"`` / ``'x'`` (anything after the closing quote, such as a
    comment, is dropped); otherwise strip a ``# comment`` preceded by a space."""
    if value[:1] in ("'", '"'):
        end = value.find(value[0], 1)
        if end != -1:
            return value[1:end]
    for marker in (" #", "\t#"):
        if marker in value:
            value = value.split(marker, 1)[0]
    return value.rstrip()


def _pair(values: Mapping[str, str], where: str) -> Optional[Keys]:
    for api_name, secret_name in KEY_PAIRS:
        if values.get(api_name) and values.get(secret_name):
            return Keys(
                values[api_name],
                values[secret_name],
                f"{api_name}/{secret_name} from {where}",
            )
    return None


def find_keys() -> Keys:
    path = env_file()
    return (
        _pair(os.environ, "the environment")
        or _pair(parse_env_file(path), str(path))
        or Keys(None, None, "none found")
    )


def main() -> int:
    keys = find_keys()
    if keys.api_key is None:
        names = " or ".join(f"{api}/{secret}" for api, secret in KEY_PAIRS)
        print(
            f"No paper keys: set {names} in the environment or in {env_file()}, "
            "for a paper account used only by these checks",
            file=sys.stderr,
        )
        return 1
    print(f"Paper keys: {keys.source}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
