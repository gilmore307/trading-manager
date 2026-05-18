-- Align active registry rows with the accepted Layer 8/9 swap.
-- Layer 8 is EventRiskGovernor; Layer 9 is TradingGuidance / OptionExpression.
-- Data/source surfaces source_09_event_risk_governor and feature_09_event_risk_governor remain unchanged.

UPDATE trading_registry
SET     key = 'MANAGER_MODEL_TRAINING_WORKFLOW_PLAN_ARTIFACT',
    payload = 'manager_model_training_workflow_plan',
    path = 'trading-manager/src/trading_manager_tasks/model_training_workflow.py',
    applies_to = 'trading-manager;scheduler;historical_training;layer_01_market_regime;layer_02_sector_context;layer_03_target_state_vector;layer_04_event_failure_risk;model_05_alpha_confidence;model_06_position_projection;model_07_underlying_action;layer_08_event_risk_governor;model_09_option_expression;current_physical_names;layer_01_02_foundation_catch_up;post_model_artifact_rebuild_boundary;rolling_fold_promotion;four_one_one_split',
    note = 'Manager-owned base Layer 1-9 workflow plan within the resident Layer 1-9 historical-modeling system service. During foundation catch-up, month-scoped workflow states expose only reusable substrate data_acquisition and feature_generation for Layers 1-2 before target-specific work; base model generation/evaluation/Promotion Review belong to fold-scoped model/promotion work after frozen 4+1+1 manifests exist. Current source_09_event_risk_governor / Layer 8 EventRiskGovernor governs Layer 7 direct-underlying thesis before Layer 9 trading-guidance/option-expression handoff.',
    updated_at = NOW()
WHERE id = 'art_MMTW001';

UPDATE trading_registry
SET     key = 'ACTIVITY_PRICE_RELATIONSHIP_FORWARD_LABEL_FAMILIES',
    payload = 'forward_return;forward_drawdown;forward_reversal;forward_volatility_expansion;forward_gap_or_jump;path_asymmetry',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'event_activity_bridge;training_labels;model_evaluation;abnormal_activity',
    note = 'Forward label families used to test whether abnormal activity has a stable relationship to subsequent price/path outcomes.',
    updated_at = NOW()
WHERE id = 'cfg_APRF001';

UPDATE trading_registry
SET     key = 'ACTIVITY_PRICE_RELATIONSHIP_PROOF_GATE',
    payload = 'required_before_event_activity_bridge_model_promotion',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'event_activity_bridge;event_risk_governor;abnormal_activity;model_promotion;training_labels',
    note = 'Abnormal activity must prove stable point-in-time forward price/path relationship before becoming a separate model layer or risk-intervention input.',
    updated_at = NOW()
WHERE id = 'cfg_APRG001';

UPDATE trading_registry
SET     key = 'ACTIVITY_PRICE_RELATIONSHIP_PROOF_LEVELS',
    payload = 'contemporaneous_association;forward_price_path_relationship;incremental_residual_value;cross_market_confirmation_value;out_of_sample_stability',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'event_activity_bridge;model_evaluation;model_promotion;abnormal_activity',
    note = 'Required proof levels. Current-window association alone is insufficient; forward and incremental residual evidence are required.',
    updated_at = NOW()
WHERE id = 'cfg_APRL001';

UPDATE trading_registry
SET     key = 'ACTIVITY_PRICE_RELATIONSHIP_REQUIRED_CONTROLS',
    payload = 'market_context;sector_context;peer_context;target_state;ordinary_bar_volume_liquidity_volatility_features;scheduled_event_calendar_shells;time_of_day_day_of_week_month_effects;broad_market_liquidity_volatility_regime',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'event_activity_bridge;model_evaluation;leakage_control;abnormal_activity',
    note = 'Controls required before abnormal activity can claim incremental residual value over existing market-data and model-stack information.',
    updated_at = NOW()
WHERE id = 'cfg_APRC001';

UPDATE trading_registry
SET     key = 'ACTIVITY_PRICE_RELATIONSHIP_TEST_HORIZONS',
    payload = '5m;30m;1h;1d;5d;20d',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'event_activity_bridge;training_labels;model_evaluation;abnormal_activity',
    note = 'Initial short and event-relevant horizons for abnormal-activity to forward-price/path relationship tests.',
    updated_at = NOW()
WHERE id = 'cfg_APRH001';

UPDATE trading_registry
SET     key = 'ACTIVITY_PRICE_RELATIONSHIP_WINDOW_SEPARATION_POLICY',
    payload = 'activity_detection_window;event_availability_window;forward_label_window',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md;trading-data/src/data_source/source_09_event_risk_governor/README.md',
    applies_to = 'event_activity_bridge;trading-data;training_labels;leakage_control;layer_08_event_risk_governor;current_physical_names',
    note = 'Detector inputs, event availability, and forward labels must use separate windows so price-derived abnormality is not validated against the same interval that created it. This is Layer 8 event-governor evidence unless promoted into Layer 4 event-failure-risk scope by reviewed evidence.',
    updated_at = NOW()
WHERE id = 'cfg_APRW001';

UPDATE trading_registry
SET     key = 'CURRENT_PHYSICAL_MODEL_LAYER_NAME_POLICY',
    payload = 'current_physical_surfaces_aligned_with_nine_layer_order;historical_migrations_and_artifacts_unchanged',
    path = 'trading-manager/docs/05_decision.md',
    applies_to = 'layer_04_event_failure_risk;model_05_alpha_confidence;model_06_position_projection;model_07_underlying_action;model_08_event_risk_governor;model_09_option_expression;current_physical_names;model_architecture',
    note = 'After the accepted Layer 8/9 swap, active script/table/package/stage names use model_08_event_risk_governor for EventRiskGovernor and model_09_option_expression for TradingGuidance/OptionExpression. Historical/applied migrations and old artifacts remain unchanged for auditability.',
    updated_at = NOW()
WHERE id = 'cfg_LPNM001';

UPDATE trading_registry
SET     key = 'EVENT_ABNORMAL_ACTIVITY_ALLOWED_USES',
    payload = 'detector_provenance;residual_unexplained_board_tape_disturbance;discrete_price_action_token;cross_source_abnormal_evidence_not_already_consumed;microstructure_liquidity_disruption;option_derivatives_abnormality',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'event_risk_governor;equity_abnormal_activity_event;price_action;option_abnormal_activity;event_interpretation_v1',
    note = 'Allowed abnormal-activity uses for event-risk governance after excluding ordinary model-owned market-data features. Use category values from EVENT_ABNORMAL_ACTIVITY_EVIDENCE_CATEGORIES for implementation-facing classification.',
    updated_at = NOW()
WHERE id = 'cfg_EAAB001';

UPDATE trading_registry
SET     key = 'EVENT_ABNORMAL_ACTIVITY_EVIDENCE_CATEGORIES',
    payload = 'price_action_pattern;residual_market_structure_disturbance;microstructure_liquidity_disruption;option_derivatives_abnormality',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'event_abnormal_activity_residual_policy;event_risk_governor;source_09_event_risk_governor;equity_abnormal_activity_event;price_action;option_abnormal_activity',
    note = 'Accepted abnormal-activity evidence categories. They are residual/provenance/risk evidence and must not duplicate ordinary model-owned bars, liquidity, trend, or target-state features.',
    updated_at = NOW()
WHERE id = 'cfg_EAAC001';

UPDATE trading_registry
SET     key = 'EVENT_ABNORMAL_ACTIVITY_RESIDUAL_POLICY',
    payload = 'residual_or_provenance_only;no_duplicate_bar_liquidity_features;incremental_value_required_over_upstream_context_states',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'event_risk_governor;source_09_event_risk_governor;equity_abnormal_activity_event;feature_09_event_risk_governor;market_context_state;sector_context_state;target_context_state',
    note = 'Abnormal-activity event evidence may cite bars/liquidity as detector provenance or residual unexplained board/tape disturbance, but must not re-emit model-owned bar/liquidity/target-state features as independent event alpha.',
    updated_at = NOW()
WHERE id = 'cfg_EAAR001';

UPDATE trading_registry
SET     key = 'EVENT_ACTIVITY_BRIDGE_ABNORMALITY_STARTUP_SCOPE',
    payload = 'price_action_pattern=false_breakout,false_breakdown,liquidity_sweep_high,liquidity_sweep_low,bull_trap,bear_trap;residual_market_structure_disturbance=target_specific_board_tape_disturbance_after_upstream_conditioning;microstructure_liquidity_disruption=spread_widening,depth_disappearance,quote_quality_breakdown,one_sided_prints,halt_or_pause,anomalous_quote_environment;option_derivatives_abnormality=iv_shock,skew_or_term_structure_shock,unusual_option_volume,call_put_imbalance,sweep_or_block_evidence,oi_change,option_liquidity_disruption',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'event_activity_bridge;event_risk_governor;abnormal_activity;startup_scope;source_09_event_risk_governor',
    note = 'Narrow startup abnormality scope for Layer 8 activity bridge evidence. These are compact point-in-time detector refs only, not standalone alpha or duplicated upstream model features.',
    updated_at = NOW()
WHERE id = 'cfg_EABAS001';

UPDATE trading_registry
SET     key = 'EVENT_ACTIVITY_BRIDGE_CORE_FIELDS',
    payload = 'linked_event_ref;activity_evidence_refs;activity_window;event_window;lead_lag_seconds;residual_activity_score;cross_market_confirmation_score;option_confirmation_score;prediction_market_confirmation_score;explanation_status',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'event_activity_bridge;event_interpretation_v1;source_09_event_risk_governor;prediction_market',
    note = 'Core field set for the event-activity bridge. Scores are model-owned; source repos preserve refs, windows, and clocks.',
    updated_at = NOW()
WHERE id = 'cfg_EABF001';

UPDATE trading_registry
SET     key = 'EVENT_ACTIVITY_BRIDGE_EVIDENCE_LEGS',
    payload = 'event_evidence_ref;price_activity_ref;liquidity_activity_ref;option_activity_ref;prediction_market_activity_ref',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md;trading-data/src/data_source/source_09_event_risk_governor/README.md',
    applies_to = 'event_activity_bridge;trading-data;event_evidence;activity_evidence;prediction_market;layer_08_event_risk_governor;current_physical_names',
    note = 'Evidence-leg vocabulary for source-owned bridge refs used by Layer 8 event-governor research/governance. Prediction-market activity is included for future Polymarket-style odds/volume/liquidity evidence.',
    updated_at = NOW()
WHERE id = 'cfg_EABL001';

UPDATE trading_registry
SET     key = 'EVENT_ACTIVITY_BRIDGE_EXPLANATION_STATUS_VALUES',
    payload = 'explained_by_known_event;partially_explained;unexplained;later_explained;review_required',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'event_activity_bridge;point_in_time;event_risk_governor;training_labels',
    note = 'Accepted explanation-status values. Later explanations create follow-up bridge evidence and must not rewrite the original point-in-time activity record.',
    updated_at = NOW()
WHERE id = 'cfg_EABE001';

UPDATE trading_registry
SET     key = 'EVENT_ACTIVITY_BRIDGE_RELATION_TYPES',
    payload = 'pre_event_precursor;co_event_reaction;post_event_absorption;event_activity_divergence;unresolved_latent_hazard',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'event_activity_bridge;event_risk_governor;event_family_training;prediction_market',
    note = 'Accepted bridge relation types for lead/lag, reaction, absorption, divergence, and unresolved latent hazard evidence.',
    updated_at = NOW()
WHERE id = 'cfg_EABR001';

UPDATE trading_registry
SET     key = 'EVENT_CONTEXT_VECTOR_HORIZONS',
    payload = '5min;15min;60min;390min',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'event_context_vector;event_risk_governor;model_08_event_risk_governor',
    note = 'Accepted EventRiskGovernor V1 event-context horizons. Horizons are context-observation horizons, not trade-action variants.',
    updated_at = NOW()
WHERE id = 'cfg_ECVH001';

UPDATE trading_registry
SET     key = 'EVENT_CONTEXT_VECTOR_SCORE_FAMILIES',
    payload = '8_event_presence_score_<horizon>;8_event_timing_proximity_score_<horizon>;8_event_intensity_score_<horizon>;8_event_direction_bias_score_<horizon>;8_event_context_alignment_score_<horizon>;8_event_uncertainty_score_<horizon>;8_event_gap_risk_score_<horizon>;8_event_reversal_risk_score_<horizon>;8_event_liquidity_disruption_score_<horizon>;8_event_contagion_risk_score_<horizon>;8_event_context_quality_score_<horizon>;8_event_market_impact_score_<horizon>;8_event_sector_impact_score_<horizon>;8_event_industry_impact_score_<horizon>;8_event_theme_factor_impact_score_<horizon>;8_event_peer_group_impact_score_<horizon>;8_event_symbol_impact_score_<horizon>;8_event_microstructure_impact_score_<horizon>;8_event_scope_confidence_score_<horizon>;8_event_scope_escalation_risk_score_<horizon>;8_event_target_relevance_score_<horizon>',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'event_context_vector;event_risk_governor;model_08_event_risk_governor;state_vector_value',
    note = 'Accepted current 8_event_* event-context scalar score-family tokens for model_08_event_risk_governor / Layer 8 EventRiskGovernor. These families separate event presence, timing, intensity, direction bias, alignment, risks, quality, impact scope, scope confidence, escalation risk, and target relevance; enum-like audit fields remain model-local.',
    updated_at = NOW()
WHERE id = 'cfg_ECVS001';

UPDATE trading_registry
SET     key = 'EVENT_FAMILY_TO_LAYER_04_PROMOTION_POLICY',
    payload = 'script_emitted_evidence_packet_required;matched_controls_required;split_stability_required;pit_leakage_review_required;incremental_value_over_base_stack_required;agent_review_required;manager_decision_required;no_automatic_promotion',
    path = 'trading-model/docs/13_layer_04_event_failure_risk.md;trading-model/docs/51_event_family_scouting.md;trading-manager/docs/05_decision.md',
    applies_to = 'event_risk_governor;event_family_strategy_promotion_review;event_failure_risk_model;manager_decision',
    note = 'Promotion policy from Layer 8 EventRiskGovernor research into Layer 4 EventFailureRiskModel. Residual/event discovery may generate hypotheses and review packets, but cannot automatically promote event families into front decision scope.',
    updated_at = NOW()
WHERE id = 'cfg_EFRP001';

UPDATE trading_registry
SET     key = 'EVENT_LIFECYCLE_CLOCK_FIELDS',
    payload = 'event_awareness_time;event_scheduled_time;event_effective_time;event_actual_time;source_published_time;source_updated_time;ingested_time;available_time;interpretation_time;resolution_time;decision_time;tradeable_time;reaction_window',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'event_lifecycle_contract;point_in_time;event_interpretation_v1;source_09_event_risk_governor;event_risk_governor',
    note = 'Lifecycle clocks that preserve awareness, scheduled release, source publication, system availability, interpretation, resolution, decision/tradeability, and evaluation-only reaction windows.',
    updated_at = NOW()
WHERE id = 'cfg_ELCV001';

UPDATE trading_registry
SET     key = 'EVENT_LIFECYCLE_GOLDEN_EXAMPLES',
    payload = 'earnings=scheduled_known_outcome_later;cpi_macro_release=scheduled_recurring_data_release;surprise_regulatory_raid_or_news=unscheduled_surprise',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'event_lifecycle_contract;event_family_training;golden_tests;event_risk_governor',
    note = 'Initial golden lifecycle examples for event-family contract tests: earnings, CPI/macro release, and unscheduled surprise regulatory/news events.',
    updated_at = NOW()
WHERE id = 'cfg_ELG001';

