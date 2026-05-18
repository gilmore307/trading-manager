-- Finish active Layer 8/9 cleanup for registry rows missed by the first route-alignment pass.
-- Layer 8 = TradingGuidance / OptionExpression optional expression context.
-- Layer 9 = EventRiskGovernor over the Layer 7 direct-underlying/spot thesis.

UPDATE trading_registry
SET
  payload = '8_candidate_count;8_eligible_candidate_count;8_candidate_hard_filter_fail_reason_codes;8_contract_dte_fit_score;8_contract_spread_pct;8_contract_iv_rank;8_premium_risk_reason_codes;8_option_expression_reason_codes',
  note = 'Reviewed Layer 8 diagnostic field-family tokens for candidate counts, per-candidate hard-filter reason codes, contract fit attribution, premium-risk attribution, and expression reason codes. Diagnostics are not default scalar score-family rows.',
  updated_at = NOW()
WHERE id = 'cfg_OEPD001';

UPDATE trading_registry
SET
  payload = '8_resolved_expression_type;8_resolved_option_right;8_resolved_dominant_horizon;8_resolved_selected_contract_ref;8_resolved_contract_fit_score;8_resolved_expression_confidence_score;8_resolved_no_option_reason_codes;8_resolved_reason_codes',
  note = 'Reviewed current 8_* resolved expression field-family tokens for Layer 8 option-expression. They communicate chosen option expression, selected point-in-time contract reference, fit/confidence, and no-option reason codes; they are not broker order fields.',
  updated_at = NOW()
WHERE id = 'cfg_OEPR001';

UPDATE trading_registry
SET
  note = 'Narrow startup abnormality scope for Layer 9 activity bridge evidence. These are compact point-in-time detector refs only, not standalone alpha or duplicated upstream model features.',
  updated_at = NOW()
WHERE id = 'cfg_EABAS001';

UPDATE trading_registry
SET
  key = 'LAYER_NINE_REQUIRED_EVENT_FEED_ARTIFACTS',
  updated_at = NOW()
WHERE id = 'cfg_L9EVTCOV001';

UPDATE trading_registry
SET
  payload = 'PYTHONPATH=src python3 scripts/tasks/execute_layer_eight_option_feature_generation.py --start-month ${START_MONTH} --end-month ${END_MONTH}',
  path = '/root/projects/trading-manager/scripts/tasks/execute_layer_eight_option_feature_generation.py',
  updated_at = NOW()
WHERE id = 'scr_L8FEAT001';

UPDATE trading_registry
SET
  id = 'scr_L9EVTINV001',
  payload = 'PYTHONPATH=src python3 scripts/tasks/invalidate_layer_nine_event_downstream_outputs.py',
  path = 'trading-manager/scripts/tasks/invalidate_layer_nine_event_downstream_outputs.py;trading-manager/src/trading_manager_tasks/model_training_invalidation.py',
  updated_at = NOW()
WHERE id = 'scr_L8EVTINV001';

UPDATE trading_registry
SET
  id = 'scr_L9EVTBF001',
  payload = 'PYTHONPATH=src python3 scripts/tasks/prepare_layer_nine_event_feed_backfill.py',
  path = 'trading-manager/scripts/tasks/prepare_layer_nine_event_feed_backfill.py;trading-manager/src/trading_manager_tasks/event_feed_backfill.py',
  updated_at = NOW()
WHERE id = 'scr_L8EVTBF001';

UPDATE trading_registry
SET
  id = 'term_L9EVTDIS001',
  payload = 'layer_nine_event_feed_backfill_dispatch',
  updated_at = NOW()
WHERE id = 'term_L8EVTDIS001';

UPDATE trading_registry
SET
  id = 'term_L9EVTBF001',
  payload = 'layer_nine_event_feed_backfill_preparation',
  updated_at = NOW()
WHERE id = 'term_L8EVTBF001';

UPDATE trading_registry
SET
  payload = 'layer_nine_event_feed_in_window_row_coverage',
  updated_at = NOW()
WHERE id = 'term_L9EVTCOV002';

UPDATE trading_registry
SET
  payload = 'layer_nine_event_source_coverage_gate',
  updated_at = NOW()
WHERE id = 'term_L9EVTCOV001';

UPDATE trading_registry
SET
  note = REPLACE(note, 'Layer 9 gate accepted no active target chain', 'Layer 8 gate accepted no active target chain'),
  updated_at = NOW()
WHERE note LIKE '%Layer 9 gate accepted no active target chain%';
