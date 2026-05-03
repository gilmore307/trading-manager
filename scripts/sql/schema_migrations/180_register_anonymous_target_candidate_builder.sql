-- Register the concrete Layer 2 -> Layer 3 candidate-builder boundary.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  ('trm_ATCB001', 'term', 'ANONYMOUS_TARGET_CANDIDATE_BUILDER', 'text', 'anonymous_target_candidate_builder', 'trading-model/src/models/anonymous_target_candidate_builder/target_candidate_builder_contract.md', 'trading-model;trading-data;sector_context_model;strategy_selection_model', 'registry_only', 'Concrete boundary between SectorContextModel and StrategySelectionModel. It expands selected/prioritized sector or industry baskets into anonymous target candidates while keeping real ticker/company identity in audit/routing metadata outside model-facing fitting vectors.')
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