UPDATE trading_registry
SET     key = 'EVENT_LIFECYCLE_STATE_VALUES',
    payload = 'scheduled_future;pre_event_window;live_release_window;post_event_initial_reaction;post_event_decay;developing_update;resolved;stale_event;unknown',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'event_lifecycle_contract;event_risk_governor;event_interpretation_v1',
    note = 'Recommended state values describing where the current point-in-time event row sits in the event arc.',
    updated_at = NOW()
WHERE id = 'cfg_ELS001';

UPDATE trading_registry
SET     key = 'EVENT_LIFECYCLE_TYPE_VALUES',
    payload = 'scheduled_known_outcome_later;unscheduled_surprise;scheduled_recurring_data_release;multi_stage_developing_event;unknown',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'event_lifecycle_contract;event_risk_governor;event_interpretation_v1;source_09_event_risk_governor',
    note = 'Accepted event lifecycle classes. Scheduled-known catalysts may be visible before outcome release; surprise events cannot have a specific pre-event event row.',
    updated_at = NOW()
WHERE id = 'cfg_ELTV001';

UPDATE trading_registry
SET     key = 'EVENT_RISK_GOVERNOR_RISK_TARGET_BASIS',
    payload = 'underlying_action_plan_primary;trading_guidance_record_optional;option_expression_plan_optional;crypto_direct_underlying_only',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'event_risk_governor;underlying_action_plan;trading_guidance_record;option_expression_plan;crypto;direct_underlying_only',
    note = 'Layer 8 EventRiskGovernor uses the Layer 7 direct-underlying/spot thesis as the canonical intervention target. Layer 9 trading-guidance and option-expression context are optional; crypto/direct-underlying-only routes must not require option-chain or option-expression evidence.',
    updated_at = NOW()
WHERE id = 'cfg_ERG002';

UPDATE trading_registry
SET     key = 'EVENT_RISK_INTERVENTION_STATUS_VALUES',
    payload = 'observe_only;explain_only;block_new_entries;reduce_exposure;flatten_candidate;halt_candidate;human_review_required',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'event_risk_governor;event_risk_intervention;event_interpretation_v1;execution_risk_control',
    note = 'Accepted Layer 8 event-risk intervention severity ladder. Flatten/halt candidates require high-confidence high-severity evidence plus accepted execution risk policy or human review path.',
    updated_at = NOW()
WHERE id = 'cfg_ERIS001';

UPDATE trading_registry
SET     key = 'EXECUTION_REALTIME_LAYER_GAP_SUMMARY',
    payload = 'layer_01_proxy_gap_review_required;layer_08_event_adapter_review_required;layer_06_broker_account_route_deferred;layer_07_restriction_account_route_deferred;layer_08_thetadata_terminal_required',
    path = 'trading-execution/docs/20_realtime_data.md',
    applies_to = 'trading-execution;realtime_input_coverage;layer_01_market_regime;layer_08_event_risk_governor;model_06_position_projection;model_07_underlying_action;model_09_option_expression;current_physical_names',
    note = 'Current realtime coverage gap summary for the nine-layer stack. Layer 6 broker/account state, Layer 7 restrictions, Layer 8 ThetaData option-chain context, and Layer 9 event adapters remain bounded route gaps until reviewed implementation fills them.',
    updated_at = NOW()
WHERE id = 'cfg_EXEC_RT003';

UPDATE trading_registry
SET     key = 'LAYER_08_OPTION_BUCKET_EXPIRATION_POLICY',
    payload = 'near_to_far_listed_expirations;current_week;next_week;following_week;continue_outward_only_when_coverage_policy_requires',
    path = 'trading-model/docs/18_layer_09_trading_guidance.md',
    applies_to = 'layer_09_option_expression;OptionExpressionModel;option_contract_bucket;manager_model_training_workflow_plan',
    note = 'Layer 9 option-expression contract bucket expansion scans listed expirations from near to far for the option-expression boundary.',
    updated_at = NOW()
WHERE id = 'cfg_L8OPT001';

UPDATE trading_registry
SET     key = 'LAYER_08_OPTION_BUCKET_PREFILTER_POLICY',
    payload = 'no_acquisition_time_prefilter_for_model_construction;retain_illiquid_wide_spread_low_oi_high_iv_deep_itm_otm_stale_and_extreme_contracts_as_features_labels_reason_codes',
    path = 'trading-model/docs/18_layer_09_trading_guidance.md',
    applies_to = 'layer_09_option_expression;OptionExpressionModel;option_contract_bucket;historical_model_construction;robustness_coverage',
    note = 'Layer 9 option-expression historical model-construction buckets intentionally retain extreme/illiquid contracts for robustness instead of filtering them out at acquisition time.',
    updated_at = NOW()
WHERE id = 'cfg_L8OPT003';

UPDATE trading_registry
SET     key = 'LAYER_08_OPTION_BUCKET_STRIKE_POLICY',
    payload = 'current_to_target_listed_strike_corridor;three_listed_strike_levels_below;three_listed_strike_levels_above;use_actual_listed_strikes_not_fixed_dollars;example_95_to_100_one_dollar_strikes_92_to_103',
    path = 'trading-model/docs/18_layer_09_trading_guidance.md',
    applies_to = 'layer_09_option_expression;OptionExpressionModel;option_contract_bucket;strike_selection;manager_model_training_workflow_plan',
    note = 'Layer 9 option-expression bucket strikes cover the current-price to target-price listed-strike corridor plus three actual listed strike levels on each side.',
    updated_at = NOW()
WHERE id = 'cfg_L8OPT002';

UPDATE trading_registry
SET     key = 'LAYER_09_OPTION_EXPRESSION_SINGLE_LEG_POLICY',
    payload = 'single_leg_only;long_call;long_put;no_option_expression;multi_leg_spreads_deferred',
    path = 'trading-model/docs/18_layer_09_trading_guidance.md',
    applies_to = 'layer_09_option_expression;OptionExpressionModel;option_expression_plan;expression_vector',
    note = 'Layer 9 option-expression V1 coverage is single-leg only: long call, long put, or no-option expression. Multi-leg spreads are deferred beyond V1.',
    updated_at = NOW()
WHERE id = 'cfg_L8OPT004';

UPDATE trading_registry
SET     key = 'LAYER_EIGHT_REQUIRED_EVENT_FEED_ARTIFACTS',
    payload = 'alpaca_news:equity_news.csv;gdelt_news:gdelt_article.csv;sec_company_financials:sec_company_fact.csv;trading_economics_calendar_web:trading_economics_calendar_event.csv',
    path = 'trading-manager/src/trading_manager_tasks/layer_eight_event_risk_governor.py;trading-data/src/data_source/source_09_event_risk_governor/README.md',
    applies_to = 'source_09_event_risk_governor;event_artifact_paths;event_feed_coverage',
    note = 'Required reviewed saved feed artifacts for a complete current source_09 / Layer 8 event-risk-governor rebuild. Missing artifacts or zero requested-window row coverage block write-mode materialization.',
    updated_at = NOW()
WHERE id = 'cfg_L8EVTCOV001';

UPDATE trading_registry
SET     key = 'LAYER_PHYSICAL_NUMBERING_AUDIT',
    payload = 'physical_current_numbering_aligned;historical_migrations_and_artifacts_unchanged;compatibility_aliases_only_for_prior_evidence_refs',
    path = 'trading-manager/docs/28_numbering_physical_contract.md',
    applies_to = 'model_08_event_risk_governor;model_05_alpha_confidence;model_06_position_projection;model_07_underlying_action;model_09_option_expression;source_09_event_risk_governor;feature_09_event_risk_governor;registry_current;openclaw_database',
    note = 'Audit follow-up resolved current-version physical numbering: live/current PostgreSQL table names, stored layer/model values, current registry rows, and current code defaults now follow the accepted nine-layer order. Historical migrations and old artifacts are intentionally not rewritten.',
    updated_at = NOW()
WHERE id = 'cfg_LPNA001';

UPDATE trading_registry
SET     key = 'LAYER_THREE_PLUS_SIX_MONTH_FOLD_MATERIALIZATION',
    payload = 'target_symbol_six_month_fold_not_month_local_run',
    path = 'trading-manager/src/trading_manager_tasks/layer_three_target_state.py;trading-manager/src/trading_manager_tasks/layer_eight_event_risk_governor.py;trading-manager/src/trading_manager_tasks/model_training_workflow.py',
    applies_to = 'model_worker_1;layer_03_target_state_vector;layers_03_09_stack;legacy_layer_08_event_risk_governor;layer_08_event_risk_governor;current_physical_names',
    note = 'Layer 3+ base-stack Model Worker stages run against one selected target/instrument over the complete six-month rolling fold. Local input materializers must accept start_month/end_month ranges and must not assume one chronological month per run. Layer 8 event-governor materialization remains a separate overlay surface.',
    updated_at = NOW()
WHERE id = 'cfg_FOLDMAT001';

UPDATE trading_registry
SET     key = 'MODEL_LAYER_CONCEPTUAL_REORDER_POLICY',
    payload = 'layer_01_market_regime;layer_02_sector_context;layer_03_target_state_vector;layer_04_event_failure_risk;layer_05_alpha_confidence;layer_06_position_projection;layer_07_underlying_action;layer_08_event_risk_governor;layer_09_trading_guidance',
    path = 'trading-model/docs/03_contracts.md;trading-model/docs/13_layer_04_event_failure_risk.md;trading-manager/docs/05_decision.md',
    applies_to = 'trading-model;trading-data;trading-manager;model_training_workflow;event_failure_risk_model;event_risk_governor;trading_guidance;current_physical_names',
    note = 'Active layer order after the Layer 8/9 swap: Layer 8 is EventRiskGovernor / EventIntelligenceOverlay for event-risk governance of the Layer 7 direct-underlying thesis; Layer 9 is TradingGuidance / OptionExpression / realtime handoff. Active script/package/table names use the current nine-layer numbering; historical/applied migration records may retain prior names.',
    updated_at = NOW()
WHERE id = 'cfg_MLRP003';

UPDATE trading_registry
SET     key = 'MODEL_PROMOTION_ACCEPTANCE_DECISION_RECEIPTS',
    payload = 'layer_1:market_regime_model:mdevrun_1d00f2757982bd63:mpcand_b79411e80a774787:mpdec_d743cb5dbc8159f2:deferred;layer_2:sector_context_model:mdevrun_00c81e53569941df:mpcand_a6044e72162553f9:mpdec_3ab83ea1f423326d:deferred;layer_3:target_state_vector_model:mdevrun_327616bb447ceb5b:mpcand_1b077bca49a18dbf:mpdec_70fef0f31847cc1c:deferred;layer_4:event_failure_risk_model:mdevrun_closeout_l04_no_eval_substrate_20260508:mpcand_6ab73401f22ab057:mpdec_76b07ea01a3f525b:deferred;layer_5:alpha_confidence_model:mdevrun_closeout_l05_no_eval_substrate_20260508:mpcand_72289e5cc95ae2d5:mpdec_9c3e19d6559ef55b:deferred;layer_6:position_projection_model:mdevrun_closeout_l06_no_eval_substrate_20260508:mpcand_622c6ffa9ffca030:mpdec_b118232e76fae092:deferred;layer_7:underlying_action_model:mdevrun_closeout_l07_no_eval_substrate_20260508:mpcand_d4911cef39a14b97:mpdec_fabc9c709149a698:deferred;layer_8:event_risk_governor:mdevrun_closeout_l08_no_eval_substrate_20260508:mpcand_9de333239d5c3f12:mpdec_e7448aaab1334345:deferred;layer_9:option_expression_model:missing_production_eval_substrate:no_persisted_decision_receipt:deferred',
    path = 'trading-model/docs/31_promotion_acceptance.md',
    applies_to = 'model_governance;model_promotion;promotion_decision;promotion_acceptance;layers_1_9',
    note = 'Persisted promotion acceptance decision/status entries mapped to the current conceptual layer order. Layers with reviewed manager decisions keep their receipt ids; Layer 9 is explicitly deferred until a residual-event-risk production evaluation substrate and persisted review decision exist. Deferred decisions leave active config pointers unchanged.',
    updated_at = NOW()
WHERE id = 'cfg_MPC001';

UPDATE trading_registry
SET     key = 'MODEL_PROMOTION_UNIFIED_TARGETS',
    payload = 'market_regime_model;sector_context_model;target_state_vector_model;event_failure_risk_model;alpha_confidence_model;position_projection_model;underlying_action_model;event_risk_governor;option_expression_model',
    path = 'trading-manager/docs/24_model_promotion.md',
    applies_to = 'model_promotion_review;layers_1_9;promotion_control_plane',
    note = 'Canonical stable model ids accepted by the unified manager-side promotion review request planner, ordered by current conceptual layer order. Physical model_NN names are implementation paths or SQL surfaces, not promotion-control-plane ids.',
    updated_at = NOW()
WHERE id = 'cfg_UMP002';

UPDATE trading_registry
SET     key = 'MODEL_WORKFLOW_SEGMENTED_LAYER_PROGRESSION_POLICY',
    payload = 'layer_01_background_panel_six_month_unit;layer_02_sector_panel_six_month_unit;layers_03_08_target_symbol_six_month_unit;layer_09_option_expression_after_target_chain_complete;selected_target_symbol_required_for_layer_03_plus;reviewed_exception_required_for_target_fanout',
    path = 'trading-manager/docs/26_historical_scheduler_runtime.md',
    applies_to = 'manager_model_training_workflow_plan;historical_training;scheduler;dataset_expansion;layer_01_market_regime;layer_02_sector_context;layer_03_target_state_vector;layer_04_event_failure_risk;model_05_alpha_confidence;model_06_position_projection;model_07_underlying_action;model_09_option_expression;model_08_event_risk_governor;current_physical_names',
    note = 'Formal workflow progression is segmented by dataset unit inside the same historical-modeling system service: Layers 1-2 use one six-month panel; Layers 3-8 run one selected target symbol over one six-month unit; Layer 8 EventRiskGovernor runs as the service-owned event-risk overlay lane. Current layer_09_option_expression remains the option-expression stage token.',
    updated_at = NOW()
WHERE id = 'cfg_MWFP002';

UPDATE trading_registry
SET     key = 'OPTION_EXPRESSION_BASELINE_LADDER',
    payload = 'no_option_expression;underlying_only_expression;naive_atm_nearest_expiration_call_put;fixed_delta_fixed_dte_option;layer_7_full_contract_fit_model',
    path = 'trading-model/docs/18_layer_09_trading_guidance.md',
    applies_to = 'option_expression_model;model_evaluation;promotion_evidence;baseline_ladder',
    note = 'Accepted Layer 9 option-expression evaluation baseline ladder. The current physical score/model namespace uses layer_09/model_09. The model must prove value versus no option, underlying-only expression, naive ATM option, fixed delta/DTE option, and full contract-fit model.',
    updated_at = NOW()
WHERE id = 'cfg_OERB001';

UPDATE trading_registry
SET     key = 'OPTION_EXPRESSION_BOUNDARY_POLICY',
    payload = 'option_expression_not_broker_order;selected_contract_ref_not_broker_order_id;selected_contract_not_send_order;contract_constraints_not_route_or_time_in_force;premium_risk_plan_not_account_mutation;planned_premium_budget_not_final_order_quantity;expression_confidence_not_final_approval;no_broker_mutation;single_leg_long_options;no_0dte;no_adjusted_contracts;maintain_or_no_trade_means_no_option_expression;preferred_delta_range_hard_filter;target_range_moneyness_guardrail',
    path = 'trading-model/docs/18_layer_09_trading_guidance.md',
    applies_to = 'option_expression_model;option_expression_plan;expression_vector;model_09_option_expression;underlying_action_plan;trading-execution',
    note = 'Layer 9 option-expression boundary policy: OptionExpressionModel produces an offline option-expression plan and expression vector. Current physical model_09/9_* names are active. It must not place orders, emit broker order fields, choose route/time-in-force, emit final order quantity, mutate broker/account state, create maintain/no-trade overlays in V1, use 0DTE in V1, use adjusted contracts in V1, select contracts outside the preferred delta policy, or select strikes outside coherent underlying-action target-range guardrails.',
    updated_at = NOW()
