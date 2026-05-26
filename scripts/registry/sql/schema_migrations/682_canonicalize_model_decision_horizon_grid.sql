-- Canonicalize the shared model decision horizon grid.
--
-- The current layer-specific horizon rows all carry the same
-- 10min/1h/1D/1W values. Keep those rows as semantic consumers for their
-- layers, but move the actual shared value set into one canonical registry
-- config so the horizon grid has a single current fact source.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
  'cfg_MDHG001',
  'config',
  'MODEL_DECISION_HORIZON_GRID',
  'text',
  '10min;1h;1D;1W',
  'trading-manager/docs/28_numbering_physical_contract.md;trading-manager/scripts/registry/rules/model-layer-naming.md',
  'model_decision_horizon;trading-model;trading-data;trading-evaluation;trading-execution',
  'registry_only',
  'Canonical model decision horizon grid shared by current model/state/action vector surfaces. 1D is rolling 24-hour natural time and 1W is rolling 7-calendar-day time; labels must remain point-in-time with purge/embargo where evaluation uses future outcomes.'
)
ON CONFLICT (id) DO UPDATE SET
    kind = EXCLUDED.kind,
    key = EXCLUDED.key,
    payload_format = EXCLUDED.payload_format,
    payload = EXCLUDED.payload,
    path = EXCLUDED.path,
    applies_to = EXCLUDED.applies_to,
    artifact_sync_policy = EXCLUDED.artifact_sync_policy,
    note = EXCLUDED.note,
    updated_at = NOW();

UPDATE trading_registry
SET payload = 'model_decision_horizon_grid',
    note = 'TargetStateVector consumes MODEL_DECISION_HORIZON_GRID for synchronized state-observation windows across market, sector, target, and cross-state blocks. These are state observation windows, not downstream action variants.',
    updated_at = NOW()
WHERE key = 'TARGET_STATE_VECTOR_SYNCHRONIZED_STATE_WINDOWS';

UPDATE trading_registry
SET payload = 'model_decision_horizon_grid',
    note = 'EventFailureRiskModel consumes MODEL_DECISION_HORIZON_GRID so event-failure risk horizons stay aligned with downstream alpha, position, and action horizons.',
    updated_at = NOW()
WHERE key = 'EVENT_FAILURE_RISK_VECTOR_HORIZONS';

UPDATE trading_registry
SET payload = 'model_decision_horizon_grid',
    note = 'AlphaConfidenceModel consumes MODEL_DECISION_HORIZON_GRID for prediction horizons; label builders must use point-in-time evidence and purge/embargo controls.',
    updated_at = NOW()
WHERE key = 'ALPHA_CONFIDENCE_VECTOR_HORIZONS';

UPDATE trading_registry
SET payload = 'model_decision_horizon_grid',
    note = 'PositionProjectionModel consumes MODEL_DECISION_HORIZON_GRID for projection horizons; projection labels must use purge/embargo controls.',
    updated_at = NOW()
WHERE key = 'POSITION_PROJECTION_VECTOR_HORIZONS';

UPDATE trading_registry
SET payload = 'model_decision_horizon_grid',
    note = 'UnderlyingActionModel consumes MODEL_DECISION_HORIZON_GRID for Layer 8 action-planning horizons.',
    updated_at = NOW()
WHERE key = 'UNDERLYING_ACTION_VECTOR_HORIZONS';

UPDATE trading_registry
SET payload = 'model_decision_horizon_grid',
    note = 'OptionExpressionModel consumes MODEL_DECISION_HORIZON_GRID for Layer 9 expression horizons; label builders must use purge/embargo controls.',
    updated_at = NOW()
WHERE key = 'OPTION_EXPRESSION_VECTOR_HORIZONS';

UPDATE trading_registry
SET payload = 'model_decision_horizon_grid',
    note = 'EventRiskGovernor consumes MODEL_DECISION_HORIZON_GRID for event-context horizons. Horizons are context-observation horizons, not trade-action variants.',
    updated_at = NOW()
WHERE key = 'EVENT_CONTEXT_VECTOR_HORIZONS';
