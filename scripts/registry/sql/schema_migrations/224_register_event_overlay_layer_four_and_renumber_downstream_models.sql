-- Promote EventOverlayModel to Layer 4 and renumber downstream model surfaces.
-- Keep Layer 3 physical implementation names such as model_03_target_state_vector,
-- while updating the conceptual output vocabulary to target_context_state.

UPDATE trading_registry
SET key = 'SOURCE_04_EVENT_OVERLAY',
    payload = 'source_04_event_overlay',
    path = 'trading-data/src/data_source/source_04_event_overlay',
    applies_to = 'trading-data;trading-model;event_overlay_model;model_04_event_overlay',
    note = '04 control-plane-facing EventOverlayModel data source; prepares one SQL event overview row per required event with details behind references.'
WHERE key = 'SOURCE_07_EVENT_OVERLAY';

UPDATE trading_registry
SET applies_to = REPLACE(applies_to, 'source_07_event_overlay', 'source_04_event_overlay'),
    path = REPLACE(path, 'source_07_event_overlay', 'source_04_event_overlay'),
    note = REPLACE(note, 'source_07_event_overlay', 'source_04_event_overlay')
WHERE COALESCE(applies_to, '') LIKE '%source_07_event_overlay%'
   OR COALESCE(path, '') LIKE '%source_07_event_overlay%'
   OR COALESCE(note, '') LIKE '%source_07_event_overlay%';

UPDATE trading_registry
SET note = REPLACE(note, '07 control-plane-facing EventOverlayModel', '04 control-plane-facing EventOverlayModel')
WHERE key = 'SOURCE_04_EVENT_OVERLAY';

UPDATE trading_registry
SET key = 'TARGET_CONTEXT_STATE_VERSION_DEFAULT',
    payload = 'target_context_state_v1',
    applies_to = 'model_03_target_state_vector;feature_03_target_state_vector;target_state_vector_model;target_context_state_version',
    note = 'Default TargetContextState V1 contract/config version value emitted as target_context_state_version by current Layer 3 target-state feature/model rows.'
WHERE key = 'TARGET_STATE_VECTOR_VERSION_DEFAULT';

UPDATE trading_registry
SET key = 'TARGET_CONTEXT_STATE_VERSION',
    payload = 'target_context_state_version',
    note = 'Reviewed TargetContextState V1 contract/config version carried by feature and model rows; use target_context_state_version rather than generic feature_vector_version for the Layer 3 target-context surface.'
WHERE key = 'TARGET_STATE_VECTOR_VERSION';

UPDATE trading_registry
SET key = 'TARGET_CONTEXT_STATE_REF',
    payload = 'target_context_state_ref',
    note = 'Stable reference or hash for the model-facing target_context_state payload.'
WHERE key = 'TARGET_STATE_VECTOR_REF';

UPDATE trading_registry
SET key = 'TARGET_CONTEXT_STATE',
    payload = 'target_context_state',
    applies_to = 'trading-model;trading-data;target_state_vector_model;model_03_target_state_vector;feature_03_target_state_vector',
    note = 'Conceptual Layer 3 model-facing anonymous target context state built from separately inspectable market, sector, target-local, and cross-state blocks; raw ticker/company identity stays outside fitting vectors. Historical physical paths retain model_03_target_state_vector.'
WHERE key = 'TARGET_STATE_VECTOR';

UPDATE trading_registry
SET note = 'Layer 3 preprocessing/input feature vector consumed by TargetStateVectorModel. It excludes ticker/company identity and is not the model output context state; target_context_state is the Layer 3 conceptual output.'
WHERE key = 'ANONYMOUS_TARGET_FEATURE_VECTOR';