WHERE id = 'cfg_OEPB001';

UPDATE trading_registry
SET     key = 'OPTION_EXPRESSION_DELTA_POLICY',
    payload = 'preferred_abs_delta_range=0.35-0.65;avoid_deep_otm_lottery_contracts',
    path = 'trading-model/docs/18_layer_09_trading_guidance.md',
    applies_to = 'option_expression_model;option_expression_plan;contract_constraints;delta_policy',
    note = 'Accepted conservative Layer 9 V1 delta policy for single-leg long call/put expression. Future learned fit models may adjust by path quality, expected move, IV, liquidity, and theta pressure.',
    updated_at = NOW()
WHERE id = 'cfg_OEDLT001';

UPDATE trading_registry
SET     key = 'OPTION_EXPRESSION_DIAGNOSTIC_FIELD_FAMILIES',
    payload = '9_candidate_count;9_eligible_candidate_count;9_candidate_hard_filter_fail_reason_codes;9_contract_dte_fit_score;9_contract_spread_pct;9_contract_iv_rank;9_premium_risk_reason_codes;9_option_expression_reason_codes',
    path = 'trading-model/docs/18_layer_09_trading_guidance.md',
    applies_to = 'option_expression_model;option_expression_plan;expression_vector;diagnostics;explainability',
    note = 'Reviewed Layer 9 diagnostic field-family tokens for candidate counts, per-candidate hard-filter reason codes, contract fit attribution, premium-risk attribution, and expression reason codes. Diagnostics are not default scalar score-family rows.',
    updated_at = NOW()
WHERE id = 'cfg_OEPD001';

UPDATE trading_registry
SET     key = 'OPTION_EXPRESSION_DTE_POLICY',
    payload = '5min_15min:3-7_no_0dte;60min:7-14;390min:7-21;multi_day:21-45',
    path = 'trading-model/docs/18_layer_09_trading_guidance.md',
    applies_to = 'option_expression_model;option_expression_plan;contract_constraints;dte_policy',
    note = 'Accepted conservative Layer 9 V1 DTE policy. DTE is a range tied to Layer 7 holding-time assumptions; V1 avoids 0DTE and extreme short-DTE lottery contracts.',
    updated_at = NOW()
WHERE id = 'cfg_OEDTE001';

UPDATE trading_registry
SET     key = 'OPTION_EXPRESSION_EVALUATION_LABEL_FAMILIES',
    payload = 'realized_option_return_<horizon>;realized_option_mid_return_<horizon>;realized_option_bid_exit_return_<horizon>;realized_option_spread_cost_<horizon>;realized_iv_change_<horizon>;realized_theta_decay_<horizon>;realized_delta_path_exposure_<horizon>;underlying_target_hit_but_option_lost_label_<horizon>;option_no_expression_opportunity_cost_<horizon>;option_expression_avoided_loss_value_<horizon>;candidate_contract_utility_curve_<horizon>',
    path = 'trading-model/docs/18_layer_09_trading_guidance.md',
    applies_to = 'option_expression_model;model_evaluation;labels;leakage_controls',
    note = 'Reviewed Layer 9 offline evaluation label-family tokens. These labels must not be joined into inference rows.',
    updated_at = NOW()
WHERE id = 'cfg_OELBL001';

UPDATE trading_registry
SET     key = 'OPTION_EXPRESSION_MODEL_LAYER_POLICY',
    payload = 'layer_08_after_underlying_action;uses_underlying_action_plan;uses_option_chain_context;no_broker_mutation;model_09_physical_surface',
    path = 'trading-model/docs/18_layer_09_trading_guidance.md',
    applies_to = 'option_expression_model;model_09_option_expression;underlying_action_plan;underlying_action_vector;option_expression_plan;expression_vector',
    note = 'Layer policy for OptionExpressionModel: option expression is Layer 9, consumes Layer 7 underlying path assumptions plus option-chain context, and remains offline without broker mutation. Current physical names use model_09/9_*.',
    updated_at = NOW()
WHERE id = 'cfg_OEML001';

UPDATE trading_registry
SET     key = 'OPTION_EXPRESSION_MONEYNESS_GUARDRAIL',
    payload = 'bullish_call_strike_not_above_target_price_high;bearish_put_strike_not_below_target_price_low;apply_only_when_layer_7_target_range_is_directionally_coherent',
    path = 'trading-model/docs/18_layer_09_trading_guidance.md',
    applies_to = 'option_expression_model;option_expression_plan;contract_constraints;moneyness_policy;underlying_action_plan',
    note = 'Accepted Layer 9 V1 moneyness guardrail. Layer 8 uses Layer 7 target range to prevent lottery-like call strikes above coherent bullish target highs and put strikes below coherent bearish target lows. This is still offline contract selection, not execution.',
    updated_at = NOW()
WHERE id = 'cfg_OEMG001';

UPDATE trading_registry
SET     key = 'OPTION_EXPRESSION_RESOLVED_FIELD_FAMILIES',
    payload = '9_resolved_expression_type;9_resolved_option_right;9_resolved_dominant_horizon;9_resolved_selected_contract_ref;9_resolved_contract_fit_score;9_resolved_expression_confidence_score;9_resolved_no_option_reason_codes;9_resolved_reason_codes',
    path = 'trading-model/docs/18_layer_09_trading_guidance.md',
    applies_to = 'option_expression_plan;expression_vector;option_expression_model;model_09_option_expression;underlying_action_plan',
    note = 'Reviewed current 9_* resolved expression field-family tokens for Layer 9 option-expression. They communicate chosen option expression, selected point-in-time contract reference, fit/confidence, and no-option reason codes; they are not broker order fields.',
    updated_at = NOW()
WHERE id = 'cfg_OEPR001';

UPDATE trading_registry
SET     key = 'OPTION_EXPRESSION_TYPES',
    payload = 'long_call;long_put;no_option_expression',
    path = 'trading-model/docs/18_layer_09_trading_guidance.md',
    applies_to = 'option_expression_plan;option_expression_model;model_09_option_expression;expression_type_policy',
    note = 'Accepted Layer 9 V1 option-expression type vocabulary. Current physical model_09/9_* names are active. V1 supports single-leg long call, single-leg long put, and no-option-expression outcomes only.',
    updated_at = NOW()
WHERE id = 'cfg_OEPT001';

UPDATE trading_registry
SET     key = 'OPTION_EXPRESSION_VECTOR_HORIZONS',
    payload = '5min;15min;60min;390min',
    path = 'trading-model/docs/18_layer_09_trading_guidance.md',
    applies_to = 'expression_vector;option_expression_model;model_09_option_expression;option_expression_plan',
    note = 'Accepted OptionExpressionModel V1 horizons. 390min means one regular US equity session-equivalent horizon measured in tradable minutes; label builders must document same-session vs next-session-close resolution and use purge/embargo controls.',
    updated_at = NOW()
WHERE id = 'cfg_OEVH001';

UPDATE trading_registry
SET     key = 'OPTION_EXPRESSION_VECTOR_SCORE_FAMILIES',
    payload = '9_option_expression_eligibility_score_<horizon>;9_option_expression_direction_score_<horizon>;9_option_contract_fit_score_<horizon>;9_option_liquidity_fit_score_<horizon>;9_option_iv_fit_score_<horizon>;9_option_greek_fit_score_<horizon>;9_option_reward_risk_score_<horizon>;9_option_theta_risk_score_<horizon>;9_option_fill_quality_score_<horizon>;9_option_expression_confidence_score_<horizon>',
    path = 'trading-model/docs/18_layer_09_trading_guidance.md',
    applies_to = 'expression_vector;option_expression_model;model_09_option_expression;state_vector_value;option_expression_plan',
    note = 'Accepted current 9_* OptionExpressionModel scalar score-family tokens for Layer 9. These 10 families separate option-expression eligibility, signed expression direction, contract fit, liquidity fit, IV fit, Greek fit, reward/risk, theta risk, fill quality, and expression confidence.',
    updated_at = NOW()
WHERE id = 'cfg_OEVS001';

UPDATE trading_registry
SET     key = 'POSITION_PROJECTION_BOUNDARY_POLICY',
    payload = 'target_exposure_not_order_quantity;position_gap_not_execution_instruction;no_buy_sell_hold;no_instrument_selection;no_option_chain_features;point_in_time_position_cost_risk_only;final_adjusted_alpha_default',
    path = 'trading-model/docs/15_layer_06_position_projection.md',
    applies_to = 'position_projection_model;position_projection_vector;model_06_position_projection;underlying_action_model;underlying_action_plan;option_expression_model;model_09_option_expression',
    note = 'Layer 6 boundary policy: target exposure is abstract risk exposure, position gap is not an execution instruction, and PositionProjectionModel does not emit buy/sell/hold/open/close/reverse, choose instruments, read option chains, or mutate broker/account state. Layer 7 owns planned direct-underlying action; Layer 9 owns option expression.',
    updated_at = NOW()
WHERE id = 'cfg_PPVBP001';

UPDATE trading_registry
SET     key = 'PRICE_ACTION_EVENT_LAYER_POLICY',
    payload = 'layer_08_event_risk_governor_event_not_new_model_layer;feeds_target_event_failure_alpha_context_as_evidence;post_event_realization_is_label_only;no_action_or_execution_output',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'price_action;false_breakout;event_risk_governor;target_context_state;event_failure_risk_model;alpha_confidence_model;layer_08_event_risk_governor',
    note = 'Policy for false-breakout style price-action evidence: represent it as compact Layer 8 event-risk detector/residual evidence with source refs, without duplicating base bar/liquidity features, adding another standalone model layer, or emitting action/execution fields. Promotion into Layer 4 event-failure-risk scope requires reviewed evidence.',
    updated_at = NOW()
WHERE id = 'cfg_PAE002';

UPDATE trading_registry
SET     key = 'PRICE_ACTION_EVENT_TYPES',
    payload = 'false_breakout;false_breakdown;liquidity_sweep_high;liquidity_sweep_low;bull_trap;bear_trap',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'price_action;source_09_event_risk_governor;event_risk_governor;event_context_vector;equity_abnormal_activity_event',
    note = 'Canonical price-action event tokens for current model_08_event_risk_governor / Layer 8 EventRiskGovernor. They describe board/tape behavior used as event-risk evidence, not buy/sell/hold decisions or execution instructions.',
    updated_at = NOW()
WHERE id = 'cfg_PAE001';

UPDATE trading_registry
SET     key = 'SQL_LAYER_TABLE_NAMING_POLICY',
    payload = 'layer_owned_sql_tables_use_source_NN_feature_NN_model_NN_prefixes;layer_neutral_governance_control_receipt_registry_audit_tables_stay_unnumbered;layer_refs_live_in_fields_for_neutral_tables',
    path = '/root/projects/trading-manager/scripts/registry/rules/model-layer-naming.md',
    applies_to = 'trading_data;trading_model;trading_manager;sql_table_naming;model_layer_naming;dashboard_data_tables',
    note = 'Layer-owned SQL tables must expose the zero-padded model-layer number immediately after the surface stem, such as source_01_market_regime, feature_03_target_state_vector, and model_08_event_risk_governor. Layer-neutral governance/control/receipt/registry/audit tables must not invent fake layer prefixes; they carry layer references in fields when needed.',
    updated_at = NOW()
WHERE id = 'cfg_SQLLTN001';

UPDATE trading_registry
SET     key = 'UNDERLYING_ACTION_BOUNDARY_POLICY',
    payload = 'planned_underlying_action_not_broker_order;planned_quantity_not_final_order_quantity;entry_plan_not_order_type;stop_loss_price_not_broker_stop_order;take_profit_price_not_broker_limit_order;underlying_path_thesis_not_option_contract;no_option_contract_selection;no_broker_mutation',
    path = 'trading-model/docs/16_layer_07_underlying_action.md',
    applies_to = 'underlying_action_model;underlying_action_plan;underlying_action_vector;model_07_underlying_action;option_expression_model;model_09_option_expression;trading-execution',
    note = 'Layer 7 boundary policy: UnderlyingActionModel produces an offline direct underlying/spot action thesis for stock, ETF, or crypto-style candidates, with optional Layer 9 trading-guidance handoff. It must not place broker/exchange orders, emit broker order fields, choose option contracts, or mutate broker/account state.',
    updated_at = NOW()
WHERE id = 'cfg_UAPB001';

UPDATE trading_registry
SET     key = 'UNDERLYING_ACTION_RESOLVED_FIELD_FAMILIES',
    payload = '7_resolved_underlying_action_type;7_resolved_action_side;7_resolved_dominant_horizon;7_resolved_trade_eligibility_score;7_resolved_trade_intensity_score;7_resolved_entry_quality_score;7_resolved_action_confidence_score;7_resolved_reason_codes',
    path = 'trading-model/docs/16_layer_07_underlying_action.md',
    applies_to = 'underlying_action_plan;underlying_action_vector;underlying_action_model;model_07_underlying_action;option_expression_model;model_09_option_expression',
    note = 'Reviewed current 7_* resolved plan/handoff field-family tokens for communicating the Layer 7 direct-underlying action thesis to Layer 8 trading guidance and execution-side review. These are not broker order fields.',
    updated_at = NOW()
WHERE id = 'cfg_UAPR001';

UPDATE trading_registry
SET     key = 'FEATURE_08_OPTION_EXPRESSION',
    payload = 'feature_08_option_expression',
    path = 'trading-data/src/data_feature/feature_08_option_expression',
    applies_to = 'trading-data;trading-model;source_05_option_expression;option_expression_model;model_09_option_expression;option_expression_plan',
    note = 'Layer 9 option-expression candidate feature surface using current feature_08 data and model_09 physical names. trading-data derives point-in-time moneyness, spread/liquidity, IV, Greeks, and quality payloads from accepted source_05_option_expression rows; trading-model owns contract ranking and expression choice.',
    updated_at = NOW()
WHERE id = 'dki_OEFS001';

UPDATE trading_registry
SET     key = 'FEATURE_09_EVENT_RISK_GOVERNOR',
    payload = 'feature_09_event_risk_governor',
    path = 'trading-data/src/data_feature/feature_09_event_risk_governor',
    applies_to = 'trading-data;trading-model;source_09_event_risk_governor;event_risk_governor;model_08_event_risk_governor;event_context_vector',
    note = 'Current feature_09_event_risk_governor feature surface for Layer 8 EventRiskGovernor. trading-data derives point-in-time event-category, scope, dedup, source-priority, and quality payloads from accepted source_09_event_risk_governor rows; trading-model owns final event-risk context/intervention construction.',
    updated_at = NOW()
WHERE id = 'dki_EOFS001';

UPDATE trading_registry
SET     key = 'SOURCE_06_POSITION_EXECUTION',
    payload = 'source_06_position_execution',
    path = 'trading-data/src/data_source/source_06_position_execution',
    applies_to = 'trading-data;trading-model;option_expression_model;model_09_option_expression;selected_contract_tracking_source',
    note = '06 control-plane-facing selected-contract option time-series source for OptionExpressionModel replay/evaluation; fetches selected-contract option market data from feeds and writes trading_data.source_06_position_execution without emitting execution instructions.',
    updated_at = NOW()
WHERE id = 'dbu_EVTINPUT';

