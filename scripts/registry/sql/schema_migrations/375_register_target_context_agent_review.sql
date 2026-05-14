-- Register script-called agent review for target-to-Layer-2 context mappings.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'term_TL2CTXREV001',
    'term',
    'TARGET_LAYER2_CONTEXT_AGENT_REVIEW',
    'text',
    'target_layer2_context_agent_review',
    'trading-manager/src/trading_manager_tasks/target_context_review.py',
    'target_layer2_context_mapping;target_layer2_context_mapping_v1;script_called_agent_review;crypto_target_proxy',
    'sync_artifact',
    'Manager-owned script-called agent review boundary for target-to-Layer-2 context mapping rows and target-specific auxiliary proxies.'
  ),
  (
    'art_TL2CTXREV001',
    'artifact_type',
    'TARGET_LAYER2_CONTEXT_AGENT_REVIEW_REQUEST',
    'text',
    'target_layer2_context_agent_review_request',
    'trading-manager/src/trading_manager_tasks/target_context_review.py',
    'target_layer2_context_agent_review;target_layer2_context_mapping;bounded_evidence;script_called_agent_review',
    'sync_artifact',
    'Request artifact containing selected target context mapping rows, required checks, forbidden actions, and the prompt for a reviewer agent.'
  ),
  (
    'art_TL2CTXREV002',
    'artifact_type',
    'TARGET_LAYER2_CONTEXT_AGENT_REVIEW_DECISION',
    'text',
    'target_layer2_context_agent_review_decision',
    'trading-manager/src/trading_manager_tasks/target_context_review.py',
    'target_layer2_context_agent_review;approved;deferred;rejected;queued;agent_call_failed',
    'sync_artifact',
    'Decision artifact produced or queued by the target context review helper. It may approve, defer, or reject mapping rows but has no provider, model activation, broker/account, storage lifecycle, or Layer 1/2 universe mutation side effects.'
  ),
  (
    'scr_TL2CTXREV001',
    'script',
    'REVIEW_TARGET_LAYER2_CONTEXT_MAPPING',
    'command',
    'PYTHONPATH=src python3 scripts/tasks/review_target_layer2_context_mapping.py --target-symbol ${TARGET_SYMBOL} --write',
    '/root/projects/trading-manager/scripts/tasks/review_target_layer2_context_mapping.py',
    'target_layer2_context_agent_review;target_layer2_context_agent_review_request;target_layer2_context_agent_review_decision;target_layer2_context_mapping_v1',
    'sync_artifact',
    'Stable callable script for creating or calling a reviewer-agent pass over target-to-Layer-2 context mapping rows. Actual agent invocation requires explicit reviewed runner configuration.'
  ),
  (
    'cfg_TL2CTXREV001',
    'config',
    'TARGET_LAYER2_CONTEXT_AGENT_REVIEW_SAFETY_BOUNDARY',
    'text',
    'no_provider_calls_no_model_activation_no_broker_or_account_mutation_no_storage_lifecycle_mutation_no_layer_1_2_universe_edits_from_review_runner',
    'trading-manager/src/trading_manager_tasks/target_context_review.py',
    'target_layer2_context_agent_review;safety_boundary;crypto_target_proxy;layer_03_plus_target_study',
    'sync_artifact',
    'Safety boundary for script-called agent review of target context/proxy mappings. Review returns evidence only; structural changes still require normal repository edits, tests, registry migration, commit, and push.'
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
