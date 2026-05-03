# Model Layer Name Watch - 2026-05-02

## Trigger

Heartbeat review of recent `trading-model` work for shared names, repo identifiers, path fragments, config defaults, or templates that may belong in `trading-manager/scripts/`.

Recent reviewed commits were concentrated in `trading-model` and introduced the revised Layer 2 / Layer 3 boundary:

- Layer 2 as market-state-conditioned sector/industry trend-stability modeling.
- Layer 3+ as anonymous target-candidate and strategy-fit modeling.
- ETF/sector behavior attributes inferred in Layer 2 rather than pre-assigned.

## Registry-covered surfaces after follow-ups

The current registry snapshot now contains entries for these shared surfaces:

- `model_01_market_regime`
- `trading_model.model_01_market_regime`
- `source_02_target_candidate_holdings`
- `feature_02_sector_context`
- `model_02_sector_context`
- `sector_context_state`
- model governance table names such as `model_dataset_request`, `model_eval_metric`, and `model_config_version`

## Candidate names to review before the next implementation slice

These names appear in accepted or near-accepted model docs. Do not blindly register all of them: first decide which ones are durable shared contracts versus design-language placeholders.

### Likely shared output / feature surfaces

- `sector_selection_parameter_surface` — possible Layer 2 output-surface term, but should be reconciled with `sector_selection_parameter` before registration.

### Likely field or identity-field candidates

- `sector_or_industry_symbol`
- `sector_market_condition_profile`
- `sector_trend_stability_vector`
- `trend_stability_score`
- `cycle_regularity_score`
- `sector_selection_parameter`
- `market_context_state`
- `sector_context_state`
- `target_candidate_id`
- `anonymous_target_feature_vector`
- `strategy_fit_state`
- `composite_strategy_recommendation`

### Status / classification candidates needing caution

- `eligible`, `watch`, `gated`, `excluded` are described as possible basket states. Register them as `status_value` only if they become a formal Layer 2 output/status vocabulary, not merely explanatory prose.
- Human-readable ETF/sector behavior labels such as `growth`, `defensive`, `cyclical`, `inflation_sensitive`, and `safe_haven` should not be registered as fixed prerequisite classes yet. The accepted boundary says these are optional post-hoc interpretations after Layer 2 evidence, not hard-coded assumptions.

## Recommendation

Before the next `SectorContextModel` implementation or task-template update:

1. Treat `model_02_sector_context` / `feature_02_sector_context` as the accepted registered surface names.
2. Reconcile `sector_selection_parameter` and `sector_selection_parameter_surface` into one durable contract term before either becomes a shared schema field.
3. Register only fields that appear in a concrete output schema, task receipt, storage contract, or cross-repository handoff.
4. Add SQL migrations under `scripts/sql/schema_migrations/` and regenerate `scripts/current.csv` in the same change.

No Codex-specific temporary names were found in `trading-manager` itself during this heartbeat; the watch items came from recent `trading-model` architecture commits.

## Follow-up: registry alignment commit `f08570e`

Registry alignment migrations `178_align_model_registry_to_current_route.sql` and `179_rename_model_two_to_sector_context.sql` addressed this watch list.

Registered or reconciled rows now include:

- `MODEL_02_SECTOR_CONTEXT` as the accepted Layer 2 output term, with physical artifact/table contract `trading_model.model_02_sector_context`.
- `MARKET_CONTEXT_STATE`
- `SECTOR_CONTEXT_STATE`
- `TARGET_CANDIDATE_ID`
- `ANONYMOUS_TARGET_FEATURE_VECTOR`
- Layer 1 market-property factor fields replacing the older proxy-dashboard factor set:
  - `price_behavior_factor`
  - `trend_certainty_factor`
  - `capital_flow_factor`
  - `sentiment_factor`
  - `valuation_pressure_factor`
  - `fundamental_strength_factor`
  - `macro_environment_factor`
  - `market_structure_factor`
  - `risk_stress_factor`

The migration also removed the older `TREND_FACTOR`, `VOLATILITY_STRESS_FACTOR`, `CORRELATION_STRESS_FACTOR`, `CREDIT_STRESS_FACTOR`, `RATE_PRESSURE_FACTOR`, `DOLLAR_PRESSURE_FACTOR`, `COMMODITY_PRESSURE_FACTOR`, `SECTOR_ROTATION_FACTOR`, `BREADTH_FACTOR`, and `RISK_APPETITE_FACTOR` rows.

Remaining watch items before implementation:

