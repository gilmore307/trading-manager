-- Register execution realtime input coverage matrix and capture contract.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'trm_EXEC_RT002',
    'term',
    'EXECUTION_REALTIME_INPUT_COVERAGE_MATRIX',
    'text',
    'execution_realtime_input_coverage_v1',
    'trading-execution/src/trading_execution/market_data/contracts.py',
    'trading-execution;realtime_market_data;model_01_market_regime;model_02_sector_context;model_03_target_state_vector;model_04_event_overlay;model_05_alpha_confidence;model_06_position_projection;model_07_underlying_action;model_08_option_expression',
    'sync_artifact',
    'Side-effect-free Layers 1-8 realtime model-input coverage matrix. It records required realtime observation groups, primary sources, required capture fields, current coverage status, and known provider/account/restriction gaps without opening streams or calling providers.'
  ),
  (
    'art_EXEC_RT001',
    'artifact_type',
    'REALTIME_CAPTURE_CONTRACT',
    'text',
    'realtime_capture_contract_v1',
    'trading-execution/src/trading_execution/market_data/contracts.py',
    'trading-execution;trading-manager;trading-model;forward_holdout;shadow_monitoring;run_manifest_v1;artifact_ref_v1;ready_signal_v1',
    'sync_artifact',
    'Append-only point-in-time realtime capture contract for future forward-validation and shadow-monitoring evidence. Requires frozen model/config refs, model output refs, dataset role, label maturity, outcome labels, and manager/storage handoff refs.'
  ),
  (
    'cfg_EXEC_RT002',
    'config',
    'EXECUTION_REALTIME_COVERAGE_GAP_POLICY',
    'text',
    'coverage_matrix_must_show_partial_routes_and_gaps;catalog_inspection_performs_zero_provider_calls;capture_contract_forbids_historical_snapshot_rewrite_model_activation_and_broker_mutation',
    'trading-execution/docs/09_realtime_data.md',
    'trading-execution;realtime_market_data;coverage_status;provider_calls;broker_mutation;model_activation',
    'sync_artifact',
    'Policy that realtime model-input coverage must expose incomplete routes and gaps rather than pretending that reviewed sources are already fully connected. Catalog inspection remains side-effect-free.'
  ),
  (
    'cfg_EXEC_RT003',
    'config',
    'EXECUTION_REALTIME_LAYER_GAP_SUMMARY',
    'text',
    'layer_01_proxy_gap_review_required;layer_04_event_adapter_review_required;layer_06_broker_account_route_deferred;layer_07_restriction_account_route_deferred;layer_08_thetadata_terminal_required',
    'trading-execution/docs/09_realtime_data.md',
    'trading-execution;realtime_input_coverage;layer_01_market_regime;layer_04_event_overlay;layer_06_position_projection;layer_07_underlying_action;layer_08_option_expression',
    'sync_artifact',
    'Concise current gap summary for realtime coverage after the first Layers 1-8 matrix: proxy/native macro-market routes, event adapters, broker/account state, restriction/account state, and ThetaData terminal dependency remain explicit.'
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
