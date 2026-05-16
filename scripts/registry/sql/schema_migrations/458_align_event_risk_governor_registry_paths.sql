-- Align active Layer 8 event-risk-governor registry paths after file renames.
-- Historical migrations and decision-log audit prose intentionally remain unchanged.

UPDATE trading_registry
SET path = replace(path, 'trading-manager/src/trading_manager_tasks/layer_eight_event_overlay.py', 'trading-manager/src/trading_manager_tasks/layer_eight_event_risk_governor.py'),
    note = replace(note, 'event-risk-overlay', 'event-risk-governor'),
    updated_at = NOW()
WHERE path LIKE '%trading-manager/src/trading_manager_tasks/layer_eight_event_overlay.py%'
   OR note LIKE '%event-risk-overlay%';

UPDATE trading_registry
SET applies_to = replace(applies_to, 'manager_layer_eight_event_overlay_input_materialization', 'manager_layer_eight_event_risk_governor_input_materialization'),
    updated_at = NOW()
WHERE applies_to LIKE '%manager_layer_eight_event_overlay_input_materialization%';