- `feature_02_sector_context` is now registered as `FEATURE_02_SECTOR_CONTEXT`; keep future field-level registration deferred until a concrete output/schema proves which fields are shared.
- Reconcile `sector_selection_parameter` / `sector_selection_parameter_surface`; neither should be registered until the output schema is concrete.
- Hold `sector_market_condition_profile`, `sector_trend_stability_vector`, `trend_stability_score`, `cycle_regularity_score`, `strategy_fit_state`, and `composite_strategy_recommendation` until they appear in an accepted schema or task handoff.
- Because the newly inserted market-property factor fields use `artifact_sync_policy = sync_artifact`, downstream code/docs should be checked during the next Model 1 implementation review to ensure generated outputs actually use these canonical field names.

## Follow-up: trading-model doc streamline `3036451`

The `trading-model` documentation streamline made the current route more direct rather than introducing a broad new naming set. Two phrases should stay on watch:

- `anonymous_target_candidate_builder` — now appears repeatedly as the bridge into `StrategySelectionModel` and is already used as an `applies_to` token for `TARGET_CANDIDATE_ID` and `ANONYMOUS_TARGET_FEATURE_VECTOR`, but it is not yet registered as its own shared term or component id. Register only if it becomes a concrete artifact producer, package/module boundary, task template, or cross-repository handoff.
- `direct_stock_etf_comparison` / direct stock-ETF comparison — currently prose for `OptionExpressionModel` V1 alongside long call / long put. Do not register until it becomes a formal expression type, status value, output field, or evaluation class.

No Codex temporary names were found in `trading-manager` during this follow-up.

## Follow-up: trading-model output key prefix commit `86e4afa`

The later `trading-model` commit `86e4afa` accepted a stronger output-key ownership rule: model-facing keys use compact layer prefixes such as `1_price_behavior_factor` and `2_sector_observed_behavior_vector`, while persisted SQL columns should use safe aliases such as `layer01_price_behavior_factor` and `layer02_sector_observed_behavior_vector`.

New/shared surfaces to keep under registry review:

- Layer 1 model-facing keys: `1_price_behavior_factor`, `1_trend_certainty_factor`, `1_capital_flow_factor`, `1_sentiment_factor`, `1_valuation_pressure_factor`, `1_fundamental_strength_factor`, `1_macro_environment_factor`, `1_market_structure_factor`, `1_risk_stress_factor`, `1_transition_pressure`, and `1_data_quality_score`.
- Layer 1 physical SQL aliases, if persisted: `layer01_price_behavior_factor`, `layer01_trend_certainty_factor`, `layer01_capital_flow_factor`, `layer01_sentiment_factor`, `layer01_valuation_pressure_factor`, `layer01_fundamental_strength_factor`, `layer01_macro_environment_factor`, `layer01_market_structure_factor`, `layer01_risk_stress_factor`, `layer01_transition_pressure`, and `layer01_data_quality_score`.
- Layer 2 model-facing keys now documented with `2_` ownership: `2_sector_observed_behavior_vector`, `2_sector_attribute_vector`, `2_sector_conditional_behavior_vector`, `2_sector_trend_stability_vector`, `2_sector_tradability_vector`, `2_sector_risk_context_vector`, `2_sector_quality_diagnostics`, `2_eligibility_state`, `2_sector_handoff_state`, and optional `2_sector_selection_parameter`.
- Layer 2 physical SQL aliases should use corresponding `layer02_*` names only once a concrete persisted schema exists.

Do not immediately register both model-facing and physical names as duplicate field rows. Before the next implementation slice, decide the registry ownership pattern explicitly:

1. Whether `field` rows should name physical SQL aliases (`layer01_*`, `layer02_*`) while payload/notes mention model-facing JSON keys (`1_*`, `2_*`).
2. Whether compact numeric-prefix keys are allowed as registry `key` values, or should remain payload/schema contract strings under safe registry keys.
3. Whether the earlier newly inserted unprefixed factor rows should be migrated, aliased, or marked deprecated so downstream code does not split between unprefixed and prefixed contracts.

## Follow-up: current candidate-boundary commits `62c1caa` / `817880a` / `14bfdf0`

Heartbeat review of the latest `trading-model`, `trading-data`, and `trading-storage` commits found no Codex-only temporary names in `trading-manager` itself. The recent work mostly reinforced previously watched boundary terms.

Already registry-covered or intentionally pending:

- `model_02_sector_context`, `market_context_state`, `sector_context_state`, `target_candidate_id`, and `anonymous_target_feature_vector` are present as registry terms after migrations `178`/`179`.
- `feature_02_sector_context` is a concrete registered `data_feature` row in `scripts/current.csv` after migration `179_rename_model_two_to_sector_context.sql`.
- `stock_etf_exposure` remains a registered data kind with deprecated/legacy bundle history. Current docs correctly treat it as downstream anonymous target candidate-builder evidence, not Layer 2 core behavior input.
- `anonymous_target_candidate_builder` has become a real `trading-model/src/models/` package boundary and target-candidate contract owner. It is still only used as an `applies_to` token in registry rows. If it becomes a task template, artifact producer, or cross-repo callable component, register it as a shared component/term in `trading-manager` rather than leaving it only implicit.