UPDATE trading_registry
SET     key = 'SOURCE_09_EVENT_RISK_GOVERNOR',
    payload = 'source_09_event_risk_governor',
    path = 'trading-data/src/data_source/source_09_event_risk_governor',
    applies_to = 'trading-data;trading-model;event_risk_governor;model_08_event_risk_governor',
    note = '04 control-plane-facing EventRiskGovernor data source; prepares one SQL event overview row per required event with details behind references.',
    updated_at = NOW()
WHERE id = 'dbu_PRKINPUT';

UPDATE trading_registry
SET     key = 'EVENT_FEED_ROW_COVERAGE',
    payload = 'event_feed_row_coverage',
    path = 'trading-manager/src/trading_manager_tasks/layer_eight_event_risk_governor.py',
    applies_to = 'manager_layer_eight_event_risk_governor_input_materialization;event_source_coverage;requested_window',
    note = 'Summary field reporting requested-window row counts by required event feed source for the current layer_08_event_risk_governor / Layer 9 coverage gate.',
    updated_at = NOW()
WHERE id = 'fld_L4EVTCOV002';

UPDATE trading_registry
SET     key = 'FEATURE_08_OPTION_EXPRESSION_GENERATE',
    payload = 'trading-data-feature-08-option-expression',
    path = '/root/projects/trading-data/src/data_feature/feature_08_option_expression/__main__.py',
    applies_to = 'trading-data;source_05_option_expression;feature_08_option_expression;option_expression_model;model_09_option_expression',
    note = 'Stable package CLI entrypoint for reading source_05_option_expression rows and writing feature_08_option_expression JSONB option-candidate feature blocks. The importable implementation lives under src/data_feature/feature_08_option_expression.',
    updated_at = NOW()
WHERE id = 'scr_F8OEGEN';

UPDATE trading_registry
SET     key = 'FEATURE_09_EVENT_RISK_GOVERNOR_GENERATE',
    payload = 'trading-data-feature-08-event-risk-governor',
    path = '/root/projects/trading-data/src/data_feature/feature_09_event_risk_governor/__main__.py',
    applies_to = 'trading-data;source_09_event_risk_governor;feature_09_event_risk_governor;event_risk_governor;model_08_event_risk_governor',
    note = 'Stable package CLI entrypoint for reading source_09_event_risk_governor rows and writing feature_09_event_risk_governor JSONB event overview feature blocks. The importable implementation lives under src/data_feature/feature_09_event_risk_governor.',
    updated_at = NOW()
WHERE id = 'scr_F4EOGEN';

UPDATE trading_registry
SET     key = 'LAYER_09_OPTION_EXPRESSION_FEATURE_GENERATION',
    payload = 'PYTHONPATH=src python3 scripts/tasks/execute_layer_nine_option_feature_generation.py --start-month ${START_MONTH} --end-month ${END_MONTH}',
    path = '/root/projects/trading-manager/scripts/tasks/execute_layer_nine_option_feature_generation.py',
    applies_to = 'layer_09_option_expression;feature_08_option_expression;source_05_option_expression;safe_offline_model_training',
    note = 'Manager-owned current layer_09_option_expression feature-stage adapter for Layer 9 option-expression. It writes a first-class no-provider/no-feature skip receipt when the reviewed gate has zero active target chains, or delegates to trading-data feature_08 option-expression generation after approved active-path acquisition.',
    updated_at = NOW()
WHERE id = 'scr_L8FEAT001';

UPDATE trading_registry
SET     key = 'LAYER_09_OPTION_EXPRESSION_GATE_REVIEW',
    payload = 'PYTHONPATH=src python3 scripts/tasks/review_layer_nine_option_expression_gate.py --start-month ${START_MONTH} --end-month ${END_MONTH} --write',
    path = '/root/projects/trading-manager/scripts/tasks/review_layer_nine_option_expression_gate.py',
    applies_to = 'layer_09_option_expression;option_expression_model;source_05_option_expression;autonomous_historical_provider_acquisition;safe_offline_model_training',
    note = 'Manager-owned review for current layer_09_option_expression acquisition at the Layer 9 option-expression boundary. Active target chains are prepared for autonomous option-snapshot acquisition; no manual provider gate is required.',
    updated_at = NOW()
WHERE id = 'scr_L8GATE001';

UPDATE trading_registry
SET     key = 'MANAGER_DISPATCH_LAYER_EIGHT_EVENT_FEED_BACKFILL',
    payload = 'PYTHONPATH=src python3 scripts/tasks/dispatch_event_feed_backfill.py',
    path = 'trading-manager/scripts/tasks/dispatch_event_feed_backfill.py;trading-manager/src/trading_manager_tasks/event_feed_dispatch.py',
    applies_to = 'layer_08_event_risk_governor;event_source_coverage;alpaca_news;gdelt_news;trading_economics_calendar_web;sec_company_financials',
    note = 'Validates or explicitly dispatches bounded Layer 8 event-risk-feed provider acquisition from prepared task keys. Provider calls require --execute-provider-calls; model activation, broker execution, account mutation, and dashboard read-model writes remain forbidden.',
    updated_at = NOW()
WHERE id = 'scr_L8EVTDIS001';

UPDATE trading_registry
SET     key = 'MANAGER_INVALIDATE_LAYER_EIGHT_EVENT_DOWNSTREAM_OUTPUTS',
    payload = 'PYTHONPATH=src python3 scripts/tasks/invalidate_layer_eight_event_downstream_outputs.py',
    path = 'trading-manager/scripts/tasks/invalidate_layer_eight_event_downstream_outputs.py;trading-manager/src/trading_manager_tasks/model_training_invalidation.py',
    applies_to = 'historical_modeling;legacy_layer_08_event_risk_governor;layer_08_event_risk_governor;model_05_alpha_confidence;model_06_position_projection;model_07_underlying_action;model_09_option_expression;stale_output_invalidation;current_physical_names',
    note = 'State-only helper that marks stale Layer 8 event-governor-dependent workflow stages rebuild-required after event-source contract repair. It does not delete artifacts, call providers, activate models, submit broker orders, mutate accounts, or write dashboard read models.',
    updated_at = NOW()
WHERE id = 'scr_L8EVTINV001';

UPDATE trading_registry
SET     key = 'MANAGER_MATERIALIZE_LAYER_EIGHT_EVENT_RISK_INPUTS',
    payload = 'PYTHONPATH=src python3 scripts/tasks/materialize_layer_eight_event_risk_governor_inputs.py --start-month ${START_MONTH} --end-month ${END_MONTH} --write',
    path = '/root/projects/trading-manager/scripts/tasks/materialize_layer_eight_event_risk_governor_inputs.py',
    applies_to = 'manager_layer_eight_event_risk_governor_input_materialization;legacy_layer_08_event_risk_governor;layer_08_event_risk_governor;source_09_event_risk_governor;model_training_workflow;current_physical_names',
    note = 'Callable manager entrypoint that materializes current source_09 / Layer 8 event-risk-governor rows from local detector outputs over existing reviewed Layer 2 feed artifacts without provider dispatch.',
    updated_at = NOW()
WHERE id = 'scr_L8ERGMAT001';

UPDATE trading_registry
SET     key = 'MANAGER_PLAN_EVENT_MODEL_REGENERATION',
    payload = 'PYTHONPATH=src python3 scripts/tasks/plan_event_model_regeneration.py --start-month ${START_MONTH} --end-month ${END_MONTH}',
    path = '/root/projects/trading-manager/scripts/tasks/plan_event_model_regeneration.py;/root/projects/trading-manager/src/trading_manager_tasks/event_model_regeneration_plan.py',
    applies_to = 'manager_event_model_regeneration_plan_v1;legacy_layer_08_event_risk_governor;layer_08_event_risk_governor;source_09_event_risk_governor;feature_09_event_risk_governor;model_08_event_risk_governor;storage_lifecycle_hold;current_physical_names',
    note = 'Builds the non-mutating EventRiskGovernor regeneration plan: preserve persistent Layer 1/2 data and valid base Layer 3-8 outputs where applicable, supersede old event-overlay or abnormal-activity-only Layer 9 artifacts, rebuild current Layer 8 event-risk surfaces only after reviewed event-feed coverage, and keep deletion dry-run-only until reviewed acceptance.',
    updated_at = NOW()
WHERE id = 'scr_L8ERGREG001';

UPDATE trading_registry
SET     key = 'MANAGER_PREPARE_LAYER_EIGHT_EVENT_FEED_BACKFILL',
    payload = 'PYTHONPATH=src python3 scripts/tasks/prepare_layer_eight_event_feed_backfill.py',
    path = 'trading-manager/scripts/tasks/prepare_layer_eight_event_feed_backfill.py;trading-manager/src/trading_manager_tasks/event_feed_backfill.py',
    applies_to = 'layer_08_event_risk_governor;event_source_coverage;alpaca_news;gdelt_news;trading_economics_calendar_web;sec_company_financials',
    note = 'Prepares reviewed monthly event-feed task keys required before rebuilding Layer 8 event-governor-dependent outputs. Preparation performs no provider calls, model activation, broker execution, account mutation, or dashboard read-model writes.',
    updated_at = NOW()
WHERE id = 'scr_L8EVTBF001';

UPDATE trading_registry
SET     key = 'MODEL_08_CPI_INFLATION_ASSOCIATION_READINESS_BUILD',
    payload = 'PYTHONPATH=src python3 scripts/models/model_08_event_risk_governor/build_cpi_inflation_association_readiness.py',
    path = '/root/projects/trading-model/scripts/models/model_08_event_risk_governor/build_cpi_inflation_association_readiness.py;/root/projects/trading-model/src/models/model_08_event_risk_governor/cpi_inflation_association_readiness.py',
    applies_to = 'cpi_inflation_association_readiness_v1;cpi_inflation_release;event_control_comparison;model_08_event_risk_governor;fine_grained_event_family_association',
    note = 'Builds the safe local CPI/inflation association-control readiness slice. It scans existing local calendar and ETF bar artifacts, emits CPI event labels, same-month control labels, and event/control comparisons, but keeps the family underpowered until enough local event months, official-source canonicalization, market/sector/target-state controls, and accepted surprise definitions exist. It performs no provider calls, model activation, broker/account mutation, or artifact deletion.',
    updated_at = NOW()
WHERE id = 'scr_M8ERGCPI001';

UPDATE trading_registry
SET     key = 'MODEL_09_OPTION_EXPRESSION_EVALUATE_PROMOTION_EVIDENCE',
    payload = 'python3 scripts/models/model_09_option_expression/evaluate_model_09_option_expression.py',
    path = '/root/projects/trading-model/scripts/models/model_09_option_expression/evaluate_model_09_option_expression.py',
    applies_to = 'trading-model;option_expression_model;model_09_option_expression;option_expression_plan;model_evaluation;promotion_evidence',
    note = 'Stable callable entrypoint for building local/fixture OptionExpressionModel evaluation labels and conservative promotion evidence summary. It does not write governance rows or activate configs.',
    updated_at = NOW()
WHERE id = 'scr_M8OEEVAL';

UPDATE trading_registry
SET     key = 'MODEL_09_OPTION_EXPRESSION_GENERATE',
    payload = 'python3 scripts/models/model_09_option_expression/generate_model_09_option_expression.py',
    path = '/root/projects/trading-model/scripts/models/model_09_option_expression/generate_model_09_option_expression.py',
    applies_to = 'trading-model;option_expression_model;model_09_option_expression;option_expression_plan;underlying_action_plan;source_05_option_expression',
    note = 'Stable callable entrypoint for generating deterministic Layer 7 OptionExpressionModel option_expression_plan rows.',
    updated_at = NOW()
WHERE id = 'scr_M8OEGEN';

UPDATE trading_registry
SET     key = 'MODEL_09_OPTION_EXPRESSION_REVIEW_PROMOTION',
    payload = 'python3 scripts/models/model_09_option_expression/review_option_expression_promotion.py',
    path = '/root/projects/trading-model/scripts/models/model_09_option_expression/review_option_expression_promotion.py',
    applies_to = 'trading-model;option_expression_model;model_09_option_expression;model_evaluation;promotion_review',
    note = 'Stable callable conservative promotion-review wrapper for OptionExpressionModel. Fixture/local evidence must defer until real-data thresholds, baseline improvement, split stability, and leakage gates are reviewed and accepted.',
    updated_at = NOW()
WHERE id = 'scr_M8OEREV';

UPDATE trading_registry
SET     key = 'MODEL_08_PRICE_ANOMALY_EVENT_DISCOVERY_BUILD',
    payload = 'PYTHONPATH=src python3 scripts/models/model_08_event_risk_governor/build_price_anomaly_event_discovery.py',
    path = '/root/projects/trading-model/scripts/models/model_08_event_risk_governor/build_price_anomaly_event_discovery.py;/root/projects/trading-model/src/models/model_08_event_risk_governor/price_anomaly_event_discovery.py',
    applies_to = 'price_anomaly_event_discovery_v1;price_anomaly_event_discovery_summary_v1;model_08_event_risk_governor;reverse_event_family_discovery',
    note = 'Builds the reverse price-anomaly/event-family discovery artifact. It starts from local price anomalies, scans nearby event-family mentions for enrichment/commonality, and performs no provider calls, model training, activation, broker/account mutation, destructive SQL, or artifact deletion.',
    updated_at = NOW()
WHERE id = 'scr_M8ERGPA001';

UPDATE trading_registry
SET     key = 'MODEL_08_RESIDUAL_ANOMALY_EVENT_DISCOVERY_BUILD',
    payload = 'PYTHONPATH=src python3 scripts/models/model_08_event_risk_governor/build_residual_anomaly_event_discovery.py',
    path = '/root/projects/trading-model/scripts/models/model_08_event_risk_governor/build_residual_anomaly_event_discovery.py;/root/projects/trading-model/src/models/model_08_event_risk_governor/residual_anomaly_event_discovery.py',
    applies_to = 'residual_anomaly_event_discovery_v1;residual_anomaly_event_discovery_summary_v1;event_family_strategy_promotion_review_packet_v1;model_08_event_risk_governor;event_observation_pool;event_strategy_promotion_review;event_failure_risk_model;current_physical_names',
    note = 'Builds the EventRiskGovernor residual-anomaly event discovery artifact from Layers 1-8 base-stack evaluation residuals. The builder searches nearby PIT event families for explanations, observation-pool candidates, and Layer 4 event-failure-risk promotion review packets. It is a registered callable integration surface under the current MODEL_09 physical namespace only: no provider calls, daemon start, model activation, broker/account mutation, destructive SQL, artifact deletion, or automatic event-family promotion.',
    updated_at = NOW()
WHERE id = 'scr_M8ERGRD001';

UPDATE trading_registry
SET     key = 'MODEL_08_EVENT_FAMILY_ALL_ASSOCIATION_BUILD',
    payload = 'PYTHONPATH=src python3 scripts/models/model_08_event_risk_governor/build_event_family_all_association.py',
    path = '/root/projects/trading-model/scripts/models/model_08_event_risk_governor/build_event_family_all_association.py;/root/projects/trading-model/src/models/model_08_event_risk_governor/event_family_all_association.py',
    applies_to = 'event_family_all_association_v1;event_family_all_association_summary_v1;model_08_event_risk_governor;event_family_price_association',
    note = 'Builds the local all-family event/price association measurement. It emits all 29 event-family rows, separates accepted prior risk/control associations from local keyword/proxy screening associations, no-local-label data gaps, and required-precondition blockers, and performs no provider calls, model training, activation, broker/account mutation, destructive SQL, or artifact deletion.',
    updated_at = NOW()
WHERE id = 'scr_M8ERGAA001';

