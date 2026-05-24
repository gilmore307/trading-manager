-- Correct C03 lifecycle policy to reason evidence plus execution review gates.

UPDATE trading_registry
SET key = 'C03_LIFECYCLE_UNDERLYING_REVIEW_POLICY',
    payload = 'underlying_first_lifecycle;options_are_expression_translation;model_underlying_stop_required;no_fixed_option_loss_stop;explicit_reason_evidence_required;respect_sector_opportunity_mix;agent_final_review_before_live_submission',
    note = 'C03 Lifecycle manages already-open positions in underlying-thesis terms. It decides hold, add, reduce, stop, exit, or take-profit from model stops, thesis invalidation, alpha, event risk, dynamic policy, position projection, and underlying action. Option contracts are expression translation owned by C04. Fixed option mark-to-market loss percentages are not ordinary lifecycle stops. C03 does not run fee, PDT, or churn formulas; every non-hold action must carry explicit reason evidence, add decisions must respect C01/M07 sector-opportunity and portfolio constraints, and live submission requires C07 agent final review.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'cfg_EXECRTC006';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
  'cfg_EXECRTC007',
  'config',
  'EXECUTION_AGENT_FINAL_REVIEW_POLICY',
  'text',
  'required_before_live_submission;applies_to_open_add_reduce_exit_stop_take_profit_roll_stock_fallback;review_reason_evidence;review_sector_mix_compliance;review_pdt_day_trade_fees_spread_context;hard_broker_or_regulatory_blocks_reject',
  'trading-execution/docs/50_runtime_components.md;trading-execution/src/trading_execution/runtime/decisions.py',
  'component_07_execution_gate;execution_order_intent;broker_order_request;agent_final_review;live_submission_gate',
  'sync_artifact',
  'C07 Execution Gate requires an approved agent final review before any live broker submission for open, add, reduce, exit, stop, take-profit, option roll, or stock fallback orders. The review consumes C02/C03/C04 reason evidence, sector/opportunity-mix compliance, and execution context such as PDT/day-trade limits, fees, spread, and transaction costs. Broker/regulatory hard blocks still reject outright.'
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
SET note = 'Execution runtime contract emitted by C03 Lifecycle for already-open position management. C03 is underlying-first: it decides hold, add, reduce, exit, stop, take-profit, or flatten-review from model-provided underlying thesis state, alpha, event risk, dynamic policy, and position projection. For the high-risk options account it does not use fixed option mark-to-market loss percentages as ordinary stops; C04 owns option expression translation. C03 emits explicit reason evidence and blocks add when C01/M07 sector-opportunity or portfolio constraints are already filled.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'art_EXECRTC005';

UPDATE trading_registry
SET note = 'Accepted concise numbered intraday execution component sequence. C01 Intake owns account/watch-target intake; C02 Entry owns underlying entry-thesis suitability; C03 Lifecycle owns underlying-first open-position lifecycle with model stops, reason evidence, and sector/opportunity add constraints; C04 owns option/underlying expression review; C07 owns the agent-reviewed live-submission gate. component_id values follow the model-aligned physical naming pattern component_01_* through component_07_*.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'cfg_EXECRTC003';
