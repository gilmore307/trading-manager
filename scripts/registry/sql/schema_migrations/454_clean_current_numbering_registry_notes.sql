-- Clean remaining current-version registry notes/payloads after the physical
-- current-table/code migration. Historical migration history and old artifacts
-- are intentionally left unchanged.

UPDATE trading_registry
SET payload = 'base_unadjusted_diagnostic_only;final_adjusted_layer_5_facing',
    note = 'Conceptual Layer 4 output-tier policy: base/unadjusted alpha from Layer 1/2/3 is diagnostic-only, while final adjusted alpha_confidence_vector is the default downstream output for PositionProjectionModel.',
    updated_at = NOW()
WHERE key = 'ALPHA_CONFIDENCE_VECTOR_OUTPUT_TIER_POLICY';

UPDATE trading_registry
SET note = 'Current gap summary for realtime coverage after the conceptual Layers 1-8 matrix: proxy/native macro-market routes, event adapters, broker/account state, restriction/account state, and ThetaData terminal dependency remain explicit.',
    updated_at = NOW()
WHERE key = 'EXECUTION_REALTIME_LAYER_GAP_SUMMARY';

UPDATE trading_registry
SET note = 'Formal workflow progression is segmented by dataset unit: Layers 1-2 use one six-month panel; Layers 3-7 run one selected target symbol over one six-month unit; conceptual Layer 8 EventRiskGovernor is a separate event-risk overlay.',
    updated_at = NOW()
WHERE key = 'MODEL_WORKFLOW_SEGMENTED_LAYER_PROGRESSION_POLICY';

UPDATE trading_registry
SET payload = 'layer_07_after_underlying_action;uses_underlying_action_plan;uses_option_chain_context;no_broker_mutation',
    note = 'Layer policy for OptionExpressionModel: option expression is conceptual Layer 7, consumes conceptual Layer 6 underlying path assumptions plus option-chain context, and remains offline without broker mutation.',
    updated_at = NOW()
WHERE key = 'OPTION_EXPRESSION_MODEL_LAYER_POLICY';

UPDATE trading_registry
SET payload = 'layers_01_02_six_month_panel;layers_03_07_target_symbol_six_month;layer_08_event_risk_governor_six_month_overlay',
    note = 'Accepted dataset-unit policy: Layers 1-2 use one six-month panel; Layers 3-7 use one selected target symbol over one six-month window; conceptual Layer 8 EventRiskGovernor is a separate event-risk overlay.',
    updated_at = NOW()
WHERE key = 'HISTORICAL_DATASET_UNIT_POLICY';

UPDATE trading_registry
SET key = 'LAYERS_FOUR_TO_SEVEN_DATABASE_OFFLINE_WORKFLOW',
    payload = 'layers_04_05_06_07_database_safe_offline_workflow',
    note = 'Manager-safe offline workflow for conceptual Layers 4-7 after upstream Layer 3 completes. Generation/evaluation/review stages may run without provider approval because provider_calls=0, activation=false, broker_execution=false, and promotion review remains deferred unless separately approved.',
    updated_at = NOW()
WHERE key = 'LAYERS_FIVE_TO_SEVEN_DATABASE_OFFLINE_WORKFLOW'
  AND NOT EXISTS (SELECT 1 FROM trading_registry WHERE key = 'LAYERS_FOUR_TO_SEVEN_DATABASE_OFFLINE_WORKFLOW');

UPDATE trading_registry
SET key = 'FOLD_SCOPED_LAYER_08_EVENT_RISK_GOVERNOR_INPUTS',
    path = replace(path, 'layer_eight_event_overlay.py', 'layer_eight_event_risk_governor.py'),
    note = 'Layer 8 event-risk-governor materialization accepts six-month folds, prepares detector task keys per symbol-month, and writes one fold-scoped source_08 task key for the event index.',
    updated_at = NOW()
WHERE key = 'FOLD_SCOPED_LAYER_04_EVENT_OVERLAY_INPUTS'
  AND NOT EXISTS (SELECT 1 FROM trading_registry WHERE key = 'FOLD_SCOPED_LAYER_08_EVENT_RISK_GOVERNOR_INPUTS');

UPDATE trading_registry
SET note = 'Component completion receipt proving Layer 7 feature generation is a reviewed no-op when the Layer 7 gate accepted no active target chain and therefore no source_05/feature_07 rows are required before deterministic no-option model generation.',
    updated_at = NOW()
WHERE key = 'LAYER_07_OPTION_EXPRESSION_FEATURE_NO_PROVIDER_SKIP_RECEIPT';

UPDATE trading_registry
SET payload = replace(
        replace(
            replace(
                replace(payload, '8_candidate_', '7_candidate_'),
                '8_eligible_', '7_eligible_'
            ),
            '8_contract_', '7_contract_'
        ),
        '8_premium_', '7_premium_'
    ),
    note = 'Reviewed Layer 7 diagnostic field-family tokens for candidate counts, per-candidate hard-filter reason codes, contract fit attribution, premium-risk attribution, and expression reason codes. Diagnostics are not default scalar score-family rows.',
    updated_at = NOW()
WHERE key = 'OPTION_EXPRESSION_DIAGNOSTIC_FIELD_FAMILIES';

UPDATE trading_registry
SET note = replace(note, 'Accepted legacy ', 'Accepted current '),
    updated_at = NOW()
WHERE key IN ('MODEL_04_ALPHA_CONFIDENCE', 'MODEL_05_POSITION_PROJECTION', 'MODEL_06_UNDERLYING_ACTION', 'MODEL_07_OPTION_EXPRESSION')
  AND note LIKE 'Accepted legacy %';

UPDATE trading_registry
SET note = replace(note, 'Physical value name remains legacy 6_* until dedicated migration.', 'Current value name uses the Layer 5 prefix.'),
    updated_at = NOW()
WHERE key IN (
    'POSITION_PROJECTION_CONFIDENCE_SCORE_BY_HORIZON',
    'POSITION_TARGET_EXPOSURE_SCORE_BY_HORIZON',
    'POSITION_TARGET_POSITION_BIAS_SCORE_BY_HORIZON'
);

UPDATE trading_registry
SET note = replace(note, 'Physical value name remains legacy 7_* until dedicated migration.', 'Current value name uses the Layer 6 prefix.'),
    updated_at = NOW()
WHERE key LIKE 'UNDERLYING_%'
  AND note LIKE '%Physical value name remains legacy 7_* until dedicated migration.%';
