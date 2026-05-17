-- Follow-up registry text cleanup after conceptual Layer 04 EventFailureRiskModel insertion.
-- Registry text only; legacy physical names are preserved until a reviewed renumbering migration.

UPDATE trading_registry
SET path = 'trading-model/docs/10_layer_09_event_risk_governor.md;trading-data/src/data_source/source_08_event_risk_governor/README.md',
    applies_to = 'event_activity_bridge;trading-data;training_labels;leakage_control;conceptual_layer_09_event_risk_governor;legacy_physical_names',
    note = 'Detector inputs, event availability, and forward labels must use separate windows so price-derived abnormality is not validated against the same interval that created it. This is conceptual Layer 9 event-governor evidence unless promoted into Layer 4 event-failure-risk scope by reviewed evidence.',
    updated_at = NOW()
WHERE id = 'cfg_APRW001';

UPDATE trading_registry
SET path = 'trading-model/docs/10_layer_09_event_risk_governor.md;trading-data/src/data_source/source_08_event_risk_governor/README.md',
    applies_to = 'event_activity_bridge;trading-data;event_evidence;activity_evidence;prediction_market;conceptual_layer_09_event_risk_governor;legacy_physical_names',
    note = 'Evidence-leg vocabulary for source-owned bridge refs used by conceptual Layer 9 event-governor research/governance. Prediction-market activity is included for future Polymarket-style odds/volume/liquidity evidence.',
    updated_at = NOW()
WHERE id = 'cfg_EABL001';

UPDATE trading_registry
SET payload = 'layer_01_proxy_gap_review_required;legacy_layer_08_event_adapter_review_required;legacy_layer_06_broker_account_route_deferred;legacy_layer_07_restriction_account_route_deferred;legacy_layer_08_thetadata_terminal_required',
    applies_to = 'trading-execution;realtime_input_coverage;layer_01_market_regime;conceptual_layer_09_event_risk_governor;legacy_layer_08_event_risk_governor;model_05_position_projection;model_06_underlying_action;model_07_option_expression;legacy_physical_names',
    note = 'Current gap summary for realtime coverage after the older conceptual Layers 1-8 matrix. These are legacy execution-route keys until a reviewed execution-side renumbering migration aligns them with the Layer 4 EventFailureRiskModel / Layer 9 EventRiskGovernor architecture.',
    updated_at = NOW()
WHERE id = 'cfg_EXEC_RT003';

UPDATE trading_registry
SET applies_to = 'model_worker_1;layer_03_target_state_vector;layers_03_08_base_stack;legacy_layer_08_event_risk_governor;conceptual_layer_09_event_risk_governor;legacy_physical_names',
    note = 'Layer 3+ base-stack Model Worker stages run against one selected target/instrument over the complete six-month rolling fold. Local input materializers must accept start_month/end_month ranges and must not assume one chronological month per run. Legacy source_08 event-governor materialization remains a separate conceptual Layer 9 overlay surface.',
    updated_at = NOW()
WHERE id = 'cfg_FOLDMAT001';

UPDATE trading_registry
SET payload = 'conceptual_layer_09_event_risk_governor_event_not_new_model_layer;feeds_target_event_failure_alpha_context_as_evidence;post_event_realization_is_label_only;no_action_or_execution_output',
    applies_to = 'price_action;false_breakout;event_risk_governor;target_context_state;event_failure_risk_model;alpha_confidence_model;conceptual_layer_09_event_risk_governor',
    note = 'Policy for false-breakout style price-action evidence: represent it as compact conceptual Layer 9 event-risk detector/residual evidence with source refs, without duplicating base bar/liquidity features, adding another standalone model layer, or emitting action/execution fields. Promotion into Layer 4 event-failure-risk scope requires reviewed evidence.',
    updated_at = NOW()
WHERE id = 'cfg_PAE002';

UPDATE trading_registry
SET payload = 'layer_08_after_underlying_action;uses_underlying_action_plan;uses_option_chain_context;no_broker_mutation;legacy_model_07_physical_surface',
    note = 'Layer policy for OptionExpressionModel: option expression is conceptual Layer 8, consumes conceptual Layer 7 underlying path assumptions plus option-chain context, and remains offline without broker mutation. Physical model_07/7_* names remain legacy until renumbering.',
    updated_at = NOW()
WHERE id = 'cfg_OEML001';

UPDATE trading_registry
SET note = 'Conceptual Layer 6 boundary policy: target exposure is abstract risk exposure, position gap is not an execution instruction, and PositionProjectionModel does not emit buy/sell/hold/open/close/reverse, choose instruments, read option chains, or mutate broker/account state. Conceptual Layer 7 owns planned direct-underlying action; conceptual Layer 8 owns option expression.',
    updated_at = NOW()
