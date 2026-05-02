# Model Layer Name Watch - 2026-05-02

## Trigger

Heartbeat review of recent `trading-model` work for shared names, repo identifiers, path fragments, config defaults, or templates that may belong in `trading-manager/scripts/`.

Recent reviewed commits were concentrated in `trading-model` and introduced the revised Layer 2 / Layer 3 boundary:

- Layer 2 as market-state-conditioned sector/industry trend-stability modeling.
- Layer 3+ as anonymous target-candidate and strategy-fit modeling.
- ETF/sector behavior attributes inferred in Layer 2 rather than pre-assigned.

## Already covered in the registry snapshot

The current registry snapshot already contains entries for the older shared surfaces below:

- `model_01_market_regime`
- `trading_model.model_01_market_regime`
- `source_02_security_selection`
- Layer 1 market-property output fields such as `trend_factor`, `breadth_factor`, `sector_rotation_factor`, and `data_quality_score`
- model governance table names such as `model_dataset_request`, `model_eval_metric`, and `model_config_version`

## Candidate names to review before the next implementation slice

These names are now present in accepted or near-accepted model docs, but are not yet registered in `scripts/current.csv` as of this review. Do not blindly register all of them: first decide which ones are durable shared contracts versus design-language placeholders.

### Likely shared output / feature surfaces

- `feature_02_security_selection` — likely data-feature key if Layer 2 deterministic feature routing becomes manager-facing.
- `model_02_security_selection` — likely model-output/table term if the Layer 2 model output is materialized with the same pattern as `model_01_market_regime`.
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

Before the next `SecuritySelectionModel` implementation or task-template update:

1. Pick the canonical Layer 2 output key/table name (`model_02_security_selection` versus another accepted form).
2. Reconcile `sector_selection_parameter` and `sector_selection_parameter_surface` into one durable contract term.
3. Register only fields that appear in a concrete output schema, task receipt, storage contract, or cross-repository handoff.
4. Add SQL migrations under `scripts/sql/schema_migrations/` and regenerate `scripts/current.csv` in the same change.

No Codex-specific temporary names were found in `trading-manager` itself during this heartbeat; the watch items came from recent `trading-model` architecture commits.

## Follow-up: registry alignment commit `f08570e`

A later registry alignment migration, `178_align_model_registry_to_current_route.sql`, addressed part of this watch list.

Registered or reconciled rows now include:

- `MODEL_02_SECURITY_SELECTION` as a planned Layer 2 output term, with physical artifact/table contract still pending implementation.
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

- Decide whether `feature_02_security_selection` should become a `data_feature` registry row once a concrete deterministic feature surface exists.
- Reconcile `sector_selection_parameter` / `sector_selection_parameter_surface`; neither should be registered until the output schema is concrete.
- Hold `sector_market_condition_profile`, `sector_trend_stability_vector`, `trend_stability_score`, `cycle_regularity_score`, `strategy_fit_state`, and `composite_strategy_recommendation` until they appear in an accepted schema or task handoff.
- Because the newly inserted market-property factor fields use `artifact_sync_policy = sync_artifact`, downstream code/docs should be checked during the next Model 1 implementation review to ensure generated outputs actually use these canonical field names.
