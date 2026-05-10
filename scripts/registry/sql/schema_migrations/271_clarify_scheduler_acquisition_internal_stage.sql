-- Clarify that scheduler provider acquisition is an internal historical-training stage.

UPDATE trading_registry
SET applies_to = 'trading-manager;scheduler;historical_training;layer_01_market_regime;manager_scheduler_decision_v1;live_call_approval_v1',
    note = 'Runs one capacity-aware scheduler tick. It applies regular-trading-day market-hours protection and resource gates, then reports or executes safe Layer 1 task-key preparation. Historical provider acquisition is the next internal training stage and remains gated by live_call_approval_v1; the tick itself performs no provider dispatch, model activation, or broker execution.',
    updated_at = NOW()
WHERE key = 'MANAGER_AUTOMATION_SCHEDULER_RUN';

UPDATE trading_registry
SET applies_to = 'trading-manager;scheduler;task_summary;manager_request_v1;ready_signal_v1;live_call_approval_v1',
    note = 'One scheduler tick decision artifact: records allowed/backoff/executed status, explicit reason code, market-hours/resource gate state, selected work, next internal stage, required approval gate, command preview, and safety counters proving no provider/model/broker side effects during preparation.',
    updated_at = NOW()
WHERE key = 'MANAGER_SCHEDULER_DECISION_V1';
