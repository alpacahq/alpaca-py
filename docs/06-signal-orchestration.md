version: 2025-09-04
status: canonical
scope: orchestration-ops
note: "Operational commands are print/preview only; no background execution from chat."
contracts:
  inputs: {op:"schedule|health|restart|deploy|logs|import_holly_watchlist", target, params?}
  outputs: {status, ts_utc, details?}
ops:
  schedule: "configure signal runs (describe plan only)"
  health: "report heartbeat and last run (query via action-internal metrics only)"
  restart: "describe steps; do not execute"
  deploy: "describe steps; do not execute"
  logs: "summarize recent entries if action exposes them"
  import_holly_watchlist: "summarize intended import; no direct EOD scraping"
ps7_and_railway_preview:
  health: |
    # PREVIEW ONLY: show that we'd call action health, not a raw endpoint
    "orchestrator: healthy? last_run=..."
  restart: |
    # PREVIEW ONLY: show Railway commands; do not run
    "railway up" ; "railway logs --service orchestrator"
router:
  node: automation_ops
  triggers: ["orchestrate","daemon","schedule","monitor","restart","deploy","logs","HOLLY"]
  prechecks: []
tests:
  smoke:
    - "import HOLLY watchlist" -> "candidates listed with ts (preview)"
    - "restart orchestrator" -> "print commands only"
changelog:
  - 2025-09-04: mark all ops as preview-only; remove fictitious endpoints
