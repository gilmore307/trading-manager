# Model Layer Registry Naming Rules

## Purpose

This file owns registry naming rules for model-layer source, feature, and model surfaces that cross repository boundaries.

It replaces dated watch-list notes with durable rules. Candidate names should be registered only when they become concrete SQL contracts, storage contracts, task receipts, model-facing payloads, or cross-repository handoffs.

## Canonical Surface Pattern

Use compact numeric layer prefixes:

```text
source_NN_<layer_slug>
feature_NN_<layer_slug>
model_NN_<layer_slug>
model_NN_<layer_slug>_explainability
model_NN_<layer_slug>_diagnostics
```

Accepted examples:

- `source_01_market_regime`
- `feature_01_market_regime`
- `model_01_market_regime`
- `model_01_market_regime_explainability`
- `model_01_market_regime_diagnostics`
- `source_02_target_candidate_holdings`
- `feature_02_sector_context`
- `model_02_sector_context`
- `source_03_target_state`
- `feature_03_target_state_vector`
- `model_03_target_state_vector`
- `source_04_event_overlay`
- `model_04_event_overlay`
- `model_05_alpha_confidence`
- `model_06_position_projection`

Rules:

- `source_NN_*` rows are `data_source` when they are control-plane-facing runnable source outputs.
- `feature_NN_*` rows are `data_feature` when they are deterministic model-facing outputs produced by `trading-data`.
- `model_NN_*` names are model-owned contracts; register shared table/surface names as `term`, fields, statuses, or other appropriate kinds only when other repositories consume them.
- Do not maintain semantic aliases such as `layer01_*`, `layer02_*`, or separate prose-only route names for the same physical surface.

## Field Naming

Layer-owned fields use compact numeric prefixes only when the field is specific to that layer contract:

```text
1_*
2_*
3_*
4_*
5_*
6_*
```

Generic identity, lineage, timestamp, receipt, run, and registry metadata fields should stay generic and should not receive a layer prefix.

Do not register generated feature columns merely because a model emits them. Register only durable fields that appear in a reviewed schema, task receipt, storage contract, or cross-repository handoff.

When a reviewed model contract makes a compact numeric-prefixed field the canonical downstream name, any active `field` row for that shared field should use the same compact payload. Do not leave downstream code split between an unprefixed registry field such as `market_direction_score` and a canonical physical/model field such as `1_market_direction_score`. If an unprefixed phrase is still useful as human concept language, keep it in notes or register it as a separate explanatory `term`, not as the canonical model-output `field`.

For accepted model state/context outputs, only reviewed core scalar score tokens belong in `state_vector_value`. Do not duplicate them as generic `field` rows. State/context-vector block/group names, diagnostics, routing/audit fields, windows, enum values, research payloads, and unresolved placeholders remain model-local docs/contracts unless later promoted by manager-phase durable interface review.

## V2.2 Direction-Neutral Flow

Current accepted model-layer intent is direction-neutral tradability first:

```text
market_context_state -> sector_context_state -> anonymous_target_feature_vector -> target_context_state -> event_context_vector -> alpha_confidence_model -> position_projection_model
```

Layer 3 direction evidence is not Layer 5 alpha confidence. Layer 4 `event_overlay_model` owns point-in-time event context/risk before confidence. Layer 5 `alpha_confidence_model` owns final adjusted alpha direction, strength, expected residual return, confidence, signal reliability, path quality, reversal risk, drawdown risk, and alpha-level tradability. Base/unadjusted Layer 1/2/3 alpha remains diagnostic unless separately promoted. Layer 6 `position_projection_model` owns target holding-state projection from final adjusted alpha plus current/pending position, cost, portfolio exposure, and risk-budget context. Event evidence, alpha confidence, and position projection are context/model layers, not final action or execution surfaces.

## Layer 1 Boundary

Layer 1 currently means broad market-context state and direction-neutral market tradability/regime evidence. Accepted core `1_*` MarketRegime scalar scores are `state_vector_value` tokens for `market_context_state`, not duplicate generic `field` rows. Diagnostic payloads such as coverage/data quality stay out of registry state-vector values unless later promoted through a narrower contract review.

## Layer 2 Boundary

Layer 2 currently means market-state-conditioned sector/industry direction-neutral tradability and sector-context modeling. Accepted core `2_*` SectorContext scalar scores are `state_vector_value` tokens for `sector_context_state`; handoff/eligibility/routing enum values stay model-local unless manager-phase interface promotion requires a narrower registry kind.

