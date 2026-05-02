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
