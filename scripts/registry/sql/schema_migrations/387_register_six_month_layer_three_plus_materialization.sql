-- Register six-month fold-scoped materialization for Layer 3+ model-worker stages.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_FOLDMAT001',
    'config',
    'LAYER_THREE_PLUS_SIX_MONTH_FOLD_MATERIALIZATION',
    'text',
    'target_symbol_six_month_fold_not_month_local_run',
    'trading-manager/src/trading_manager_tasks/layer_three_target_state.py;trading-manager/src/trading_manager_tasks/layer_four_event_overlay.py;trading-manager/src/trading_manager_tasks/model_training_workflow.py',
    'model_worker_1;layer_03_target_state_vector;layer_04_event_overlay;layers_03_08',
    'sync_artifact',
    'Layer 3+ Model Worker stages run against one selected target/instrument over the complete six-month rolling fold. Local input materializers must accept start_month/end_month ranges and must not assume one chronological month per run.'
  ),
  (
    'term_FOLDMAT001',
    'term',
    'FOLD_SCOPED_LAYER_03_TARGET_STATE_INPUTS',
    'text',
    'source_03_target_state task key spans fold_start through fold_end and reuses all reviewed Layer 2 feed artifacts in that range',
    'trading-manager/src/trading_manager_tasks/layer_three_target_state.py;trading-manager/tests/test_layer_three_target_state.py',
    'layer_03_target_state_vector;source_03_target_state;fold_materialization',
    'sync_artifact',
    'Layer 3 target-state input materialization uses one target candidate per symbol across the fold and merges all month-scoped reviewed Layer 2 bars into the six-month source task key.'
  ),
  (
    'term_FOLDMAT002',
    'term',
    'FOLD_SCOPED_LAYER_04_EVENT_OVERLAY_INPUTS',
    'text',
    'source_04_event_overlay detector/source task keys span fold_start through fold_end and keep detector runs separated by symbol and month',
    'trading-manager/src/trading_manager_tasks/layer_four_event_overlay.py;trading-manager/tests/test_layer_four_event_overlay.py',
    'layer_04_event_overlay;source_04_event_overlay;fold_materialization',
    'sync_artifact',
    'Layer 4 event-overlay materialization accepts six-month folds, prepares detector task keys per symbol-month, and writes one fold-scoped source_04 task key for the event index.'
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
