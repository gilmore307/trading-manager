-- Register segmented layer progression policy for formal historical model training.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_MWFP002',
    'config',
    'MODEL_WORKFLOW_SEGMENTED_LAYER_PROGRESSION_POLICY',
    'text',
    'layer_01_background_panel_continuous;layer_02_sector_panel_continuous;layers_03_07_target_major_serial_chain;layer_08_option_expression_after_target_chain_complete;reviewed_exception_required_for_target_fanout',
    'trading-manager/docs/99_historical_scheduler_runtime.md',
    'manager_model_training_workflow_plan_v1;historical_training;scheduler;dataset_expansion;layer_01_market_regime;layer_02_sector_context;layer_03_target_state_vector;layer_04_event_overlay;layer_05_alpha_confidence;layer_06_position_projection;layer_07_underlying_action;layer_08_option_expression',
    'sync_artifact',
    'Formal workflow progression is segmented: Layers 1-2 are finite panel flows and continue forward by month after their own receipts; Layers 3-7 run target-major, completing one selected target candidate through Layer 7 before the next target by default; Layer 8 option-expression expansion waits for the completed upstream target chain.'
  )
ON CONFLICT (id) DO UPDATE
SET kind = EXCLUDED.kind,
    key = EXCLUDED.key,
    payload_format = EXCLUDED.payload_format,
    payload = EXCLUDED.payload,
    path = EXCLUDED.path,
    applies_to = EXCLUDED.applies_to,
    artifact_sync_policy = EXCLUDED.artifact_sync_policy,
    note = EXCLUDED.note,
    updated_at = NOW();
