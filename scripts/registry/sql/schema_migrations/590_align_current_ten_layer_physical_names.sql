-- Align active registry rows to the current 10-layer physical naming structure.

UPDATE trading_registry
SET key = replace(key, 'MODEL_06_POSITION_PROJECTION', 'MODEL_07_POSITION_PROJECTION'),
    updated_at = NOW()
WHERE key LIKE '%MODEL_06_POSITION_PROJECTION%';

UPDATE trading_registry
SET key = replace(key, 'MODEL_07_UNDERLYING_ACTION', 'MODEL_08_UNDERLYING_ACTION'),
    updated_at = NOW()
WHERE key LIKE '%MODEL_07_UNDERLYING_ACTION%';

UPDATE trading_registry
SET key = replace(key, 'MODEL_08_OPTION_EXPRESSION', 'MODEL_09_OPTION_EXPRESSION'),
    updated_at = NOW()
WHERE key LIKE '%MODEL_08_OPTION_EXPRESSION%';

UPDATE trading_registry
SET key = replace(key, 'MODEL_09_EVENT_RISK_GOVERNOR', 'MODEL_10_EVENT_RISK_GOVERNOR'),
    updated_at = NOW()
WHERE key LIKE '%MODEL_09_EVENT_RISK_GOVERNOR%';

UPDATE trading_registry
SET key = replace(key, 'SOURCE_09_EVENT_RISK_GOVERNOR', 'SOURCE_10_EVENT_RISK_GOVERNOR'),
    updated_at = NOW()
WHERE key LIKE '%SOURCE_09_EVENT_RISK_GOVERNOR%';

UPDATE trading_registry
SET key = replace(key, 'FEATURE_08_OPTION_EXPRESSION', 'FEATURE_09_OPTION_EXPRESSION'),
    updated_at = NOW()
WHERE key LIKE '%FEATURE_08_OPTION_EXPRESSION%';

UPDATE trading_registry
SET key = replace(key, 'FEATURE_09_EVENT_RISK_GOVERNOR', 'FEATURE_10_EVENT_RISK_GOVERNOR'),
    updated_at = NOW()
WHERE key LIKE '%FEATURE_09_EVENT_RISK_GOVERNOR%';

UPDATE trading_registry
SET key = replace(key, 'LAYER_NINE_EVENT', 'LAYER_TEN_EVENT'),
    updated_at = NOW()
WHERE key LIKE '%LAYER_NINE_EVENT%';

UPDATE trading_registry
SET payload = replace(replace(replace(replace(replace(replace(replace(replace(payload,
        'model_06_position_projection', 'model_07_position_projection'),
        'model_07_underlying_action', 'model_08_underlying_action'),
        'model_08_option_expression', 'model_09_option_expression'),
        'model_09_event_risk_governor', 'model_10_event_risk_governor'),
        'source_09_event_risk_governor', 'source_10_event_risk_governor'),
        'feature_08_option_expression', 'feature_09_option_expression'),
        'feature_09_event_risk_governor', 'feature_10_event_risk_governor'),
        'layer_nine_event_', 'layer_ten_event_'),
    path = replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(path,
        'model_06_position_projection', 'model_07_position_projection'),
        'model_07_underlying_action', 'model_08_underlying_action'),
        'model_08_option_expression', 'model_09_option_expression'),
        'model_09_event_risk_governor', 'model_10_event_risk_governor'),
        'source_09_event_risk_governor', 'source_10_event_risk_governor'),
        'feature_08_option_expression', 'feature_09_option_expression'),
        'feature_09_event_risk_governor', 'feature_10_event_risk_governor'),
        '15_layer_06_position_projection.md', '16_layer_07_position_projection.md'),
        '16_layer_07_underlying_action.md', '17_layer_08_underlying_action.md'),
        '17_layer_08_trading_guidance.md', '18_layer_09_trading_guidance.md'),
    applies_to = replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(applies_to,
        'model_06_position_projection', 'model_07_position_projection'),
        'model_07_underlying_action', 'model_08_underlying_action'),
        'model_08_option_expression', 'model_09_option_expression'),
        'model_09_event_risk_governor', 'model_10_event_risk_governor'),
        'source_09_event_risk_governor', 'source_10_event_risk_governor'),
        'feature_08_option_expression', 'feature_09_option_expression'),
        'feature_09_event_risk_governor', 'feature_10_event_risk_governor'),
        'layer_06_position_projection', 'layer_07_position_projection'),
        'layer_07_underlying_action', 'layer_08_underlying_action'),
        'layer_08_option_expression', 'layer_09_option_expression'),
        'layer_09_event_risk_governor', 'layer_10_event_risk_governor'),
    note = replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(note,
        'model_06_position_projection', 'model_07_position_projection'),
        'model_07_underlying_action', 'model_08_underlying_action'),
        'model_08_option_expression', 'model_09_option_expression'),
        'model_09_event_risk_governor', 'model_10_event_risk_governor'),
        'source_09_event_risk_governor', 'source_10_event_risk_governor'),
        'feature_08_option_expression', 'feature_09_option_expression'),
        'feature_09_event_risk_governor', 'feature_10_event_risk_governor'),
        'Layer 6 PositionProjectionModel', 'Layer 7 PositionProjectionModel'),
        'Layer 7 UnderlyingActionModel', 'Layer 8 UnderlyingActionModel'),
        'Layer 8 OptionExpressionModel', 'Layer 9 OptionExpressionModel'),
        'Layer 9 EventRiskGovernor', 'Layer 10 EventRiskGovernor'),
    updated_at = NOW();

