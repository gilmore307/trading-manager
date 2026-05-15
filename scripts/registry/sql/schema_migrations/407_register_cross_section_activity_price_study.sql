-- Register cross-sectional activity-price relationship study requirements.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_APXS001',
    'config',
    'ACTIVITY_PRICE_CROSS_SECTION_STUDY_REQUIRED',
    'text',
    'required_before_event_activity_bridge_model_promotion',
    'trading-model/docs/99_activity_price_relationship_study.md',
    'activity_price_relationship_proof_gate;event_activity_bridge;event_risk_governor;model_promotion',
    'sync_artifact',
    'The activity-price proof gate must be cross-sectional across size buckets, sector/theme buckets, and event families; one story stock is insufficient for model-layer promotion.'
  ),
  (
    'cfg_APXS002',
    'config',
    'ACTIVITY_PRICE_STUDY_SIZE_BUCKETS',
    'text',
    'mega_large_cap;large_cap;mid_cap;small_cap;micro_or_speculative_cap',
    'trading-model/docs/99_activity_price_relationship_study.md',
    'activity_price_relationship_study;cohort_design;cross_section',
    'sync_artifact',
    'Initial size buckets for the activity-price relationship proof study.'
  ),
  (
    'cfg_APXS003',
    'config',
    'ACTIVITY_PRICE_STUDY_SECTOR_THEME_BUCKETS',
    'text',
    'technology_platform;semiconductor_ai;financials_bank_or_broker;energy_commodity;healthcare_biotech;industrial_defense_aerospace;communications_satellite;consumer_retail;crypto_sensitive',
    'trading-model/docs/99_activity_price_relationship_study.md',
    'activity_price_relationship_study;cohort_design;cross_section',
    'sync_artifact',
    'Initial sector/theme buckets for cross-sectional abnormal-activity proof.'
  ),
  (
    'cfg_APXS004',
    'config',
    'ACTIVITY_PRICE_STUDY_EVENT_FAMILIES',
    'text',
    'earnings_or_guidance;analyst_rating_or_price_target;contract_award_or_customer_order;regulatory_or_legal;financing_or_offering;product_or_partnership;macro_policy_or_geopolitical;short_report_or_investigative_claim;clinical_or_fda;prediction_market_resolution_related',
    'trading-model/docs/99_activity_price_relationship_study.md',
    'activity_price_relationship_study;event_family_training;event_activity_bridge',
    'sync_artifact',
    'Initial event-family buckets for activity-price relationship tests. Families should be evaluated separately before aggregate conclusions.'
  ),
  (
    'cfg_APXS005',
    'config',
    'ACTIVITY_PRICE_STUDY_REQUIRED_COMPARISONS',
    'text',
    'all_eligible_windows;abnormal_activity_windows;non_abnormal_windows;event_only_windows;event_plus_abnormal_windows;abnormal_without_visible_event_windows;pre_event_abnormal_later_explained_windows;event_activity_divergence_windows',
    'trading-model/docs/99_activity_price_relationship_study.md',
    'activity_price_relationship_study;model_evaluation;event_activity_bridge',
    'sync_artifact',
    'Required comparison groups for the cross-sectional activity-price relationship proof study.'
  ),
  (
    'cfg_APXS006',
    'config',
    'ACTIVITY_PRICE_STUDY_ACCEPTANCE_CRITERIA',
    'text',
    'forward_price_path_relationship;incremental_residual_value;cross_sectional_non_story_stock_support;out_of_sample_stability;leakage_controls_passed;reviewed_failure_modes',
    'trading-model/docs/99_activity_price_relationship_study.md',
    'activity_price_relationship_study;model_promotion;event_activity_bridge',
    'sync_artifact',
    'Acceptance criteria for opening an EventActivityBridgeModel promotion task after the activity-price proof study.'
  ),
  (
    'cfg_APXS007',
    'config',
    'ACTIVITY_PRICE_STUDY_PILOT_BASKET',
    'text',
    'AAPL;MSFT;NVDA;AMD;JPM;COIN;XOM;CVX;LLY;PFE;RKLB;ACHR;ASTS;RCAT;CAVA;ELF;VKTX;SAVA',
    'trading-model/docs/99_activity_price_relationship_study.md',
    'activity_price_relationship_study;pilot_basket;cohort_design',
    'sync_artifact',
    'Initial pilot basket for cross-sectional proof. It is replaceable when liquidity, coverage, or corporate-action quality is insufficient.'
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