UPDATE trading_registry
SET     key = 'MODEL_08_EVENT_FAMILY_BATCH_CATALOG_BUILD',
    payload = 'PYTHONPATH=src python3 scripts/models/model_08_event_risk_governor/build_event_family_batch_catalog.py',
    path = '/root/projects/trading-model/scripts/models/model_08_event_risk_governor/build_event_family_batch_catalog.py;/root/projects/trading-model/src/models/model_08_event_risk_governor/event_family_batch_catalog.py',
    applies_to = 'event_family_batch_catalog_v1;event_family_batch_summary_v1;event_family_batch_queue;event_family_first_pass_packet_v1;event_family_blocker_queue;event_family_scouting;model_08_event_risk_governor;fine_grained_event_family_association',
    note = 'Builds the non-mutating fine-grained event-family batch catalog for current model_08_event_risk_governor / Layer 8 EventRiskGovernor association scouting. Routing buckets such as symbol_news, sector_news, macro_news, sec_filing, and earnings_guidance are split into mechanism-level first-pass family packets, a priority queue, and blocker queue before any price/path association study, risk promotion, or alpha claim. The helper performs no provider calls, model activation, broker/account mutation, or artifact deletion.',
    updated_at = NOW()
WHERE id = 'scr_M8ERGFAM001';

UPDATE trading_registry
SET     key = 'MODEL_08_EVENT_FAMILY_EMPIRICAL_COVERAGE_BUILD',
    payload = 'PYTHONPATH=src python3 scripts/models/model_08_event_risk_governor/build_event_family_empirical_coverage.py',
    path = '/root/projects/trading-model/scripts/models/model_08_event_risk_governor/build_event_family_empirical_coverage.py;/root/projects/trading-model/src/models/model_08_event_risk_governor/event_family_empirical_coverage.py',
    applies_to = 'event_family_empirical_coverage_v1;event_family_empirical_coverage_summary_v1;model_08_event_risk_governor;fine_grained_event_family_association',
    note = 'Builds the safe local all-family EventRiskGovernor empirical coverage/readiness scan. It uses existing local source/study artifacts only to identify families with existing empirical artifacts, candidate events needing interpretation and matched controls, missing source/parser coverage, PIT baseline blockers, residual-detector blockers, liquidity/depth blockers, and revised-definition blockers. It performs no provider calls, training, activation, broker/account mutation, destructive SQL, artifact deletion, or final alpha/risk promotion.',
    updated_at = NOW()
WHERE id = 'scr_M8ERGECS001';

UPDATE trading_registry
SET     key = 'MODEL_08_EVENT_FAMILY_PRECONDITION_COMPLETION_BUILD',
    payload = 'PYTHONPATH=src python3 scripts/models/model_08_event_risk_governor/build_event_family_precondition_completion.py',
    path = '/root/projects/trading-model/scripts/models/model_08_event_risk_governor/build_event_family_precondition_completion.py;/root/projects/trading-model/src/models/model_08_event_risk_governor/event_family_precondition_completion.py',
    applies_to = 'event_family_precondition_completion_v1;event_family_scouting_packet_v1;event_family_precondition_completion_summary_v1;model_08_event_risk_governor;fine_grained_event_family_association',
    note = 'Builds all-family EventRiskGovernor precondition packets before final association judgment. It emits one maintained event_family_scouting_packet_v1 for each of 29 fine-grained families, defining source precedence, point-in-time clocks, baselines, matched controls, label windows, residual requirements, liquidity requirements, and early-stop gates. It fills the missing-packet governance gap but performs no provider calls, training, activation, broker/account mutation, destructive SQL, artifact deletion, or final alpha/risk promotion.',
    updated_at = NOW()
WHERE id = 'scr_M8ERGPRC001';

UPDATE trading_registry
SET     key = 'MODEL_08_EVENT_FAMILY_REMAINING_ACCEPTANCE_BUILD',
    payload = 'PYTHONPATH=src python3 scripts/models/model_08_event_risk_governor/build_event_family_remaining_acceptance.py',
    path = '/root/projects/trading-model/scripts/models/model_08_event_risk_governor/build_event_family_remaining_acceptance.py;/root/projects/trading-model/src/models/model_08_event_risk_governor/event_family_remaining_acceptance.py',
    applies_to = 'event_family_remaining_acceptance_v1;event_family_remaining_acceptance_summary_v1;model_08_event_risk_governor;fine_grained_event_family_association',
    note = 'Builds the safe local remaining event-family acceptance artifact. It accounts for all 29 fine-grained families, separates risk/control candidates from packet/baseline/residual/liquidity blockers, defers the current option-abnormality definition as low-signal, and promotes no standalone directional alpha. It performs no provider calls, model activation, broker/account mutation, or artifact deletion.',
    updated_at = NOW()
WHERE id = 'scr_M8ERGREM001';

UPDATE trading_registry
SET     key = 'MODEL_08_EVENT_FAMILY_THRESHOLD_GRADING_BUILD',
    payload = 'PYTHONPATH=src python3 scripts/models/model_08_event_risk_governor/build_event_family_threshold_grading.py',
    path = '/root/projects/trading-model/scripts/models/model_08_event_risk_governor/build_event_family_threshold_grading.py;/root/projects/trading-model/src/models/model_08_event_risk_governor/event_family_threshold_grading.py',
    applies_to = 'event_family_threshold_grading_v1;event_family_threshold_grading_summary_v1;model_08_event_risk_governor;event_family_threshold_queue',
    note = 'Builds the EventRiskGovernor event-family threshold/grading queue. It removes measured no-clear families from the active threshold queue while preserving audit artifacts, keeps accepted risk/control seeds and expanded screening candidates, and performs no provider calls, model training, activation, broker/account mutation, destructive SQL, or artifact deletion.',
    updated_at = NOW()
WHERE id = 'scr_M8ERGTH001';

UPDATE trading_registry
SET     key = 'MODEL_08_EVENT_LAYER_FINAL_JUDGMENT_BUILD',
    payload = 'PYTHONPATH=src python3 scripts/models/model_08_event_risk_governor/build_event_layer_final_judgment.py',
    path = '/root/projects/trading-model/scripts/models/model_08_event_risk_governor/build_event_layer_final_judgment.py;/root/projects/trading-model/src/models/model_08_event_risk_governor/event_layer_final_judgment.py',
    applies_to = 'event_layer_final_judgment_v1;event_layer_final_judgment_summary_v1;model_08_event_risk_governor;event_risk_governor_final_posture',
    note = 'Builds the final current-cycle EventRiskGovernor posture judgment from reviewed local evidence. The accepted posture is a bounded EventRiskGovernor/EventIntelligenceOverlay, not a standalone event-alpha model. It permits only risk/control outputs from current evidence, accepts CPI surprise and earnings scheduled shells for risk/control only, accepts zero standalone directional-alpha event families, and performs no provider calls, training, activation, broker/account mutation, destructive SQL, or artifact deletion.',
    updated_at = NOW()
WHERE id = 'scr_M8ERGFJ001';

UPDATE trading_registry
SET     key = 'MODEL_08_EVENT_OBSERVATION_POOL_POLICY_BUILD',
    payload = 'PYTHONPATH=src python3 scripts/models/model_08_event_risk_governor/build_event_observation_pool_policy.py',
    path = '/root/projects/trading-model/scripts/models/model_08_event_risk_governor/build_event_observation_pool_policy.py;/root/projects/trading-model/src/models/model_08_event_risk_governor/event_observation_pool_policy.py',
    applies_to = 'event_observation_pool_policy_v1;event_observation_pool_policy_summary_v1;model_08_event_risk_governor;event_observation_pool;event_strategy_promotion_review',
    note = 'Builds the EventRiskGovernor event observation-pool and promotion policy artifact. It separates historical all-event residual-anomaly research from realtime observation-pool monitoring, and requires script-emitted evidence plus agent review before any event family is promoted from correction overlay to strategy-decision scope.',
    updated_at = NOW()
WHERE id = 'scr_M8ERGOP001';

UPDATE trading_registry
SET     key = 'MODEL_08_EVENT_PRICE_ASSOCIATION_READINESS_BUILD',
    payload = 'PYTHONPATH=src python3 scripts/models/model_08_event_risk_governor/build_event_price_association_readiness.py',
    path = '/root/projects/trading-model/scripts/models/model_08_event_risk_governor/build_event_price_association_readiness.py;/root/projects/trading-model/src/models/model_08_event_risk_governor/event_price_association_readiness.py',
    applies_to = 'event_price_association_readiness_batch_v1;event_price_association_family_readiness;event_price_association_candidate_events;event_price_association_price_labels;model_08_event_risk_governor;fine_grained_event_family_association',
    note = 'Builds the safe local first event-price association readiness slice for selected high-priority EventRiskGovernor families. It inventories existing local artifacts, emits candidate-event/readiness/price-label diagnostics where possible, keeps underpowered or unstandardized families blocked, and performs no provider calls, model activation, broker/account mutation, or artifact deletion.',
    updated_at = NOW()
WHERE id = 'scr_M8ERGPAR001';

UPDATE trading_registry
SET     key = 'MODEL_08_EVENT_RISK_GOVERNOR_ACCEPTANCE_REPORT_BUILD',
    payload = 'PYTHONPATH=src python3 scripts/models/model_08_event_risk_governor/build_event_model_acceptance_report.py',
    path = '/root/projects/trading-model/scripts/models/model_08_event_risk_governor/build_event_model_acceptance_report.py;/root/projects/trading-model/src/models/model_08_event_risk_governor/event_model_acceptance.py',
    applies_to = 'event_model_acceptance_report_v1;model_08_event_risk_governor;event_risk_governor;event_family_scouting;storage_lifecycle_hold',
    note = 'Builds the accepted event-model acceptance report: Layer 9 remains a bounded EventRiskGovernor / EventIntelligenceOverlay, broad event alpha and signed earnings/guidance alpha remain blocked, diagnostic artifacts are preserved, and storage deletion stays on hold until reviewed regeneration completes.',
    updated_at = NOW()
WHERE id = 'scr_M8ERGCLS001';

UPDATE trading_registry
SET     key = 'MODEL_08_EVENT_RISK_GOVERNOR_EVALUATE_PROMOTION_EVIDENCE',
    payload = 'python3 scripts/models/model_08_event_risk_governor/evaluate_model_08_event_risk_governor.py',
    path = '/root/projects/trading-model/scripts/models/model_08_event_risk_governor/evaluate_model_08_event_risk_governor.py',
    applies_to = 'trading-model;event_risk_governor;model_08_event_risk_governor;event_context_vector;model_evaluation;promotion_evidence',
    note = 'Stable callable entrypoint for building local/fixture EventRiskGovernor evaluation labels and conservative promotion evidence summary. It does not write governance rows or activate configs.',
    updated_at = NOW()
WHERE id = 'scr_M8ERGEVAL';

UPDATE trading_registry
SET     key = 'MODEL_08_EVENT_RISK_GOVERNOR_GENERATE',
    payload = 'python3 scripts/models/model_08_event_risk_governor/generate_model_08_event_risk_governor.py',
    path = '/root/projects/trading-model/scripts/models/model_08_event_risk_governor/generate_model_08_event_risk_governor.py',
    applies_to = 'trading-model;event_risk_governor;model_08_event_risk_governor;event_context_vector;source_09_event_risk_governor',
    note = 'Stable callable entrypoint for generating deterministic current model_08_event_risk_governor / Layer 8 EventRiskGovernor event-risk context/intervention rows from local/fixture event-risk input evidence.',
    updated_at = NOW()
WHERE id = 'scr_M8ERGGEN';

UPDATE trading_registry
SET     key = 'MODEL_08_EVENT_RISK_GOVERNOR_REVIEW_PROMOTION',
    payload = 'python3 scripts/models/model_08_event_risk_governor/review_event_risk_governor_promotion.py',
    path = '/root/projects/trading-model/scripts/models/model_08_event_risk_governor/review_event_risk_governor_promotion.py',
    applies_to = 'trading-model;event_risk_governor;model_08_event_risk_governor;model_evaluation;promotion_review',
    note = 'Stable callable conservative promotion-review wrapper for EventRiskGovernor. Fixture/local evidence must defer until real-data thresholds, baseline improvement, split stability, and leakage gates are reviewed and accepted.',
    updated_at = NOW()
WHERE id = 'scr_M8ERGREV';

UPDATE trading_registry
SET     key = 'MODEL_EARNINGS_GUIDANCE_ARTIFACT_COVERAGE_SCOUT',
    payload = 'PYTHONPATH=src python3 scripts/models/model_08_event_risk_governor/run_earnings_guidance_artifact_coverage_scout.py',
    path = 'trading-model/scripts/models/model_08_event_risk_governor/run_earnings_guidance_artifact_coverage_scout.py',
    applies_to = 'earnings_guidance_event_family;event_family_scouting_packet_v1;event_risk_governor;model_promotion',
    note = 'Deterministic local coverage gate for official company filing/release/transcript text artifacts required before guidance interpretation; performs no provider calls.',
    updated_at = NOW()
WHERE id = 'scr_EGACS001';

UPDATE trading_registry
SET     key = 'MODEL_EARNINGS_GUIDANCE_BASELINE_SOURCE_AUDIT',
    payload = 'PYTHONPATH=src python3 scripts/models/model_08_event_risk_governor/run_earnings_guidance_baseline_source_audit.py',
    path = 'trading-model/scripts/models/model_08_event_risk_governor/run_earnings_guidance_baseline_source_audit.py',
    applies_to = 'earnings_guidance_event_family;expectation_baseline;event_risk_governor;model_promotion',
    note = 'Deterministic local audit of already captured calendar artifacts as point-in-time expectation baseline candidates; performs no provider calls.',
    updated_at = NOW()
WHERE id = 'scr_EGBS001';

UPDATE trading_registry
SET     key = 'MODEL_EARNINGS_GUIDANCE_CURRENT_PRIOR_COMPARISON_READINESS',
    payload = 'PYTHONPATH=src python3 scripts/models/model_08_event_risk_governor/run_earnings_guidance_current_prior_comparison_readiness.py',
    path = 'trading-model/scripts/models/model_08_event_risk_governor/run_earnings_guidance_current_prior_comparison_readiness.py',
    applies_to = 'earnings_guidance_event_family;prior_company_guidance;current_guidance_comparison;event_risk_governor',
    note = 'No-provider readiness pass that joins prior company-guidance context, current official guidance-context review rows, and official result artifacts before any raise/cut or signed-direction claim.',
    updated_at = NOW()
WHERE id = 'scr_CPGC001';

UPDATE trading_registry
SET     key = 'MODEL_EARNINGS_GUIDANCE_EVENT_ALONE_STUDY',
    payload = 'PYTHONPATH=src python3 scripts/models/model_08_event_risk_governor/run_earnings_guidance_event_alone_study.py',
    path = 'trading-model/scripts/models/model_08_event_risk_governor/run_earnings_guidance_event_alone_study.py',
    applies_to = 'earnings_guidance_event_family;event_family_scouting_packet_v1;activity_price_relationship_study;event_risk_governor',
    note = 'Deterministic local study entrypoint that tests canonical Nasdaq earnings-calendar shells against same-symbol non-earnings controls using daily equity bars. The study itself performs no provider calls.',
    updated_at = NOW()
WHERE id = 'scr_EGEA001';

UPDATE trading_registry
SET     key = 'MODEL_EARNINGS_GUIDANCE_EVENT_SCOUTING_STUDY',
    payload = 'PYTHONPATH=src python3 scripts/models/model_08_event_risk_governor/run_earnings_guidance_event_scouting.py',
    path = 'trading-model/scripts/models/model_08_event_risk_governor/run_earnings_guidance_event_scouting.py',
    applies_to = 'earnings_guidance_event_family;event_family_scouting_packet_v1;activity_price_relationship_study;event_risk_governor',
    note = 'Deterministic local study entrypoint that joins option-abnormality windows with reviewed Nasdaq earnings-calendar shells and filters matched controls to verified non-earnings dates. It performs no provider calls.',
    updated_at = NOW()
