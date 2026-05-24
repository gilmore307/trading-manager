-- Register C03 as underlying-first position lifecycle with churn/cost controls.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
  'cfg_EXECRTC006',
  'config',
  'C03_LIFECYCLE_UNDERLYING_COST_POLICY',
  'text',
  'underlying_first_lifecycle;options_are_expression_translation;model_underlying_stop_required;no_fixed_option_loss_stop;hard_risk_bypasses_churn_guards;noncritical_add_reduce_cost_aware',
  'trading-execution/docs/50_runtime_components.md;trading-execution/docs/05_decision.md;trading-execution/src/trading_execution/runtime/decisions.py',
  'component_03_lifecycle;position_lifecycle_decision;component_04_option_review;component_06_order_intent;model_04_event_failure_risk;model_05_alpha_confidence;model_06_dynamic_risk_policy;model_07_position_projection;model_08_underlying_action',
  'sync_artifact',
  'C03 Lifecycle manages already-open positions in underlying-thesis terms. It decides hold, add, reduce, stop, exit, or take-profit from model stops, thesis invalidation, alpha, event risk, dynamic policy, position projection, and underlying action. Option contracts are expression translation owned by C04. Fixed option mark-to-market loss percentages are not ordinary lifecycle stops; non-critical add/reduce churn is dampened by same-day round-trip, PDT, minimum-hold, churn, and transaction-cost/fee-drag guards while hard risk exits can bypass those guards.'
)
ON CONFLICT (id) DO UPDATE SET
    kind = EXCLUDED.kind,
    key = EXCLUDED.key,
    payload_format = EXCLUDED.payload_format,
    payload = EXCLUDED.payload,
    path = EXCLUDED.path,
    applies_to = EXCLUDED.applies_to,
    artifact_sync_policy = EXCLUDED.artifact_sync_policy,
    note = EXCLUDED.note,
    updated_at = CURRENT_TIMESTAMP;

UPDATE trading_registry
SET note = 'Execution runtime contract emitted by C03 Lifecycle for already-open position management. C03 is underlying-first: it decides hold, add, reduce, exit, stop, take-profit, or flatten-review from model-provided underlying thesis state, alpha, event risk, dynamic policy, and position projection. For the high-risk options account it does not use fixed option mark-to-market loss percentages as ordinary stops; C04 owns option expression translation. Non-critical add/reduce churn is dampened by day-trade, minimum-hold, churn, and transaction-cost guards.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'art_EXECRTC005';

UPDATE trading_registry
SET note = 'Accepted concise numbered intraday execution component sequence. C01 Intake owns account/watch-target intake; C02 Entry owns underlying entry-thesis suitability; C03 Lifecycle owns underlying-first open-position lifecycle with model stops and churn/cost controls; C04 owns option/underlying expression review; downstream failure review, order intent, and execution gates own their separate boundaries. component_id values follow the model-aligned physical naming pattern component_01_* through component_07_*.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'cfg_EXECRTC003';
