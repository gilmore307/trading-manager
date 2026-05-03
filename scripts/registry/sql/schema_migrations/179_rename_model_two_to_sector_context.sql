-- Rename active Layer 2 registry contracts from security-selection wording to sector-context wording.
-- Target/security selection now begins at the anonymous target candidate builder boundary.

UPDATE trading_registry
SET
    key = 'SOURCE_02_TARGET_CANDIDATE_HOLDINGS',
    payload = 'source_02_target_candidate_holdings',
    path = 'trading-data/src/data_source/source_02_target_candidate_holdings',
    applies_to = 'trading-data;trading-model;anonymous_target_candidate_builder',
    note = '02 control-plane-facing holdings source for anonymous target candidate preparation; fetches ETF holdings only for market_regime_etf_universe rows with universe_type = sector_observation_etf and writes trading_data.source_02_target_candidate_holdings after Layer 2 sector/basket prioritization.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'dbu_SECINPUT';

UPDATE trading_registry
SET
    applies_to = replace(applies_to, 'source_02_security_selection', 'source_02_target_candidate_holdings'),
    note = replace(replace(note, 'source_02_security_selection', 'source_02_target_candidate_holdings'), 'SecuritySelectionModel', 'anonymous target candidate preparation'),
    updated_at = CURRENT_TIMESTAMP
WHERE applies_to LIKE '%source_02_security_selection%'
   OR note LIKE '%source_02_security_selection%'
   OR note LIKE '%SecuritySelectionModel%';

UPDATE trading_registry
SET
    applies_to = replace(applies_to, 'security_selection_model', 'sector_context_model'),
    note = replace(replace(note, 'security_selection_model', 'sector_context_model'), 'SecuritySelectionModel', 'SectorContextModel'),
    updated_at = CURRENT_TIMESTAMP
WHERE applies_to LIKE '%security_selection_model%'
   OR note LIKE '%security_selection_model%'
   OR note LIKE '%SecuritySelectionModel%';

UPDATE trading_registry
SET
    key = 'MODEL_02_SECTOR_CONTEXT',
    payload = 'model_02_sector_context',
    applies_to = 'trading-model;sector_context_model;feature_02_sector_context',
    note = 'Accepted Layer 2 SectorContextModel model-output term for sector_context_state; physical output table is trading_model.model_02_sector_context.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'trm_M2S001';

UPDATE trading_registry
SET
    applies_to = 'trading-model;sector_context_model;model_02_sector_context',
    note = 'Conceptual Layer 2 SectorContextModel state: inferred sector attributes, market-condition profile, trend stability, composition, tradability, risk context, and eligibility.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'trm_SCS001';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  ('trm_SCM001', 'term', 'SECTOR_CONTEXT_MODEL', 'text', 'sector_context_model', 'trading-model/docs/07_system_model_architecture_rfc.md', 'trading-model;trading-data;model_02_sector_context;feature_02_sector_context', 'registry_only', 'Accepted canonical Layer 2 model id. SectorContextModel models sector/industry basket context under market conditions; it does not select final stock targets.'),
  ('dki_SCFS001', 'data_feature', 'FEATURE_02_SECTOR_CONTEXT', 'text', 'feature_02_sector_context', 'trading-data/src/data_feature/feature_02_sector_context', 'trading-data;trading-model;sector_context_model;source_01_market_regime', 'sync_artifact', 'Layer 2 deterministic feature surface for SectorContextModel sector/industry relative strength, normalized trend, volatility-ratio, correlation, breadth, and dispersion evidence.')
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