WHERE id = 'scr_EGSS001';

UPDATE trading_registry
SET     key = 'MODEL_EARNINGS_GUIDANCE_EXPECTATION_BASELINE_READINESS',
    payload = 'PYTHONPATH=src python3 scripts/models/model_08_event_risk_governor/run_earnings_guidance_expectation_baseline_readiness.py',
    path = 'trading-model/scripts/models/model_08_event_risk_governor/run_earnings_guidance_expectation_baseline_readiness.py',
    applies_to = 'earnings_guidance_event_family;event_family_scouting_packet_v1;event_risk_governor;model_promotion',
    note = 'Deterministic local readiness gate that validates point-in-time expectation baseline artifacts before any signed earnings/guidance claim; performs no provider calls.',
    updated_at = NOW()
WHERE id = 'scr_EGEB001';

UPDATE trading_registry
SET     key = 'MODEL_EARNINGS_GUIDANCE_INTERPRETATION_REVIEW',
    payload = 'PYTHONPATH=src python3 scripts/models/model_08_event_risk_governor/run_earnings_guidance_interpretation_review.py',
    path = 'trading-model/scripts/models/model_08_event_risk_governor/run_earnings_guidance_interpretation_review.py',
    applies_to = 'earnings_guidance_event_family;event_family_scouting_packet_v1;event_risk_governor;model_promotion',
    note = 'Deterministic local review that separates partial official guidance context from rejected boilerplate/accounting/risk language; performs no provider calls and makes no signed claims.',
    updated_at = NOW()
WHERE id = 'scr_EGIR001';

UPDATE trading_registry
SET     key = 'MODEL_EARNINGS_GUIDANCE_PRIOR_GUIDANCE_EXHIBIT_EXTRACTION',
    payload = 'PYTHONPATH=src python3 scripts/models/model_08_event_risk_governor/run_earnings_guidance_prior_guidance_exhibit_extraction.py',
    path = 'trading-model/scripts/models/model_08_event_risk_governor/run_earnings_guidance_prior_guidance_exhibit_extraction.py',
    applies_to = 'earnings_guidance_event_family;prior_company_guidance;expectation_baseline;event_risk_governor',
    note = 'No-provider extraction pass that reviews official prior-quarter earnings/outlook exhibits for prior-company-guidance baseline context.',
    updated_at = NOW()
WHERE id = 'scr_PGEE001';

UPDATE trading_registry
SET     key = 'MODEL_EARNINGS_GUIDANCE_PRIOR_GUIDANCE_EXTRACTION',
    payload = 'PYTHONPATH=src python3 scripts/models/model_08_event_risk_governor/run_earnings_guidance_prior_guidance_extraction.py',
    path = 'trading-model/scripts/models/model_08_event_risk_governor/run_earnings_guidance_prior_guidance_extraction.py',
    applies_to = 'earnings_guidance_event_family;prior_company_guidance;expectation_baseline;event_risk_governor',
    note = 'No-provider extraction pass that accepts explicit prior official guidance/outlook context and rejects generic forward-looking boilerplate.',
    updated_at = NOW()
WHERE id = 'scr_POGE001';

UPDATE trading_registry
SET     key = 'MODEL_EARNINGS_GUIDANCE_PRIOR_OFFICIAL_BASELINE_SOURCE_AUDIT',
    payload = 'PYTHONPATH=src python3 scripts/models/model_08_event_risk_governor/run_earnings_guidance_prior_official_baseline_audit.py',
    path = 'trading-model/scripts/models/model_08_event_risk_governor/run_earnings_guidance_prior_official_baseline_audit.py',
    applies_to = 'earnings_guidance_event_family;prior_company_guidance;expectation_baseline;event_risk_governor',
    note = 'No-provider model audit that consumes SEC submission rows and selects pre-event official filing candidates for prior-company-guidance baselines.',
    updated_at = NOW()
WHERE id = 'scr_POGB001';

UPDATE trading_registry
SET     key = 'MODEL_EARNINGS_GUIDANCE_PRIOR_OFFICIAL_DOCUMENT_COVERAGE',
    payload = 'PYTHONPATH=src python3 scripts/models/model_08_event_risk_governor/run_earnings_guidance_prior_official_document_coverage.py',
    path = 'trading-model/scripts/models/model_08_event_risk_governor/run_earnings_guidance_prior_official_document_coverage.py',
    applies_to = 'earnings_guidance_event_family;prior_company_guidance;expectation_baseline;event_risk_governor',
    note = 'No-provider coverage check that confirms selected prior official filing documents have local text artifacts before reviewed prior-guidance extraction.',
    updated_at = NOW()
WHERE id = 'scr_POGB002';

UPDATE trading_registry
SET     key = 'MODEL_EARNINGS_GUIDANCE_READINESS_SCOUT',
    payload = 'PYTHONPATH=src python3 scripts/models/model_08_event_risk_governor/run_earnings_guidance_readiness_scout.py',
    path = 'trading-model/scripts/models/model_08_event_risk_governor/run_earnings_guidance_readiness_scout.py',
    applies_to = 'earnings_guidance_event_family;event_family_scouting_packet_v1;event_risk_governor;model_promotion',
    note = 'Deterministic local readiness audit for official guidance interpretation, expectation baselines, and signed-direction eligibility; performs no provider calls.',
    updated_at = NOW()
WHERE id = 'scr_EGRS002';

UPDATE trading_registry
SET     key = 'MODEL_EARNINGS_GUIDANCE_RESULT_ARTIFACT_SCOUT',
    payload = 'PYTHONPATH=src python3 scripts/models/model_08_event_risk_governor/run_earnings_guidance_result_artifact_scout.py',
    path = 'trading-model/scripts/models/model_08_event_risk_governor/run_earnings_guidance_result_artifact_scout.py',
    applies_to = 'earnings_guidance_event_family;event_family_scouting_packet_v1;activity_price_relationship_study;event_risk_governor',
    note = 'Deterministic local study entrypoint that joins canonical earnings shells to official SEC submission/companyfacts artifacts and records partial result interpretation without claiming guidance surprise or signed alpha.',
    updated_at = NOW()
WHERE id = 'scr_EGRS001';

UPDATE trading_registry
SET     key = 'MODEL_EARNINGS_GUIDANCE_TEXT_CANDIDATE_SCOUT',
    payload = 'PYTHONPATH=src python3 scripts/models/model_08_event_risk_governor/run_earnings_guidance_text_candidate_scout.py',
    path = 'trading-model/scripts/models/model_08_event_risk_governor/run_earnings_guidance_text_candidate_scout.py',
    applies_to = 'earnings_guidance_event_family;event_family_scouting_packet_v1;event_risk_governor;model_promotion',
    note = 'Deterministic local scout that extracts guidance/outlook-like candidate spans from acquired official document text; candidates remain review-required and perform no provider calls.',
    updated_at = NOW()
WHERE id = 'scr_EGTCS001';

UPDATE trading_registry
SET     key = 'MODEL_EARNINGS_OPTION_ABNORMALITY_SPLIT_SCOUT',
    payload = 'PYTHONPATH=src python3 scripts/models/model_08_event_risk_governor/run_earnings_option_abnormality_split_scout.py',
    path = 'trading-model/scripts/models/model_08_event_risk_governor/run_earnings_option_abnormality_split_scout.py',
    applies_to = 'earnings_guidance_event_family;option_derivatives_abnormality;event_family_scouting_packet_v1;activity_price_relationship_study;event_risk_governor',
    note = 'Deterministic local study entrypoint that joins canonical earnings shells to reviewed option-abnormality evidence and blocks the amplifier claim when verified earnings-without-option-abnormality controls are absent.',
    updated_at = NOW()
WHERE id = 'scr_EOAS001';

UPDATE trading_registry
SET     key = 'MODEL_EARNINGS_OPTION_CONTROL_VERIFICATION',
    payload = 'PYTHONPATH=src python3 scripts/models/model_08_event_risk_governor/run_earnings_option_control_verification.py',
    path = 'trading-model/scripts/models/model_08_event_risk_governor/run_earnings_option_control_verification.py',
    applies_to = 'earnings_guidance_event_family;option_derivatives_abnormality;event_family_scouting_packet_v1;activity_price_relationship_study;event_risk_governor',
    note = 'Deterministic local summarizer for contract-level earnings option-event probes; records whether sampled earnings-without-option-abnormality controls exist without making provider calls itself.',
    updated_at = NOW()
WHERE id = 'scr_EOCV001';

UPDATE trading_registry
SET     key = 'MODEL_OPTION_ABNORMALITY_NON_EARNINGS_SATURATION',
    payload = 'PYTHONPATH=src python3 scripts/models/model_08_event_risk_governor/run_option_abnormality_non_earnings_saturation.py',
    path = 'trading-model/scripts/models/model_08_event_risk_governor/run_option_abnormality_non_earnings_saturation.py',
    applies_to = 'option_derivatives_abnormality;earnings_guidance_event_family;activity_price_relationship_study;event_risk_governor',
    note = 'Deterministic local diagnostic that checks whether reviewed non-earnings symbol/date windows can furnish clean no-option-abnormality controls under the current option-event standard.',
    updated_at = NOW()
WHERE id = 'scr_OANS001';

UPDATE trading_registry
SET     key = 'MODEL_SAME_SYMBOL_NON_EARNINGS_OPTION_CONTROL_VERIFICATION',
    payload = 'PYTHONPATH=src python3 scripts/models/model_08_event_risk_governor/run_same_symbol_non_earnings_option_control_verification.py',
    path = 'trading-model/scripts/models/model_08_event_risk_governor/run_same_symbol_non_earnings_option_control_verification.py',
    applies_to = 'earnings_guidance_event_family;option_derivatives_abnormality;event_family_scouting_packet_v1;activity_price_relationship_study;event_risk_governor',
    note = 'Deterministic local summarizer for same-symbol non-earnings option-event receipt controls; records whether clean no-option-abnormality controls exist without making provider calls itself.',
    updated_at = NOW()
WHERE id = 'scr_SSNEOCV001';

UPDATE trading_registry
SET     key = 'EVENT_CONTAGION_RISK_SCORE_BY_HORIZON',
    payload = '8_event_contagion_risk_score_<horizon>',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'event_context_vector;model_08_event_risk_governor;event_risk_governor;model_evaluation;promotion_evidence',
    note = 'current model_08_event_risk_governor / Layer 8 EventRiskGovernor high-is-bad score family for cross-scope event transmission or contagion risk by horizon.',
    updated_at = NOW()
WHERE id = 'fld_EOMV1010';

UPDATE trading_registry
SET     key = 'EVENT_CONTEXT_ALIGNMENT_SCORE_BY_HORIZON',
    payload = '8_event_context_alignment_score_<horizon>',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'event_context_vector;model_08_event_risk_governor;event_risk_governor;target_context_state;model_evaluation;promotion_evidence',
    note = 'current model_08_event_risk_governor / Layer 8 EventRiskGovernor score family for whether event evidence supports or conflicts with current target_context_state by horizon.',
    updated_at = NOW()
WHERE id = 'fld_EOMV1005';

UPDATE trading_registry
SET     key = 'EVENT_CONTEXT_QUALITY_SCORE_BY_HORIZON',
    payload = '8_event_context_quality_score_<horizon>',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'event_context_vector;model_08_event_risk_governor;event_risk_governor;model_evaluation;promotion_evidence',
    note = 'current model_08_event_risk_governor / Layer 8 EventRiskGovernor high-is-good score family for event evidence quality by horizon.',
    updated_at = NOW()
WHERE id = 'fld_EOMV1011';

UPDATE trading_registry
SET     key = 'EVENT_DIRECTION_BIAS_SCORE_BY_HORIZON',
    payload = '8_event_direction_bias_score_<horizon>',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'event_context_vector;model_08_event_risk_governor;event_risk_governor;model_evaluation;promotion_evidence',
    note = 'current model_08_event_risk_governor / Layer 8 EventRiskGovernor score family for signed target-conditioned event direction bias by horizon; this is not alpha confidence.',
    updated_at = NOW()
WHERE id = 'fld_EOMV1004';

UPDATE trading_registry
SET     key = 'EVENT_GAP_RISK_SCORE_BY_HORIZON',
    payload = '8_event_gap_risk_score_<horizon>',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'event_context_vector;model_08_event_risk_governor;event_risk_governor;model_evaluation;promotion_evidence',
    note = 'current model_08_event_risk_governor / Layer 8 EventRiskGovernor high-is-bad score family for event-driven gap or discrete jump risk by horizon.',
    updated_at = NOW()
WHERE id = 'fld_EOMV1007';

UPDATE trading_registry
SET     key = 'EVENT_INDUSTRY_IMPACT_SCORE_BY_HORIZON',
    payload = '8_event_industry_impact_score_<horizon>',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'event_context_vector;model_08_event_risk_governor;event_risk_governor;model_evaluation;promotion_evidence',
    note = 'current model_08_event_risk_governor / Layer 8 EventRiskGovernor score family for industry impact strength by horizon.',
    updated_at = NOW()
WHERE id = 'fld_EOMV1014';

UPDATE trading_registry
SET     key = 'EVENT_INTENSITY_SCORE_BY_HORIZON',
    payload = '8_event_intensity_score_<horizon>',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'event_context_vector;model_08_event_risk_governor;event_risk_governor;model_evaluation;promotion_evidence',
    note = 'current model_08_event_risk_governor / Layer 8 EventRiskGovernor score family for event information-shock or attention intensity by horizon.',
    updated_at = NOW()
WHERE id = 'fld_EOMV1003';

UPDATE trading_registry
SET     key = 'EVENT_LIQUIDITY_DISRUPTION_SCORE_BY_HORIZON',
    payload = '8_event_liquidity_disruption_score_<horizon>',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'event_context_vector;model_08_event_risk_governor;event_risk_governor;model_evaluation;promotion_evidence',
    note = 'current model_08_event_risk_governor / Layer 8 EventRiskGovernor high-is-bad score family for event-driven spread, depth, slippage, or liquidity-disruption risk by horizon.',
    updated_at = NOW()
WHERE id = 'fld_EOMV1009';

UPDATE trading_registry
SET     key = 'EVENT_MARKET_IMPACT_SCORE_BY_HORIZON',
    payload = '8_event_market_impact_score_<horizon>',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'event_context_vector;model_08_event_risk_governor;event_risk_governor;market_context_state;model_evaluation;promotion_evidence',
    note = 'current model_08_event_risk_governor / Layer 8 EventRiskGovernor score family for broad-market impact strength by horizon.',
    updated_at = NOW()
WHERE id = 'fld_EOMV1012';

UPDATE trading_registry
SET     key = 'EVENT_MICROSTRUCTURE_IMPACT_SCORE_BY_HORIZON',
    payload = '8_event_microstructure_impact_score_<horizon>',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'event_context_vector;model_08_event_risk_governor;event_risk_governor;model_evaluation;promotion_evidence',
    note = 'current model_08_event_risk_governor / Layer 8 EventRiskGovernor score family for spread, depth, halt, borrow, option-liquidity, IV, or order-flow microstructure impact by horizon.',
    updated_at = NOW()
WHERE id = 'fld_EOMV1018';

UPDATE trading_registry
SET     key = 'EVENT_PEER_GROUP_IMPACT_SCORE_BY_HORIZON',
    payload = '8_event_peer_group_impact_score_<horizon>',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'event_context_vector;model_08_event_risk_governor;event_risk_governor;model_evaluation;promotion_evidence',
    note = 'current model_08_event_risk_governor / Layer 8 EventRiskGovernor score family for peer-group impact strength by horizon.',
    updated_at = NOW()
WHERE id = 'fld_EOMV1016';

