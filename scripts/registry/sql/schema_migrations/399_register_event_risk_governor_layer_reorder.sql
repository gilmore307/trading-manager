-- Register conceptual layer reorder that moves event intelligence to Layer 8.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_MLRP003',
    'config',
    'MODEL_LAYER_CONCEPTUAL_REORDER_POLICY',
    'text',
    'layer_01_market_regime;layer_02_sector_context;layer_03_target_state_vector;layer_04_alpha_confidence;layer_05_position_projection;layer_06_underlying_action;layer_07_trading_guidance;layer_08_event_risk_governor',
    'trading-model/docs/94_model_stack_closeout.md',
    'trading-model;trading-data;trading-manager;model_training_workflow;event_risk_governor;trading_guidance',
    'sync_artifact',
    'Active conceptual layer order accepted on 2026-05-15: base Layers 1-7 can produce trading guidance without event intelligence; Layer 8 is a post-guidance event-risk governor.'
  ),
  (
    'trm_TGM001',
    'term',
    'TRADING_GUIDANCE_MODEL',
    'text',
    'trading_guidance_model',
    'trading-model/docs/08_layer_07_trading_guidance.md',
    'layer_07_trading_guidance;option_expression_model;underlying_action_plan;option_expression_plan;trading_guidance_record',
    'registry_only',
    'Conceptual Layer 7 model boundary that outputs the base offline trading-guidance candidate before event-risk intervention. V1 physical implementation may remain the legacy OptionExpressionModel surface until migration.'
  ),
  (
    'trm_TGR001',
    'term',
    'TRADING_GUIDANCE_RECORD',
    'text',
    'trading_guidance_record',
    'trading-model/docs/08_layer_07_trading_guidance.md',
    'layer_07_trading_guidance;trading_guidance_model;option_expression_plan;underlying_action_plan;trading-execution',
    'registry_only',
    'Layer 7 base offline trading-guidance candidate. It can include direct-underlying, option-expression, maintain, or no-trade guidance, but it is not a broker order and does not mutate accounts.'
  ),
  (
    'trm_ERG001',
    'term',
    'EVENT_RISK_GOVERNOR',
    'text',
    'event_risk_governor',
    'trading-model/docs/09_layer_08_event_risk_governor.md',
    'layer_08_event_risk_governor;event_interpretation_v1;trading_guidance_record;event_risk_intervention;execution_risk_control',
    'sync_artifact',
    'Conceptual Layer 8 event-intelligence boundary that reviews the Layer 7 base trading-guidance candidate and may block, cap, reduce, flatten-candidate, halt-candidate, or require human review for high-risk point-in-time events.'
  ),
  (
    'trm_ERI001',
    'term',
    'EVENT_RISK_INTERVENTION',
    'text',
    'event_risk_intervention',
    'trading-model/docs/09_layer_08_event_risk_governor.md',
    'event_risk_governor;layer_08_event_risk_governor;trading_guidance_record;execution_risk_control',
    'sync_artifact',
    'Layer 8 output that modifies the decision/risk record consumed by execution risk-control. It is not a broker order, route, time-in-force, or account mutation.'
  ),
  (
    'cfg_ERIS001',
    'config',
    'EVENT_RISK_INTERVENTION_STATUS_VALUES',
    'text',
    'observe_only;explain_only;block_new_entries;reduce_exposure;flatten_candidate;halt_candidate;human_review_required',
    'trading-model/docs/09_layer_08_event_risk_governor.md',
    'event_risk_governor;event_risk_intervention;event_interpretation_v1;execution_risk_control',
    'sync_artifact',
    'Accepted Layer 8 event-risk intervention severity ladder. Flatten/halt candidates require high-confidence high-severity evidence plus accepted execution risk policy or human review path.'
  ),
  (
    'cfg_LPNM001',
    'config',
    'LEGACY_PHYSICAL_MODEL_LAYER_NAME_POLICY',
    'text',
    'legacy_physical_surfaces_remain_until_dedicated_code_sql_migration',
    'trading-manager/docs/81_decision.md',
    'model_04_event_overlay;model_05_alpha_confidence;model_06_position_projection;model_07_underlying_action;model_08_option_expression;layer_04_event_overlay;layer_08_option_expression',
    'registry_only',
    'After the conceptual reorder, physical script/table/package/stage names may temporarily retain legacy numbering. Active docs must distinguish conceptual layer order from legacy implementation names until a reviewed migration renames code and SQL surfaces.'
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
