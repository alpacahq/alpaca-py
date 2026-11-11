#!/usr/bin/env bash
# Run consumer scenarios with the SDK each recording comes from.
#
# Two passes:
#   1. the released SDK named in BASELINE, in a venv with alpaca-py==BASELINE
#      from PyPI and the third-party versions pinned in poetry.lock;
#   2. this checkout's SDK (the poetry env), for scenarios whose `since` is
#      newer than BASELINE (API not released yet).
# Each pass skips the scenarios that belong to the other.
#
# CONSUMER_MODE picks what runs:
#   record  (default) against the paper API, writing recordings that are
#           missing (add --consumer-rerecord to redo existing ones)
#   migrate offline: upgrade recordings made with an older recording format
#   refresh offline: re-take snapshots from the stored responses, after a
#           pandas/numpy/pydantic change in poetry.lock
#   surface offline: write surface_baseline.json, the public surface of the
#           BASELINE release (one pass only)
# Pytest arguments pass through, e.g. `-k trading`.
#
# Record mode needs CONSUMER_TRADING_API_KEY_ID / CONSUMER_TRADING_API_SECRET_KEY
# for a paper account used only by these checks, in the environment or the
# repo's .env (CONSUMER_ENV_FILE=path for another file). See _dotenv.py and
# .env.example. Optional: CONSUMER_VENV=path (defaults to .consumer-venv).
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
repo="$(cd "$here/.." && pwd)"
baseline="$(tr -d '[:space:]' < "$here/BASELINE")"
venv="${CONSUMER_VENV:-$repo/.consumer-venv}"
mode="${CONSUMER_MODE:-record}"

case "$mode" in
  record) options=(--consumer-mode=record) ;;
  migrate) options=(--consumer-mode=migrate) ;;
  refresh) options=(--consumer-mode=replay --consumer-update-snapshots --consumer-match-sdk) ;;
  surface) options=() ;;
  *) echo "CONSUMER_MODE must be record, migrate, refresh or surface, not '$mode'" >&2; exit 2 ;;
esac

cd "$repo"
if [ "$mode" = "record" ]; then
  # Fail before building the venv. The tests read the keys the same way.
  poetry run python "$here/_dotenv.py"
fi
python="$(poetry run python -c 'import sys; print(sys.executable)')"
# The same third-party versions CI installs: read from poetry.lock.
pins="$(poetry run python "$here/_runtime_pins.py")"

if [ ! -x "$venv/bin/python" ]; then
  "$python" -m venv "$venv"
fi
# Reinstall only when the baseline or the pins changed, so repeat runs are
# quick and the offline modes work offline once the venv exists.
stamp="$venv/.consumer-stamp"
wanted="$(printf '%s\n' "python=$("$venv/bin/python" -c 'import sys; print(sys.version)')" "alpaca-py==$baseline" $pins)"
if [ "$(cat "$stamp" 2>/dev/null)" != "$wanted" ]; then
  "$venv/bin/python" -m pip install --quiet --upgrade pip
  # shellcheck disable=SC2086  # one pin per word
  "$venv/bin/python" -m pip install --quiet $pins
  # With dependencies, so the baseline gets anything it needs that the current
  # SDK dropped. pip keeps the pins above when they satisfy the baseline.
  "$venv/bin/python" -m pip install --quiet "alpaca-py==$baseline"
  printf '%s' "$wanted" > "$stamp"
fi

if [ "$mode" = "surface" ]; then
  # From consumer_checks/, so the repo's own `alpaca/` package is not importable.
  (cd "$here" && "$venv/bin/python" _surface.py > surface_baseline.json)
  echo "wrote consumer_checks/surface_baseline.json for alpaca-py $baseline"
  exit 0
fi

# Exit status 5 means pytest collected nothing (e.g. -k matched no scenario).
run() { "$@" || { status=$?; [ "$status" -eq 5 ] || return "$status"; }; }

echo "== pass 1: alpaca-py $baseline"
# From consumer_checks/, so the repo's own `alpaca/` package is not importable.
(cd "$here" && run "$venv/bin/python" -m pytest . "${options[@]}" "$@")
echo "== pass 2: this checkout's SDK (scenarios with a newer \`since\`)"
run poetry run pytest consumer_checks "${options[@]}" "$@"