UPDATE trading_registry
SET     key = 'EVENT_PRESENCE_SCORE_BY_HORIZON',
    payload = '8_event_presence_score_<horizon>',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'event_context_vector;model_08_event_risk_governor;event_risk_governor;model_evaluation;promotion_evidence',
    note = 'current model_08_event_risk_governor / Layer 8 EventRiskGovernor score family for relevant event presence by horizon; presence is not good/bad by itself.',
    updated_at = NOW()
WHERE id = 'fld_EOMV1001';

UPDATE trading_registry
SET     key = 'EVENT_REVERSAL_RISK_SCORE_BY_HORIZON',
    payload = '8_event_reversal_risk_score_<horizon>',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'event_context_vector;model_08_event_risk_governor;event_risk_governor;target_context_state;model_evaluation;promotion_evidence',
    note = 'current model_08_event_risk_governor / Layer 8 EventRiskGovernor high-is-bad score family for event-driven reversal risk against current target context by horizon.',
    updated_at = NOW()
WHERE id = 'fld_EOMV1008';

UPDATE trading_registry
SET     key = 'EVENT_SCOPE_CONFIDENCE_SCORE_BY_HORIZON',
    payload = '8_event_scope_confidence_score_<horizon>',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'event_context_vector;model_08_event_risk_governor;event_risk_governor;model_evaluation;promotion_evidence',
    note = 'current model_08_event_risk_governor / Layer 8 EventRiskGovernor score family for confidence in event impact-scope classification by horizon.',
    updated_at = NOW()
WHERE id = 'fld_EOMV1019';

UPDATE trading_registry
SET     key = 'EVENT_SCOPE_ESCALATION_RISK_SCORE_BY_HORIZON',
    payload = '8_event_scope_escalation_risk_score_<horizon>',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'event_context_vector;model_08_event_risk_governor;event_risk_governor;model_evaluation;promotion_evidence',
    note = 'current model_08_event_risk_governor / Layer 8 EventRiskGovernor high-is-bad score family for lower-scope event escalation into higher-scope impact by horizon.',
    updated_at = NOW()
WHERE id = 'fld_EOMV1020';

UPDATE trading_registry
SET     key = 'EVENT_SECTOR_IMPACT_SCORE_BY_HORIZON',
    payload = '8_event_sector_impact_score_<horizon>',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'event_context_vector;model_08_event_risk_governor;event_risk_governor;sector_context_state;model_evaluation;promotion_evidence',
    note = 'current model_08_event_risk_governor / Layer 8 EventRiskGovernor score family for sector impact strength by horizon.',
    updated_at = NOW()
WHERE id = 'fld_EOMV1013';

UPDATE trading_registry
SET     key = 'EVENT_SYMBOL_IMPACT_SCORE_BY_HORIZON',
    payload = '8_event_symbol_impact_score_<horizon>',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'event_context_vector;model_08_event_risk_governor;event_risk_governor;model_evaluation;promotion_evidence',
    note = 'current model_08_event_risk_governor / Layer 8 EventRiskGovernor score family for target/symbol-scope impact strength by horizon; raw ticker identity remains outside fitting vectors.',
    updated_at = NOW()
WHERE id = 'fld_EOMV1017';

UPDATE trading_registry
SET     key = 'EVENT_TARGET_RELEVANCE_SCORE_BY_HORIZON',
    payload = '8_event_target_relevance_score_<horizon>',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'event_context_vector;model_08_event_risk_governor;event_risk_governor;target_context_state;model_evaluation;promotion_evidence',
    note = 'current model_08_event_risk_governor / Layer 8 EventRiskGovernor score family for event relevance to the current anonymous target candidate by horizon.',
    updated_at = NOW()
WHERE id = 'fld_EOMV1021';

UPDATE trading_registry
SET     key = 'EVENT_THEME_FACTOR_IMPACT_SCORE_BY_HORIZON',
    payload = '8_event_theme_factor_impact_score_<horizon>',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'event_context_vector;model_08_event_risk_governor;event_risk_governor;model_evaluation;promotion_evidence',
    note = 'current model_08_event_risk_governor / Layer 8 EventRiskGovernor score family for cross-industry theme/factor impact strength by horizon.',
    updated_at = NOW()
WHERE id = 'fld_EOMV1015';

UPDATE trading_registry
SET     key = 'EVENT_TIMING_PROXIMITY_SCORE_BY_HORIZON',
    payload = '8_event_timing_proximity_score_<horizon>',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'event_context_vector;model_08_event_risk_governor;event_risk_governor;model_evaluation;promotion_evidence',
    note = 'current model_08_event_risk_governor / Layer 8 EventRiskGovernor score family for proximity to a sensitive event window by horizon.',
    updated_at = NOW()
WHERE id = 'fld_EOMV1002';

UPDATE trading_registry
SET     key = 'EVENT_UNCERTAINTY_SCORE_BY_HORIZON',
    payload = '8_event_uncertainty_score_<horizon>',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'event_context_vector;model_08_event_risk_governor;event_risk_governor;model_evaluation;promotion_evidence',
    note = 'current model_08_event_risk_governor / Layer 8 EventRiskGovernor high-is-bad score family for event-driven information uncertainty by horizon.',
    updated_at = NOW()
WHERE id = 'fld_EOMV1006';

UPDATE trading_registry
SET     key = 'OPTION_CONTRACT_FIT_SCORE_BY_HORIZON',
    payload = '9_option_contract_fit_score_<horizon>',
    path = 'trading-model/docs/18_layer_09_trading_guidance.md',
    applies_to = 'expression_vector;option_expression_model;model_09_option_expression;option_expression_plan;model_evaluation;promotion_evidence',
    note = 'Current 8_* score-family token for Layer 9 option-expression: selected contract fit to the Layer 7 path thesis and option-expression constraints by horizon.',
    updated_at = NOW()
WHERE id = 'fld_OEV1003';

UPDATE trading_registry
SET     key = 'OPTION_EXPRESSION_CONFIDENCE_SCORE_BY_HORIZON',
    payload = '9_option_expression_confidence_score_<horizon>',
    path = 'trading-model/docs/18_layer_09_trading_guidance.md',
    applies_to = 'expression_vector;option_expression_model;model_09_option_expression;option_expression_plan;model_evaluation;promotion_evidence',
    note = 'Current 8_* score-family token for Layer 9 option-expression: calibrated confidence in the complete offline option-expression plan by horizon. This is not final approval or execution authorization.',
    updated_at = NOW()
WHERE id = 'fld_OEV1010';

UPDATE trading_registry
SET     key = 'OPTION_EXPRESSION_DIRECTION_SCORE_BY_HORIZON',
    payload = '9_option_expression_direction_score_<horizon>',
    path = 'trading-model/docs/18_layer_09_trading_guidance.md',
    applies_to = 'expression_vector;option_expression_model;model_09_option_expression;option_expression_plan;model_evaluation;promotion_evidence',
    note = 'Current 8_* signed score-family token for Layer 9 option-expression direction by horizon. Positive is call-side/bullish expression, negative is put-side/bearish expression, near zero is no-option expression; this is not order routing.',
    updated_at = NOW()
WHERE id = 'fld_OEV1002';

UPDATE trading_registry
SET     key = 'OPTION_EXPRESSION_ELIGIBILITY_SCORE_BY_HORIZON',
    payload = '9_option_expression_eligibility_score_<horizon>',
    path = 'trading-model/docs/18_layer_09_trading_guidance.md',
    applies_to = 'expression_vector;option_expression_model;model_09_option_expression;option_expression_plan;model_evaluation;promotion_evidence',
    note = 'Current 8_* high-is-good score-family token for Layer 9 option-expression admissibility after Layer 7 thesis, policy, option-chain, liquidity, IV, and risk constraints by horizon. This is not final approval.',
    updated_at = NOW()
WHERE id = 'fld_OEV1001';

UPDATE trading_registry
SET     key = 'OPTION_FILL_QUALITY_SCORE_BY_HORIZON',
    payload = '9_option_fill_quality_score_<horizon>',
    path = 'trading-model/docs/18_layer_09_trading_guidance.md',
    applies_to = 'expression_vector;option_expression_model;model_09_option_expression;option_expression_plan;model_evaluation;promotion_evidence',
    note = 'Layer 9 high-is-good score family for conservative fill-quality estimate by horizon. This is not route or order type.',
    updated_at = NOW()
WHERE id = 'fld_OEV1009';

UPDATE trading_registry
SET     key = 'OPTION_GREEK_FIT_SCORE_BY_HORIZON',
    payload = '9_option_greek_fit_score_<horizon>',
    path = 'trading-model/docs/18_layer_09_trading_guidance.md',
    applies_to = 'expression_vector;option_expression_model;model_09_option_expression;option_expression_plan;model_evaluation;promotion_evidence',
    note = 'Layer 9 high-is-good score family for delta/Greek fit by horizon.',
    updated_at = NOW()
WHERE id = 'fld_OEV1006';

UPDATE trading_registry
SET     key = 'OPTION_IV_FIT_SCORE_BY_HORIZON',
    payload = '9_option_iv_fit_score_<horizon>',
    path = 'trading-model/docs/18_layer_09_trading_guidance.md',
    applies_to = 'expression_vector;option_expression_model;model_09_option_expression;option_expression_plan;model_evaluation;promotion_evidence',
    note = 'Layer 9 high-is-good score family for implied-volatility and IV-rank fit by horizon.',
    updated_at = NOW()
WHERE id = 'fld_OEV1005';

UPDATE trading_registry
SET     key = 'OPTION_LIQUIDITY_FIT_SCORE_BY_HORIZON',
    payload = '9_option_liquidity_fit_score_<horizon>',
    path = 'trading-model/docs/18_layer_09_trading_guidance.md',
    applies_to = 'expression_vector;option_expression_model;model_09_option_expression;option_expression_plan;model_evaluation;promotion_evidence',
    note = 'Layer 9 high-is-good score family for option bid/ask, volume, and open-interest fit by horizon.',
    updated_at = NOW()
WHERE id = 'fld_OEV1004';

UPDATE trading_registry
SET     key = 'OPTION_REWARD_RISK_SCORE_BY_HORIZON',
    payload = '9_option_reward_risk_score_<horizon>',
    path = 'trading-model/docs/18_layer_09_trading_guidance.md',
    applies_to = 'expression_vector;option_expression_model;model_09_option_expression;option_expression_plan;model_evaluation;promotion_evidence',
    note = 'Layer 9 high-is-good score family for premium-adjusted reward/risk quality by horizon.',
    updated_at = NOW()
WHERE id = 'fld_OEV1007';

UPDATE trading_registry
SET     key = 'OPTION_THETA_RISK_SCORE_BY_HORIZON',
    payload = '9_option_theta_risk_score_<horizon>',
    path = 'trading-model/docs/18_layer_09_trading_guidance.md',
    applies_to = 'expression_vector;option_expression_model;model_09_option_expression;option_expression_plan;model_evaluation;promotion_evidence',
    note = 'Layer 9 high-is-bad score family for theta-decay pressure by horizon.',
    updated_at = NOW()
WHERE id = 'fld_OEV1008';

UPDATE trading_registry
SET     key = 'EVENT_ACTIVITY_BRIDGE',
    payload = 'event_activity_bridge',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'event_risk_governor;event_interpretation_v1;event_abnormal_activity_residual_policy;prediction_market;polymarket;source_09_event_risk_governor',
    note = 'Contract connecting event evidence to price, liquidity, option, and prediction-market activity. Useful when raw news is difficult to standardize semantically but activity gives stable point-in-time lead/lag or confirmation/divergence evidence.',
    updated_at = NOW()
WHERE id = 'trm_EAB001';

UPDATE trading_registry
SET     key = 'EVENT_CONTEXT_VECTOR',
    payload = 'event_context_vector',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'trading-model;event_risk_governor;model_08_event_risk_governor;alpha_confidence_model',
    note = 'Layer 8 point-in-time event-context / event-risk-governor evidence output. It contains event timing, scope, type, intensity, directional context, risk context, and quality context without action or execution instructions; it is not a hard upstream alpha prerequisite.',
    updated_at = NOW()
WHERE id = 'trm_ECV001';

UPDATE trading_registry
SET     key = 'EVENT_LIFECYCLE_CONTRACT',
    payload = 'event_lifecycle_contract',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'event_risk_governor;event_interpretation_v1;source_09_event_risk_governor;trading-manager;trading-data;trading-model',
    note = 'Contract requiring event intelligence to preserve lifecycle class and clocks so scheduled-known catalysts are not trained or evaluated as unscheduled surprise events.',
    updated_at = NOW()
WHERE id = 'trm_ELC001';

UPDATE trading_registry
SET     key = 'EVENT_RISK_GOVERNOR',
    payload = 'event_risk_governor',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'trading-model;trading-data;source_09_event_risk_governor;model_08_event_risk_governor;event_context_vector;event_risk_intervention;underlying_action_plan;trading_guidance_record;option_expression_plan;current_physical_names',
    note = 'Accepted Layer 8 event-risk governor. It consumes point-in-time residual event evidence with the Layer 7 direct-underlying action thesis as the canonical risk target; optional Layer 9 trading-guidance/option-expression context may be attached when available. It may warn/block/cap/review or emit promotion packets and remains bounded to risk governance unless reviewed evidence moves a family into Layer 4 EventFailureRiskModel.',
    updated_at = NOW()
WHERE id = 'trm_ERG001';

UPDATE trading_registry
SET     key = 'EVENT_RISK_INTERVENTION',
    payload = 'event_risk_intervention',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'event_risk_governor;layer_08_event_risk_governor;legacy_layer_08_event_risk_governor;trading_guidance_record;execution_risk_control;current_physical_names',
    note = 'Layer 9 output that modifies the decision/risk record consumed by execution risk-control. It is not a broker order, route, time-in-force, or account mutation.',
    updated_at = NOW()
WHERE id = 'trm_ERI001';

UPDATE trading_registry
SET     key = 'EXECUTION_REALTIME_INPUT_COVERAGE_MATRIX',
    payload = 'execution_realtime_input_coverage',
    path = 'trading-execution/src/trading_execution/market_data/contracts.py',
    applies_to = 'trading-execution;realtime_market_data;model_01_market_regime;model_02_sector_context;model_03_target_state_vector;model_08_event_risk_governor;model_05_alpha_confidence;model_06_position_projection;model_07_underlying_action;model_09_option_expression',
    note = 'Side-effect-free Layers 1-8 realtime model-input coverage matrix. It records required realtime observation groups, primary sources, required capture fields, current coverage status, and known provider/account/restriction gaps without opening streams or calling providers.',
    updated_at = NOW()
WHERE id = 'trm_EXEC_RT002';

UPDATE trading_registry
SET     key = 'EXPRESSION_VECTOR',
    payload = 'expression_vector',
    path = 'trading-model/docs/18_layer_09_trading_guidance.md',
    applies_to = 'trading-model;option_expression_model;model_09_option_expression;option_expression_plan;underlying_action_plan;model_evaluation',
    note = 'Layer 8 scalar/vector output for option-expression quality by horizon. It carries eligibility, signed expression direction, contract fit, liquidity fit, IV, Greek fit, reward/risk, theta risk, fill quality, and expression confidence; it is not an order instruction.',
    updated_at = NOW()
WHERE id = 'trm_EXV001';

UPDATE trading_registry
SET     key = 'FOLD_SCOPED_LAYER_09_EVENT_RISK_GOVERNOR_INPUTS',
    payload = 'source_09_event_risk_governor detector/source task keys span fold_start through fold_end and keep detector runs separated by symbol and month',
    path = 'trading-manager/src/trading_manager_tasks/layer_eight_event_risk_governor.py;trading-manager/tests/test_layer_eight_event_risk_governor.py',
    applies_to = 'layer_08_event_risk_governor;source_09_event_risk_governor;fold_materialization',
    note = 'Current source_09 / Layer 8 event-risk-governor materialization accepts six-month folds, prepares detector task keys per symbol-month, and writes one fold-scoped source_09 task key for the event index.',
    updated_at = NOW()