New caution from the storage/data alignment:

- `bkch_bitw` was reclassified from Layer 1 primary evidence to Layer 2 `sector_rotation` evidence. The pair is data content in `market_regime_relative_strength_combinations.csv`, not a shared registry name by itself. Do not register ticker-pair content unless pair ids become stable reusable contract keys outside the shared CSV.
- `sector_or_industry_symbol` is now part of the `sector_context_state` contract. Hold it for implementation review before field registration because the contract explicitly says Layer 2 field names are model-local until implementation/evaluation proves which names should be shared.

Recommended next registry cleanup:

1. Decide whether `ANONYMOUS_TARGET_CANDIDATE_BUILDER` should be a first-class component/term row now that it owns a concrete `src/models/` package and contract file.
2. Do not register `bkch_bitw` or other relative-strength pair ids unless a separate pair-id registry policy is accepted.
3. Keep Layer 2 field-level registration deferred until the `SectorContextModel` implementation proves which output fields are truly shared.

## Follow-up: sector context registry alignment `dacf22d` / `59634e5`

Later alignment commits resolved the main pending watch items from the previous heartbeat.

Resolved / registered:

- `FEATURE_02_SECTOR_CONTEXT` / `feature_02_sector_context` is now a first-class `data_feature` row (`dki_SCFS001`) for the Layer 2 deterministic SectorContextModel feature surface.
- `MODEL_02_SECTOR_CONTEXT` / `model_02_sector_context` replaced the earlier `MODEL_02_SECURITY_SELECTION` term as the accepted Layer 2 model-output route.
- `SECTOR_CONTEXT_MODEL` / `sector_context_model` is now registered as the canonical Layer 2 model id.
- `ANONYMOUS_TARGET_CANDIDATE_BUILDER` / `anonymous_target_candidate_builder` is now registered as a concrete boundary term between SectorContextModel and StrategySelectionModel.

Current caution:

- Old names may still exist as compatibility wrappers or migration history (`feature_02_security_selection`, `model_02_security_selection`, `source_02_security_selection`). Treat new uses of those names as suspect unless they are explicitly compatibility/deprecation surfaces.
- The current registry rows make `feature_02_sector_context` and `model_02_sector_context` the preferred Layer 2 route. Future implementation reviews should reject newly introduced `SecuritySelectionModel` Layer 2 identifiers unless the docs explicitly mean the downstream target/security-selection stage, not sector context modeling.

## Follow-up: layer artifact naming docs `10662e2` / `2ebbe4a` / `62b5267` / `6e04523`

The latest cross-repo documentation commits accepted a stricter layer-artifact naming rule: compact numeric-prefixed model fields are canonical in docs, model-facing payloads, and SQL physical columns, and SQL DDL should quote names such as `1_price_behavior_factor` or `2_trend_stability_score` instead of inventing semantic aliases such as `layer01_*` / `layer02_*`.

New or newly concrete shared artifact names now appear across manager/model/data/storage docs:

- `trading_model.model_01_market_regime_explainability`
- `trading_model.model_01_market_regime_diagnostics`
- `trading_model.model_02_sector_context_explainability`
- `trading_model.model_02_sector_context_diagnostics`

Registry gap to resolve before implementation hard-depends on these names:

1. Add registry rows for the explainability and diagnostics model artifacts, or explicitly document why primary model-output terms cover their companion tables.
2. Reconcile existing unprefixed Layer 1 field rows (`price_behavior_factor`, `transition_pressure`, `data_quality_score`, etc.) with the now-accepted compact canonical model-field names (`1_*`). The registry should not let downstream code split between unprefixed registry fields and prefixed SQL/model contract fields.
3. Decide whether Layer 2 compact output fields such as `2_trend_stability_score`, `2_sector_handoff_state`, `2_eligibility_state`, and `2_state_quality_score` should be registered now that they are listed as the stable downstream `model_02_sector_context` contract.
4. Register allowed handoff/status values only if they become formal status vocabularies outside the Layer 2 contract prose. Current accepted values are `selected`, `watch`, `blocked`, and `insufficient_data` for `2_sector_handoff_state`.

Compatibility/deprecation caution remains: new implementation should not introduce `layer01_*` / `layer02_*` physical aliases or revive `model_02_security_selection` / `feature_02_security_selection` except as explicit compatibility wrappers.