Current accepted shared surfaces are:

- `source_02_target_candidate_holdings`
- `feature_02_sector_context`
- `model_02_sector_context`
- `sector_context_state`
- `target_candidate_id`
- `anonymous_target_feature_vector`

Human-readable ETF/sector behavior labels such as `growth`, `defensive`, `cyclical`, `inflation_sensitive`, and `safe_haven` are not prerequisite fixed registry classes. They may be post-hoc interpretations after Layer 2 evidence, but should not become hard-coded shared classes unless a reviewed output/status vocabulary requires them.

## Layer 3 Target-State Boundary

Layer 3 is target state-vector construction. Current accepted shared names are:

- `source_03_target_state` — target-local observed-input source contract for anonymous candidates;
- `feature_03_target_state_vector` — deterministic market/sector/target/cross-state feature surface produced by `trading-data`;
- `target_state_vector_model` — canonical Layer 3 model id;
- `model_03_target_state_vector` — model-owned output/table surface;
- `target_context_state` — conceptual model-facing anonymous target context/state output; historical physical implementation names such as `model_03_target_state_vector` remain unchanged until a separate migration is accepted.

`trading-manager` owns target-state request naming and orchestration. `trading-data` owns deterministic point-in-time feature production. `trading-model` owns labels, training, evaluation, promotion evidence, and model-output semantics.

Do not register retired action/variant-selection surfaces as active Layer 3 contracts. Any future action or expression-selection lifecycle must be reviewed as a downstream consumer outside the Layer 3 target-state boundary.

Shared TargetStateVector V1 row keys and top-level feature-block names are registry-owned once both `trading-data` and `trading-model` depend on them. Current shared block names are `market_state_features`, `sector_state_features`, `target_state_features`, and `cross_state_features`; the current sparse synchronized state windows are `5min`, `15min`, `60min`, and `390min`; and the accepted sync-policy value is `market_sector_target_blocks_must_share_identical_observation_windows`. Compact `3_*` names remain reserved for accepted Layer 3 scalar score fields such as `3_target_direction_score_<window>` and `3_tradability_score_<window>`.

Direction-neutral TargetStateVector names must keep signed direction evidence separate from quality/tradability. Use `*_direction_*` names for signed long/short state evidence, `*_trend_quality_*` / `*_path_stability_*` for structural quality, `*_liquidity_tradability_*` for practical tradability, and `*_residual_direction` for beta/context-adjusted relative direction. Do not revive generic `strength`, `readiness`, or `cost` names when the contract distinguishes direction, quality, transition risk, and tradability.

Layer 3 target-state fields may use compact `3_*` payloads only after the target-state contract requires concrete shared fields. Do not register generated feature columns, model-local feature-group internals, label families, embedding names, or cluster labels merely because they appear in TargetStateVectorModel design notes. Layer 3 preprocessing vector block names such as `target_behavior_vector`, `event_risk_context_vector`, and `candidate_quality_vector` remain model-local until implementation/evaluation proves a reviewed cross-repository contract needs them.

## Layer 4 Event-Overlay Boundary

Layer 4 is point-in-time event-context overlay. Current accepted shared names are:

- `source_04_event_overlay` — event overview source/index table owned by `trading-data`;
- `event_overlay_model` — canonical Layer 4 model id;
- `model_04_event_overlay` — future model-owned output/table surface;
- `event_context_vector` — conceptual point-in-time event-context output.

Accepted compact `4_*` state-vector values are scalar event-context score-family tokens, not generic source columns and not alpha/trade/action outputs. Keep these scalar axes separate: event presence, timing proximity, intensity, target-conditioned direction bias, target-context alignment, uncertainty, gap risk, reversal risk, liquidity disruption, contagion risk, evidence quality, impact scope, scope confidence, escalation risk, and target relevance.

Event scope vocabulary must distinguish native event scope from impact scope. Source fields such as `scope_type` describe the event overview row; Layer 4 impact-scope score families describe modeled event impact by horizon. Enum-like audit/routing families such as `4_event_dominant_impact_scope_<horizon>` remain model-local unless a later manager-phase interface review promotes them through a narrower non-scalar kind. Do not register every artifact field, event lifecycle enum, event block name, or news/SEC/NLP detail as a shared registry row until implementation proves a durable cross-repository contract.