WHERE id = 'cfg_PPVBP001';

UPDATE trading_registry
SET note = 'Conceptual Layer 7 boundary policy: UnderlyingActionModel produces an offline direct stock/ETF action thesis and conceptual Layer 8 trading-guidance handoff. It must not place orders, emit broker order fields, choose option contracts, or mutate broker/account state.',
    updated_at = NOW()
WHERE id = 'cfg_UAPB001';

UPDATE trading_registry
SET note = replace(note, 'Conceptual Layer 7 high-is', 'Conceptual Layer 8 high-is'),
    updated_at = NOW()
WHERE id LIKE 'fld_OEV%'
  AND note LIKE 'Conceptual Layer 7 high-is%';

UPDATE trading_registry
SET note = 'Prepares reviewed monthly event-feed task keys required before rebuilding legacy event-governor-dependent outputs. Preparation performs no provider calls, model activation, broker execution, account mutation, or dashboard read-model writes.',
    updated_at = NOW()
WHERE id = 'scr_L8EVTBF001';

UPDATE trading_registry
SET applies_to = 'manager_layer_eight_event_risk_governor_input_materialization;legacy_layer_08_event_risk_governor;conceptual_layer_09_event_risk_governor;source_08_event_risk_governor;model_training_workflow;legacy_physical_names',
    note = 'Callable manager entrypoint that materializes legacy source_08 / conceptual Layer 9 event-risk-governor rows from local detector outputs over existing reviewed Layer 2 feed artifacts without provider dispatch.',
    updated_at = NOW()
WHERE id = 'scr_L8ERGMAT001';

UPDATE trading_registry
SET applies_to = 'event_risk_governor;conceptual_layer_09_event_risk_governor;legacy_layer_08_event_risk_governor;trading_guidance_record;execution_risk_control;legacy_physical_names',
    note = 'Conceptual Layer 9 output that modifies the decision/risk record consumed by execution risk-control. It is not a broker order, route, time-in-force, or account mutation.',
    updated_at = NOW()
WHERE id = 'trm_ERI001';

UPDATE trading_registry
SET applies_to = 'legacy_layer_08_event_risk_governor;source_08_event_risk_governor;historical_modeling;event_source_coverage;conceptual_layer_09_event_risk_governor;legacy_physical_names',
    note = 'Legacy source_08 / conceptual Layer 9 event-source coverage requires reviewed local artifacts with requested-window row coverage for Alpaca news, GDELT news, SEC company financials, and Trading Economics calendar rows before event-governor-dependent outputs may advance.',
    updated_at = NOW()
WHERE id = 'term_L8EVTCOV001';

UPDATE trading_registry
SET note = 'Accepted current model_07_option_expression model-output surface name for conceptual Layer 8 OptionExpressionModel option_expression_plan and expression_vector outputs. Physical name remains legacy until a dedicated renumbering migration; this is not live execution.',
    updated_at = NOW()
WHERE id = 'trm_M7OEM01';

UPDATE trading_registry
SET note = 'Conceptual Layer 8 point-in-time option-chain snapshot reference used to replay why a selected contract was chosen. This is not a broker order id.',
    updated_at = NOW()
WHERE id = 'trm_OQSR001';

UPDATE trading_registry
SET note = 'Conceptual Layer 8 point-in-time pending option exposure context used to avoid duplicate option-expression plans. It is not a new order instruction.',
    updated_at = NOW()
WHERE id = 'trm_POEC001';

UPDATE trading_registry
SET applies_to = 'layer_08_trading_guidance;option_expression_model;underlying_action_plan;option_expression_plan;trading_guidance_record;model_07_option_expression;legacy_physical_names',
    note = 'Conceptual Layer 8 model boundary that outputs the base offline trading-guidance candidate before event-risk intervention. The current V1 option-expression implementation surface is model_07_option_expression.',
    updated_at = NOW()
WHERE id = 'trm_TGM001';

UPDATE trading_registry
SET applies_to = 'layer_08_trading_guidance;trading_guidance_model;option_expression_plan;underlying_action_plan;trading-execution;legacy_physical_names',
    note = 'Conceptual Layer 8 base offline trading-guidance candidate. It can include direct-underlying, option-expression, maintain, or no-trade guidance, but it is not a broker order and does not mutate accounts.',
    updated_at = NOW()
WHERE id = 'trm_TGR001';
