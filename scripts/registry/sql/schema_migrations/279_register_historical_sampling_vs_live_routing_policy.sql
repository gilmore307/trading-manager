-- Register historical training sampling versus live routing policy.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_MDSE003',
    'config',
    'HISTORICAL_SAMPLING_VS_LIVE_ROUTING_POLICY',
    'text',
    'historical_training_sampling_universe_may_be_broader_than_live_inference_routing_universe;upstream_context_not_unconditional_training_filter;layer_03_targets_may_include_non_selected_sectors;report_broad_generalization_and_live_route_simulation;no_provider_or_activation_or_broker_bypass',
    'trading-manager/docs/100_dataset_expansion.md',
    'trading-manager;dataset_expansion;historical_training;live_inference_routing;trading-model/docs/97_historical_dataset_scope.md;layer_03_target_state_vector',
    'sync_artifact',
    'Dataset expansion policy distinguishing broad historical training sampling from narrower live inference routing. Layer 3 historical target samples may include targets outside Layer 2 selected sectors while preserving point-in-time context and safety gates.'
  ),
  (
    'term_MDSE003',
    'term',
    'HISTORICAL_TRAINING_SAMPLING_UNIVERSE',
    'text',
    'historical_training_sampling_universe',
    'trading-model/docs/97_historical_dataset_scope.md',
    'trading-model;trading-manager;dataset_expansion;historical_training',
    'sync_artifact',
    'Rows collected to fit, calibrate, validate, and test a model layer; may be broader than live routing when point-in-time and leakage-safe.'
  ),
  (
    'term_MDSE004',
    'term',
    'LIVE_INFERENCE_ROUTING_UNIVERSE',
    'text',
    'live_inference_routing_universe',
    'trading-model/docs/97_historical_dataset_scope.md',
    'trading-model;trading-manager;dataset_expansion;live_routing',
    'sync_artifact',
    'Rows that reach a model layer in actual decision flow after upstream gates and prioritization; may be narrower than the historical training sampling universe.'
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