## Layer 5 Alpha-Confidence Boundary

Layer 5 is calibrated alpha-confidence modeling. Current accepted shared names are:

- `alpha_confidence_model` — canonical Layer 5 model id;
- `model_05_alpha_confidence` — future model-owned output/table surface;
- `alpha_confidence_vector` — conceptual point-in-time confidence/EV/risk output.

Accepted compact `5_*` state-vector values are final adjusted scalar alpha-confidence score-family tokens, not target-state evidence, event-context evidence, position-projection fields, underlying-action fields, option-expression fields, or final-action outputs. Keep these scalar axes separate: alpha direction, alpha strength, expected residual return, alpha confidence, signal reliability, path quality, reversal risk, drawdown risk, and alpha-level tradability. Base/unadjusted Layer 1/2/3 alpha fields remain diagnostics unless separately promoted.

Do not register action/routing fields, no-trade decisions, position size, target exposure, account-risk allocation, option contract, strike, DTE, delta, or final verdict as Layer 5 state-vector values. Target holding-state projection belongs to Layer 6; planned direct-underlying action belongs to Layer 7; option expression belongs to Layer 8.

## Layer 6 Position-Projection Boundary

Layer 6 is target holding-state projection. Current accepted shared names are:

- `position_projection_model` — canonical Layer 6 model id;
- `model_06_position_projection` — future model-owned output/table surface;
- `position_projection_vector` — conceptual point-in-time target holding-state output.

Accepted compact `6_*` state-vector values are scalar position-projection score-family tokens, not buy/sell/hold actions, option-expression fields, order quantities, or execution outputs. Keep these axes separate: target position bias, target exposure, current-position alignment, position gap, position gap magnitude, expected position utility, cost-to-adjust pressure, risk-budget fit, position-state stability, and projection confidence.

`6_target_exposure_score_<horizon>` is abstract normalized risk exposure, not shares/contracts/order quantity. `6_position_gap_score_<horizon>` is target exposure minus effective current exposure, where effective current exposure includes pending exposure adjusted by fill probability. It is not an execution instruction.

Layer 6 must not output buy/sell/hold/open/close/reverse, choose instruments, read option chains, choose strike/DTE/Greeks, route orders, or mutate broker/account state. Planned direct-underlying action belongs to Layer 7; option expression belongs to Layer 8; execution belongs outside `trading-model`.

## Layer 7 Underlying-Action Boundary

Layer 7 is direct stock/ETF planned action modeling. Current accepted shared names are:

- `underlying_action_model` — canonical Layer 7 model id;
- `model_07_underlying_action` — future model-owned output/table surface;
- `underlying_action_plan` — conceptual point-in-time direct-underlying action plan output;
- `underlying_action_vector` — conceptual point-in-time score/vector output for Layer 7.

Accepted compact `7_*` state-vector values are scalar underlying-action score-family tokens, not broker orders, option-contract fields, or execution outputs. Keep these axes separate: trade eligibility, signed action direction, trade intensity, entry quality, expected return, adverse risk, reward/risk, liquidity fit, holding-time fit, and action confidence.

`planned_quantity` and `planned_notional_usd` are plan payload fields, not final order quantities. `entry_plan` is not order type. `stop_loss_price` and `take_profit_price` are thesis fields, not broker stop/limit orders.

Layer 7 must not emit broker order fields, route orders, mutate broker/account state, or choose option symbol/right/strike/expiration/DTE/delta/Greeks/specific contract refs. Option expression belongs to Layer 8; execution belongs outside `trading-model`.

## Layer 8 Option-Expression Boundary

Layer 8 is option-expression modeling after Layer 7. Current accepted shared names are:

- `option_expression_model` — canonical Layer 8 model id;
- `model_08_option_expression` — future model-owned output/table surface.

Layer 8 may use Layer 7 underlying price-path assumptions plus point-in-time option-chain context to choose option-expression and contract constraints. It still must not place orders or mutate broker/account state.

## Registration Trigger

Before implementation depends on a new shared model-layer name:

1. Decide whether it is a source, feature, model surface, field, classification/status value, table name, or explanatory term.
2. Reuse an accepted registered name when possible.
3. Add SQL migrations under `../sql/schema_migrations/` and regenerate `../current.csv` in the same change.
4. Do not register design-language placeholders or speculative basket states.
