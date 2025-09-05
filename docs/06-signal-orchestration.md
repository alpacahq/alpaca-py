version: 2025-09-03
status: canonical
scope: orchestration-ops
contracts:
  inputs: {op:"schedule|health|restart|deploy|logs|import_holly_watchlist", target, params?}
  outputs: {status, ts_utc, details?}
ops:
  schedule: "configure signal runs"
  health: "report heartbeat and last run"
  restart: "bounce services"
  deploy: "promote new build"
  logs: "fetch recent entries"
  import_holly_watchlist: "pull HOLLY day’s trades after close; de-dup; tag as candidates"
ps7_and_railway:
  health: |
    Invoke-RestMethod -Method Get -Uri "$Orchestrator/health"
  restart: |
    railway up
    railway logs --service orchestrator
router:
  node: automation_ops
  triggers: ["orchestrate","daemon","schedule","monitor","restart","deploy","logs","HOLLY"]
  prechecks: []
tests:
  smoke:
    - "import HOLLY watchlist" -> "candidates created with ts"
    - "restart orchestrator" -> "print commands only"
changelog:
  - 2025-09-03: add HOLLY watchlist import op for EOD planning
