-- Register resident scheduler daemon ownership of bounded autonomous provider-stage execution.

UPDATE trading_registry
SET payload = '--execute-safe-preparation;--execute-safe-offline-stages;--execute-autonomous-provider-stages;--auto-select-next-work;--advance-month-on-complete',
    note = 'Required reviewed daemon flags for service-owned historical operation. The status surface reports missing flags before host activation or restart; provider-stage execution is bounded to autonomous historical dispatch/reconcile slices while model, broker, and storage lifecycle gates remain hard.',
    updated_at = NOW()
WHERE id = 'cfg_MHSS001';

UPDATE trading_registry
SET payload = 'PYTHONPATH=src python3 scripts/tasks/run_automation_scheduler_daemon.py --execute-safe-preparation --execute-safe-offline-stages --execute-autonomous-provider-stages --auto-select-next-work --advance-month-on-complete',
    note = 'Runs the persistent system-service-owned historical modeling scheduler daemon. The daemon audits completed/open workflow checkpoints, selects the next planned chronological month, loops over capacity-aware scheduler ticks, persists resume state, writes decision JSONL, enforces a single-instance lock, executes safe preparation/offline stages, executes bounded autonomous provider-dispatch/reconcile slices, advances the chronological month cursor after completion, and preserves model/broker/storage gates.',
    updated_at = NOW()
WHERE id = 'scr_MASD001';