UPDATE trading_registry
SET applies_to = REGEXP_REPLACE(applies_to, '(^|;)target_state_vector(;|$)', '\1target_context_state\2', 'g')
WHERE COALESCE(applies_to, '') ~ '(^|;)target_state_vector(;|$)';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  ('trm_EOM001', 'term', 'EVENT_OVERLAY_MODEL', 'text', 'event_overlay_model', 'trading-model/docs/90_system_model_architecture_rfc.md', 'trading-model;trading-data;source_04_event_overlay;model_04_event_overlay;event_context_vector', 'registry_only', 'Accepted canonical Layer 4 model id. EventOverlayModel converts point-in-time scheduled/news/filing/macro/abnormal-activity evidence into event context before alpha confidence.'),
  ('trm_M4EOM01', 'term', 'MODEL_04_EVENT_OVERLAY', 'text', 'model_04_event_overlay', 'trading-model/docs/90_system_model_architecture_rfc.md', 'trading-model;event_overlay_model;event_context_vector;source_04_event_overlay', 'registry_only', 'Accepted Layer 4 EventOverlayModel model-output surface name for future promoted event_context_vector outputs.'),
  ('trm_ECV001', 'term', 'EVENT_CONTEXT_VECTOR', 'text', 'event_context_vector', 'trading-model/docs/05_layer_04_event_overlay.md', 'trading-model;event_overlay_model;model_04_event_overlay;alpha_confidence_model', 'registry_only', 'Layer 4 point-in-time event-context output consumed by AlphaConfidenceModel; contains event timing, scope, type, intensity, directional context, risk context, and quality context without action or execution instructions.'),
  ('trm_ASV001', 'term', 'ALPHA_CONFIDENCE_VECTOR', 'text', 'alpha_confidence_vector', 'trading-model/docs/90_system_model_architecture_rfc.md', 'trading-model;alpha_confidence_model;model_05_alpha_confidence;event_context_vector', 'registry_only', 'Layer 5 AlphaConfidenceModel output vector for long/short confidence, expected value, risk, and uncertainty; not a final action or position-sizing instruction.'),
  ('trm_TSVEC01', 'term', 'TRADING_SIGNAL_VECTOR', 'text', 'trading_signal_vector', 'trading-model/docs/90_system_model_architecture_rfc.md', 'trading-model;trading_projection_model;model_06_trading_projection;alpha_confidence_vector', 'registry_only', 'Layer 6 TradingProjectionModel output vector for offline trading intent/projection before expression/final-action selection.'),
  ('trm_OEM001', 'term', 'OPTION_EXPRESSION_MODEL', 'text', 'option_expression_model', 'trading-model/docs/90_system_model_architecture_rfc.md', 'trading-model;source_05_option_expression;model_07_option_expression;trading_signal_vector', 'registry_only', 'Accepted Layer 7 expression model id for comparing stock/ETF expression against long call/long put option expression before final action boundaries.'),
  ('trm_M7OEM01', 'term', 'MODEL_07_OPTION_EXPRESSION', 'text', 'model_07_option_expression', 'trading-model/docs/90_system_model_architecture_rfc.md', 'trading-model;option_expression_model;source_05_option_expression;final_action', 'registry_only', 'Accepted Layer 7 OptionExpressionModel model-output surface name for future promoted expression/final-action boundary outputs.')
ON CONFLICT (id) DO UPDATE SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  artifact_sync_policy = EXCLUDED.artifact_sync_policy,
  note = EXCLUDED.note;

UPDATE trading_registry
SET applies_to = 'trading-model;target_context_state;event_context_vector;model_05_alpha_confidence',
    note = 'Accepted canonical Layer 5 model id. AlphaConfidenceModel maps target_context_state plus event_context_vector to long/short alpha or direction confidence, expected value, risk, and uncertainty; it is separate from Layer 3 direction evidence and Layer 4 event context.'
WHERE key = 'ALPHA_CONFIDENCE_MODEL';

UPDATE trading_registry
SET key = 'MODEL_05_ALPHA_CONFIDENCE',
    payload = 'model_05_alpha_confidence',
    applies_to = 'trading-model;alpha_confidence_model;target_context_state;event_context_vector',
    note = 'Accepted Layer 5 AlphaConfidenceModel model-output surface name for future promoted confidence/expected-value outputs.'
WHERE key = 'MODEL_04_ALPHA_CONFIDENCE';

UPDATE trading_registry
SET applies_to = 'trading-model;alpha_confidence_model;alpha_confidence_vector;model_06_trading_projection',
    note = 'Accepted canonical Layer 6 model id. TradingProjectionModel maps confidence plus reviewed cost/risk context to offline trading intent and target projection; it is not live execution.'
WHERE key = 'TRADING_PROJECTION_MODEL';

UPDATE trading_registry
SET key = 'MODEL_06_TRADING_PROJECTION',
    payload = 'model_06_trading_projection',
    applies_to = 'trading-model;trading_projection_model;alpha_confidence_model;alpha_confidence_vector;trading_signal_vector',
    note = 'Accepted Layer 6 TradingProjectionModel model-output surface name for future promoted offline trading projection outputs.'
WHERE key = 'MODEL_05_TRADING_PROJECTION';
