# Historical Scheduler Runtime

`trading-manager` treats historical-data model training as a maintained background runtime, not a manual script sequence. The runtime goal is continuous progress with hard safety gates: provider calls require `live_call_approval_v1`, model activation requires an approving `review_decision_v1`, and broker/order/fill/account mutation remains execution-owned.

## Runtime Shape

The persistent entrypoint is:

```bash
PYTHONPATH=src python3 scripts/tasks/run_automation_scheduler_daemon.py \
  --start-month 2016-01 \
  --end-month 2016-01 \
  --execute-safe-preparation
```

The daemon repeatedly calls the capacity-aware scheduler tick, writes a checkpoint after every iteration, appends one decision JSONL row per tick, and uses a single-instance lock so two historical schedulers do not race each other.

## Durable Runtime Files

Default local runtime files live under ignored `storage/runtime/`:

| File | Contract | Purpose |
| --- | --- | --- |
| `historical_scheduler_state.json` | `manager_scheduler_daemon_state_v1` | Resume checkpoint: tick counters, last decision, last internal stage, last error, and month scope. |
| `historical_scheduler.lock` | lock file | Single-instance guard; stale locks may be replaced only when the recorded process is gone and the lock is old. |
| `historical_scheduler_decisions.jsonl` | `manager_scheduler_decision_v1` rows | Append-only operational log for scheduler decisions and gate outcomes. |

These files are runtime state, not Git artifacts. If the daemon restarts after host reboot or process failure, it resumes from the checkpoint and re-enters the scheduler work loop instead of relying on chat/session memory.

## Boot and Supervision

Reviewed host templates live in `deploy/`:

- `deploy/systemd/trading-manager-historical-scheduler.service`
- `deploy/logrotate/trading-manager-historical-scheduler`

The systemd service is designed for `Restart=always` and `WantedBy=multi-user.target`, giving process supervision and boot autostart after an operator installs/enables it. Committing the template does not install or enable the service on this host.

Example operator flow after review:

```bash
sudo cp deploy/systemd/trading-manager-historical-scheduler.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now trading-manager-historical-scheduler.service
sudo systemctl status trading-manager-historical-scheduler.service
```

Do not enable the service until the active host path, Python path, scheduler flags, resource policy, and approval-gate posture have been reviewed.

## Maintenance Guarantees

The historical scheduler runtime must provide:

- **Residency:** the daemon is a long-running process supervised by a host service manager when enabled.
- **Checkpoint/restart:** every tick updates `manager_scheduler_daemon_state_v1`; restart resumes from the latest checkpoint.
- **Single-instance safety:** the lock prevents duplicate daemon loops from racing on the same task payloads and state.
- **Observable decisions:** every tick appends one decision row for review of ready/backoff/executed/error outcomes.
- **Resource protection:** market-hours and host resource gates still run on every tick.
- **Gate preservation:** provider calls, model activation, and broker execution remain blocked unless their explicit gates are satisfied.
- **Recoverability:** runtime logs/state are local operational evidence; canonical provider/model receipts still belong in manager/storage contracts as those stages are implemented.

## Current Limit

The daemon currently repeats the implemented safe Layer 1 preparation work loop and reports `approval_gated_provider_acquisition` as the next internal stage. The next implementation increment should make the daemon dependency-aware across approval preparation, approved provider dispatch, receipt ingestion, feature generation, model training/evaluation, and promotion-review preparation.