UPDATE trading_registry
SET path = replace(path, '18_layer_10_event_risk_governor.md', '19_layer_10_event_risk_governor.md'),
    updated_at = NOW()
WHERE path LIKE '%18_layer_10_event_risk_governor.md%';

UPDATE trading_registry
SET applies_to = trim(both ';' from replace(replace(replace(applies_to, ';current_physical_names', ''), 'current_physical_names;', ''), 'current_physical_names', '')),
    updated_at = NOW()
WHERE applies_to LIKE '%current_physical_names%';

UPDATE trading_registry
SET payload = replace(payload, '6_', '7_'),
    note = replace(replace(note, 'Layer 6 target holding-state projection', 'Layer 7 target holding-state projection'), 'current 6_*', 'current 7_*'),
    updated_at = NOW()
WHERE key IN (
    'POSITION_PROJECTION_VECTOR_SCORE_FAMILIES',
    'POSITION_PROJECTION_HANDOFF_SUMMARY_FIELD_FAMILIES',
    'POSITION_PROJECTION_DIAGNOSTIC_FIELD_FAMILIES'
);

UPDATE trading_registry
SET payload = replace(payload, '7_', '8_'),
    note = replace(replace(note, 'current 7_*', 'current 8_*'), 'Layer 7 direct-underlying', 'Layer 8 direct-underlying'),
    updated_at = NOW()
WHERE key IN (
    'UNDERLYING_ACTION_VECTOR_SCORE_FAMILIES',
    'UNDERLYING_ACTION_RESOLVED_FIELD_FAMILIES'
);

UPDATE trading_registry
SET payload = replace(payload, '8_', '9_'),
    note = replace(replace(note, 'current 8_*', 'current 9_*'), 'Layer 8 diagnostic', 'Layer 9 diagnostic'),
    updated_at = NOW()
WHERE key IN (
    'OPTION_EXPRESSION_VECTOR_SCORE_FAMILIES',
    'OPTION_EXPRESSION_RESOLVED_FIELD_FAMILIES',
    'OPTION_EXPRESSION_DIAGNOSTIC_FIELD_FAMILIES'
);

UPDATE trading_registry
SET payload = 'layers_01_02_six_month_panel;layers_03_10_target_symbol_six_month;layer_10_event_risk_governor_uses_source_10_event_overlay',
    note = 'Accepted dataset-unit policy inside the resident Layer 1-10 historical-modeling system service: Layers 1-2 use one six-month panel; Layers 3-10 use one selected target symbol over one six-month window. DynamicRiskPolicyModel is Layer 6; EventRiskGovernor uses current source_10/model_10 physical surfaces.',
    updated_at = NOW()
WHERE key = 'HISTORICAL_DATASET_UNIT_POLICY';

UPDATE trading_registry
SET payload = 'active_ten_layer_physical_numbering_aligned;historical_migrations_and_artifacts_unchanged;prior_evidence_refs_only',
    note = 'Active docs, code, scripts, tests, and registry rows use the current 10-layer physical numbering: model_06_dynamic_risk_policy, model_07_position_projection, model_08_underlying_action, model_09_option_expression, model_10_event_risk_governor, source_10_event_risk_governor, and feature_10_event_risk_governor. Historical migrations and old artifacts are intentionally not rewritten.',
    updated_at = NOW()
WHERE key = 'LAYER_PHYSICAL_NUMBERING_AUDIT';

UPDATE trading_registry
SET note = 'Current realtime coverage gap summary for the ten-layer stack. Layer 10 event adapters remain bounded route gaps until reviewed implementation fills them; active model/input physical tokens use the current 10-layer numbering.',
    updated_at = NOW()
WHERE key = 'EXECUTION_REALTIME_LAYER_GAP_SUMMARY';

UPDATE trading_registry
SET applies_to = 'trading-manager;scheduler;historical_training;layer_01_market_regime;layer_02_sector_context;layer_03_target_state_vector;layer_04_event_failure_risk;model_05_alpha_confidence;layer_06_dynamic_risk_policy;model_06_dynamic_risk_policy;model_07_position_projection;model_08_underlying_action;model_09_option_expression;model_10_event_risk_governor;layer_01_02_foundation_catch_up;post_model_artifact_rebuild_boundary;rolling_fold_promotion;four_one_one_split;five_year_promotion_benchmark_window',
    note = 'Manager-owned base Layer 1-10 workflow plan within the resident historical-modeling system service. Active workflow commands route directly to the current 10-layer model packages. During foundation catch-up, month-scoped workflow states expose only reusable substrate data_acquisition and feature_generation for Layers 1-3 before target-specific work; base model generation/evaluation/promotion review belong to fold-scoped model/promotion work after frozen 4+1+1 manifests exist.',
    updated_at = NOW()
WHERE key = 'MANAGER_MODEL_TRAINING_WORKFLOW_PLAN_ARTIFACT';

UPDATE trading_registry
SET applies_to = replace(applies_to, 'model_05_alpha_confidence;model_07_position_projection', 'model_05_alpha_confidence;model_06_dynamic_risk_policy;model_07_position_projection'),
    updated_at = NOW()
WHERE key = 'HISTORICAL_MODELING_SYSTEM_SERVICE_RUNTIME'
  AND applies_to NOT LIKE '%model_06_dynamic_risk_policy%';