WHERE id = 'term_FOLDMAT002';

UPDATE trading_registry
SET     key = 'HISTORICAL_DATASET_UNIT_POLICY',
    payload = 'layers_01_02_six_month_panel;layers_03_08_target_symbol_six_month;layer_08_event_risk_governor_six_month_overlay',
    path = 'trading-manager/docs/25_automation_scheduler.md;trading-manager/docs/26_historical_scheduler_runtime.md;trading-manager/docs/22_dataset_expansion.md',
    applies_to = 'historical_scheduler;model_training_workflow;dataset_expansion;manager_model_training_workflow_plan;manager_model_training_workflow_state',
    note = 'Accepted dataset-unit policy inside the resident Layer 1-9 historical-modeling system service: Layers 1-2 use one six-month panel; Layers 3-8 use one selected target symbol over one six-month window; Layer 8 EventRiskGovernor uses the six-month overlay unit. Current physical stage tokens use the nine-layer numbering.',
    updated_at = NOW()
WHERE id = 'term_DU001';

UPDATE trading_registry
SET     key = 'HISTORICAL_MODELING_SYSTEM_SERVICE_RUNTIME',
    payload = 'manager_historical_modeling_system_service_runtime',
    path = 'trading-manager/docs/26_historical_scheduler_runtime.md',
    applies_to = 'historical_backfill;model_training_workflow;automation_scheduler;systemd;manager_scheduler_daemon_state;layer_01_market_regime;layer_02_sector_context;layer_03_target_state_vector;layer_04_event_failure_risk;model_05_alpha_confidence;model_06_position_projection;model_07_underlying_action;model_09_option_expression;model_08_event_risk_governor;layer_08_event_risk_governor;current_physical_names',
    note = 'Historical data/modeling workflow is owned by a resident system service covering the full Layer 1-9 stack. Layer 8 EventRiskGovernor is the service-owned residual/risk overlay lane; chat/manual CLI runs are fallback inspection, repair, smoke-test, or emergency-intervention tools, not the normal operating path.',
    updated_at = NOW()
WHERE id = 'trm_HMSR001';

UPDATE trading_registry
SET     key = 'LAYER_09_OPTION_EXPRESSION_FEATURE_NO_PROVIDER_SKIP_RECEIPT',
    payload = 'layer_09_option_expression_feature_generation_no_provider_skip_receipt',
    path = 'trading-manager/docs/20_task_system.md',
    applies_to = 'layer_09_option_expression;feature_08_option_expression;manager_model_training_workflow_state',
    note = 'Component completion receipt proving Layer 9 option-expression feature generation is a reviewed no-op when the Layer 9 gate accepted no active target chain and therefore no source_05/feature_08 rows are required before deterministic no-option model generation.',
    updated_at = NOW()
WHERE id = 'term_L8FEATSKIP001';

UPDATE trading_registry
SET     key = 'LAYER_EIGHT_EVENT_FEED_BACKFILL_DISPATCH',
    payload = 'layer_eight_event_feed_backfill_dispatch',
    path = 'trading-manager/src/trading_manager_tasks/event_feed_dispatch.py;trading-manager/docs/05_decision.md',
    applies_to = 'historical_modeling;source_09_event_risk_governor;event_feed_artifacts;provider_acquisition',
    note = 'Manager-owned bounded dispatch surface for the reviewed event-feed task keys consumed by source_09_event_risk_governor event_artifact_paths.',
    updated_at = NOW()
WHERE id = 'term_L8EVTDIS001';

UPDATE trading_registry
SET     key = 'LAYER_EIGHT_EVENT_FEED_BACKFILL_PREPARATION',
    payload = 'layer_eight_event_feed_backfill_preparation',
    path = 'trading-manager/src/trading_manager_tasks/event_feed_backfill.py;trading-manager/docs/05_decision.md',
    applies_to = 'historical_modeling;source_09_event_risk_governor;event_feed_artifacts',
    note = 'Manager-owned preparation surface for the monthly event-feed artifacts consumed by source_09_event_risk_governor event_artifact_paths.',
    updated_at = NOW()
WHERE id = 'term_L8EVTBF001';

UPDATE trading_registry
SET     key = 'LAYER_EIGHT_EVENT_FEED_IN_WINDOW_ROW_COVERAGE',
    payload = 'layer_eight_event_feed_in_window_row_coverage',
    path = 'trading-manager/src/trading_manager_tasks/layer_eight_event_risk_governor.py;trading-manager/docs/05_decision.md;trading-manager/docs/20_task_system.md',
    applies_to = 'layer_08_event_risk_governor;source_09_event_risk_governor;event_source_coverage;event_feed_coverage;requested_window',
    note = 'Current source_09 / Layer 8 event-risk write-mode materialization requires each required reviewed event-feed artifact family to contain at least one row in the requested [start_month, end_month_next) window. Artifact presence alone is not sufficient.',
    updated_at = NOW()
WHERE id = 'term_L8EVTCOV002';

UPDATE trading_registry
SET     key = 'LAYER_EIGHT_EVENT_SOURCE_COVERAGE_GATE',
    payload = 'layer_eight_event_source_coverage_gate',
    path = 'trading-manager/src/trading_manager_tasks/layer_eight_event_risk_governor.py;trading-data/src/data_source/source_09_event_risk_governor/feed_event_extraction.py;trading-manager/docs/05_decision.md',
    applies_to = 'legacy_layer_08_event_risk_governor;source_09_event_risk_governor;historical_modeling;event_source_coverage;layer_08_event_risk_governor;current_physical_names',
    note = 'Current source_09 / Layer 8 event-source coverage requires reviewed local artifacts with requested-window row coverage for Alpaca news, GDELT news, SEC company financials, and Trading Economics calendar rows before event-governor-dependent outputs may advance.',
    updated_at = NOW()
WHERE id = 'term_L8EVTCOV001';

UPDATE trading_registry
SET     key = 'MANAGER_LAYER_09_OPTION_EXPRESSION_GATE_REVIEW',
    payload = 'manager_layer_09_option_expression_gate_review',
    path = 'trading-manager/docs/20_task_system.md',
    applies_to = 'layer_09_option_expression;option_expression_model;source_05_option_expression;autonomous_historical_provider_acquisition;manager_stage_coverage',
    note = 'Manager-owned review for current layer_09_option_expression acquisition at the Layer 9 option-expression boundary. Active target chains are prepared for autonomous option-snapshot acquisition; no manual provider gate is required.',
    updated_at = NOW()
WHERE id = 'term_L8GATE001';

UPDATE trading_registry
SET     key = 'MANAGER_LAYER_EIGHT_EVENT_RISK_INPUT_MATERIALIZATION',
    payload = 'manager_layer_eight_event_risk_governor_input_materialization',
    path = 'trading-manager/docs/20_task_system.md',
    applies_to = 'layer_08_event_risk_governor;source_09_event_risk_governor;model_training_workflow;local_input_materialization',
    note = 'Manager receipt for building current source_09 / Layer 8 event-risk overview rows from local source-detector outputs over already-reviewed Layer 2 bar artifacts. It performs no provider calls, model activation, broker execution, or storage lifecycle mutation.',
    updated_at = NOW()
WHERE id = 'trm_L8ERGMAT001';

UPDATE trading_registry
SET     key = 'MODEL_07_UNDERLYING_ACTION',
    payload = 'model_07_underlying_action',
    path = 'trading-model/docs/16_layer_07_underlying_action.md',
    applies_to = 'trading-model;underlying_action_model;underlying_action_plan;underlying_action_vector;position_projection_vector;option_expression_model;model_09_option_expression',
    note = 'Accepted current model_07_underlying_action physical model-output surface name for Layer 7 UnderlyingActionModel underlying_action_plan and underlying_action_vector outputs.',
    updated_at = NOW()
WHERE id = 'trm_M7UAM01';

UPDATE trading_registry
SET     key = 'MODEL_09_OPTION_EXPRESSION',
    payload = 'model_09_option_expression',
    path = 'trading-model/docs/18_layer_09_trading_guidance.md',
    applies_to = 'trading-model;option_expression_model;source_05_option_expression;underlying_action_plan;underlying_action_vector;option_expression_plan;expression_vector',
    note = 'Accepted current model_09_option_expression model-output surface name for Layer 9 OptionExpressionModel option_expression_plan and expression_vector outputs. This is not live execution.',
    updated_at = NOW()
WHERE id = 'trm_M7OEM01';

UPDATE trading_registry
SET     key = 'MODEL_08_EVENT_RISK_GOVERNOR',
    payload = 'model_08_event_risk_governor',
    path = 'trading-model/docs/17_layer_08_event_risk_governor.md',
    applies_to = 'trading-model;event_risk_governor;event_context_vector;source_09_event_risk_governor',
    note = 'Accepted current physical model_08_event_risk_governor implementation surface for bounded Layer 8 event-risk evidence and intervention review.',
    updated_at = NOW()
WHERE id = 'trm_M8ERG01';

UPDATE trading_registry
SET     key = 'OPTION_CHAIN_SNAPSHOT_REF',
    payload = 'option_chain_snapshot_ref',
    path = 'trading-model/docs/18_layer_09_trading_guidance.md',
    applies_to = 'option_expression_model;option_expression_plan;model_09_option_expression;option_chain_snapshot;replay_audit',
    note = 'Layer 9 point-in-time option-chain snapshot reference used to replay why a selected contract was chosen. This is not a broker order id.',
    updated_at = NOW()
WHERE id = 'trm_OQSR001';

UPDATE trading_registry
SET     key = 'OPTION_EXPRESSION_MODEL',
    payload = 'option_expression_model',
    path = 'trading-model/docs/18_layer_09_trading_guidance.md',
    applies_to = 'trading-model;source_05_option_expression;model_09_option_expression;underlying_action_plan;underlying_action_vector;option_expression_plan;expression_vector',
    note = 'Accepted Layer 9 option-expression model id. OptionExpressionModel consumes Layer 7 underlying path assumptions plus point-in-time option-chain context and emits offline option_expression_plan / expression_vector rows; current physical surface is model_09_option_expression.',
    updated_at = NOW()
WHERE id = 'trm_OEM001';

UPDATE trading_registry
SET     key = 'OPTION_EXPRESSION_PLAN',
    payload = 'option_expression_plan',
    path = 'trading-model/docs/18_layer_09_trading_guidance.md',
    applies_to = 'trading-model;option_expression_model;model_09_option_expression;underlying_action_plan;expression_vector;trading-execution',
    note = 'Layer 9 primary offline option-expression output. It includes selected expression type, selected option right, point-in-time selected contract reference, contract constraints, premium-risk plan, underlying thesis reference, reason codes, and diagnostics; it is not a broker order or account mutation.',
    updated_at = NOW()
WHERE id = 'trm_OEP001';

UPDATE trading_registry
SET     key = 'PENDING_OPTION_EXPOSURE_CONTEXT',
    payload = 'pending_option_exposure_context',
    path = 'trading-model/docs/18_layer_09_trading_guidance.md',
    applies_to = 'option_expression_model;option_expression_plan;pending_option_orders;premium_risk_context',
    note = 'Layer 9 point-in-time pending option exposure context used to avoid duplicate option-expression plans. It is not a new order instruction.',
    updated_at = NOW()
WHERE id = 'trm_POEC001';

UPDATE trading_registry
SET     key = 'TRADING_GUIDANCE_MODEL',
    payload = 'trading_guidance_model',
    path = 'trading-model/docs/18_layer_09_trading_guidance.md',
    applies_to = 'layer_09_trading_guidance;option_expression_model;underlying_action_plan;option_expression_plan;trading_guidance_record;model_09_option_expression;current_physical_names',
    note = 'Layer 9 model boundary that outputs an optional offline trading-guidance record and optional option-expression context from the Layer 7 direct-underlying thesis. The current V1 option-expression implementation surface is model_09_option_expression; Layer 8 EventRiskGovernor uses Layer 7 underlying_action_plan as the canonical risk target and treats Layer 9 context as downstream.',
    updated_at = NOW()
WHERE id = 'trm_TGM001';

UPDATE trading_registry
SET     key = 'TRADING_GUIDANCE_RECORD',
    payload = 'trading_guidance_record',
    path = 'trading-model/docs/18_layer_09_trading_guidance.md',
    applies_to = 'layer_09_trading_guidance;trading_guidance_model;option_expression_plan;underlying_action_plan;trading-execution;current_physical_names',
    note = 'Layer 9 base offline trading-guidance candidate. It can include direct-underlying, option-expression, maintain, or no-trade guidance, but it is not a broker order and does not mutate accounts.',
    updated_at = NOW()
WHERE id = 'trm_TGR001';

UPDATE trading_registry
SET     key = 'UNDERLYING_ACTION_MODEL',
    payload = 'underlying_action_model',
    path = 'trading-model/docs/16_layer_07_underlying_action.md',
    applies_to = 'trading-model;alpha_confidence_model;alpha_confidence_vector;position_projection_model;position_projection_vector;model_07_underlying_action;underlying_action_plan;underlying_action_vector;option_expression_model;model_09_option_expression',
    note = 'Accepted canonical Layer 7 model id. UnderlyingActionModel maps alpha/position state plus point-in-time current/pending underlying exposure, quote/liquidity/borrow state, risk-budget state, and policy gates into an offline direct underlying planned action thesis for stock, ETF, or crypto spot-style candidates; current physical surface is model_07_underlying_action.',
    updated_at = NOW()
WHERE id = 'trm_UAM001';

UPDATE trading_registry
SET     key = 'UNDERLYING_ACTION_PLAN',
    payload = 'underlying_action_plan',
    path = 'trading-model/docs/16_layer_07_underlying_action.md',
    applies_to = 'trading-model;underlying_action_model;model_07_underlying_action;position_projection_vector;option_expression_model;model_09_option_expression;trading-execution',
    note = 'Layer 7 primary offline direct underlying planned action output for stock, ETF, or crypto spot-style candidates. It includes planned action type, effective exposure gap, planned incremental exposure, entry/target/stop/time-stop thesis, risk plan, Layer 9 trading-guidance handoff, and reason codes; it is not a broker/exchange order, final order quantity, option contract, or execution instruction.',
    updated_at = NOW()
WHERE id = 'trm_UAP001';

UPDATE trading_registry
SET     key = 'UNDERLYING_ACTION_VECTOR',
    payload = 'underlying_action_vector',
    path = 'trading-model/docs/16_layer_07_underlying_action.md',
    applies_to = 'trading-model;underlying_action_model;model_07_underlying_action;position_projection_vector;underlying_action_plan;option_expression_model;model_09_option_expression',
    note = 'Layer 7 score/vector output for direct underlying planned action quality by horizon. It carries eligibility, signed action direction, intensity, entry quality, expected return, adverse risk, reward/risk, liquidity fit, holding-time fit, and action confidence; it is not a broker/exchange order or option-expression vector.',
    updated_at = NOW()
WHERE id = 'trm_UAV001';

UPDATE trading_registry
SET     key = 'UNDERLYING_QUOTE_SNAPSHOT_REF',
    payload = 'underlying_quote_snapshot_ref',
    path = 'trading-model/docs/18_layer_09_trading_guidance.md',
    applies_to = 'option_expression_model;option_expression_plan;underlying_action_plan;replay_audit',
    note = 'Layer 7 point-in-time underlying quote snapshot reference paired with the option-chain snapshot for moneyness and path replay.',
    updated_at = NOW()
WHERE id = 'trm_UQSR001';
