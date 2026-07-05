# Event Impact Distribution

This file owns the current event-impact contract. It is a contract
surface, not a training-method note.

## Core Model

Event impact is a point-in-time probability distribution over signed impact
intensity:

```text
Y_t ~ P(signed_impact_intensity | standardized_event, context, t)
```

`t` is measured from the event's `available_time`, not from a later discovery or
review time. `Y_t` may be positive or negative. Probability mass and probability
density are never negative.

The signed impact distribution is decomposed into:

```text
Y_t = impact_scale_t * direction_state_t * magnitude_state_t
```

- `magnitude_state_t` is a non-negative probability distribution whose mass
  integrates to 1.
- `direction_state_t` owns bullish, bearish, and neutral probabilities.
- `impact_scale_t` owns the unit scale, such as return bps, volatility units,
  utility delta, or option-expression suitability delta.
- `time_scale_t` owns the x-axis unit, such as minutes, hours, trading days, or
  event-family phase clocks.

M04 consumes distribution summaries such as mean, quantiles, sign probabilities,
uncertainty mass, and adverse/favorable tail probabilities. It uses M03 as an
event distribution operator inside the final direct-underlying posterior
probability function. M05 consumes the resulting M04 thesis surface for
expression translation. Neither layer consumes raw event text.

## End-To-End Event Route

M03 does not start from selected trades or replay failures. It starts from the
full point-in-time event universe inside the fold/window:

1. Materialize every PIT-visible candidate event for the fold/window.
2. Standardize event semantics and assign the finest PIT-identifiable reviewed
   taxonomy node on the fixed
   `Domain -> Kingdom -> Phylum -> Class -> Order -> Family -> Genus -> Species`
   spine. This is the `semantic_node`.
3. Select the deepest evidence-supported `effect_model_node`. It may be the
   semantic node or a conservative ancestor when the semantic leaf is too
   sparse.
4. For the effect-model node, test whether PIT event parameters can support an
   identifiable probability function for later market, sector, target, option,
   or execution impact.
5. If identifiable, train distribution-parameter mappings only inside the
   channels owned by the reviewed `event_effect_model`.
6. If not identifiable, keep the event as risk shape/context only. It may widen
   variance, thicken tails, discount confidence, or raise gates, but it must not
   move mean/mode or directional contribution.

This route lets M03 combine the existing semantic event model with probability
functions without turning every event into a direction bet.

## Event Effect Models

Each effect-model node owns an `event_effect_model`. This is an impact-mode
contract, not a permission mask. The taxonomy node defines the homogeneous event
pool; the effect model defines which distribution channels the node can train
and emit after review.

Default risk-shape model:

| Channel | Default | Meaning |
|---|---:|---|
| `variance_multiplier` | allowed | The event can widen or compress the path distribution. |
| `left_tail_delta` | allowed | The event can thicken adverse tail risk. |
| `right_tail_delta` | allowed | The event can thicken favorable tail opportunity. |
| `skew_delta` | allowed | The event can skew the distribution without moving its center. |
| `confidence_discount` | allowed | The event can lower certainty in other signals. |
| `gate_pressure` | allowed | The event can raise entry/no-trade or exposure gates. |
| `mean_shift` | absent | The event cannot move expected return by default. |
| `mode_shift` | absent | The event cannot move the most likely outcome by default. |
| `directional_contribution` | absent | The event cannot add alpha/edge by default. |

Directional effect models are opt-in and review-gated. A node may own
`mean_shift`, `mode_shift`, or `directional_contribution` only after
fold-separated evidence shows a stable signed residual effect after M01/M02
controls. Without that review, even severe events remain variance/tail/gate
inputs rather than center-moving signals.

M03 training must therefore be channelized multi-head training:

```text
semantic_node      -> finest PIT-identifiable event classification
effect_model_node  -> evidence-supported node for modelability/fallback
event_effect_model -> distribution channels and probability-function class
event instance     -> learned magnitude per owned channel
M03 output         -> distribution-effect scores + validation evidence
M04                -> final fusion, threshold, calibration, and sizing
```

An unrestricted `event_delta_probability` is not a valid M03 output because it
hides whether the event changed risk shape, confidence, gates, or the center of
the distribution.

## M04 Absorption Contract

M04's primary model output is the final posterior probability function:

```text
D4(y, tau) = calibrate(A03(A01(D2(y, tau))))
```

- `D2`: M02 target base distribution.
- `A01`: M01 market/sector background distribution operator.
- `A03`: M03 event distribution operator.
- `D4`: M04 `thesis_distribution_surface`.

M04 consumes M03 through two explicit routes:

1. `center_shift` route. If the effect-model node has an identifiable
   probability function and approved center channels, M04 may absorb
   `mean_shift`, `mode_shift`, and `directional_contribution` into the
   distribution center: edge direction, expected return, thesis mean/mode, and
   action confidence after calibration.
2. `risk_shape` route. If the semantic node is too sparse or unstable for a
   center-moving probability function, M03 keeps the fine semantic
   classification but falls back to the deepest evidence-supported
   effect-model node. M04 may absorb only variance, tail, skew, confidence, and
   gate channels. These channels widen or skew the distribution, lower
   confidence, raise thresholds, reduce exposure permission, or block entries;
   they must not move the most likely direction by themselves.

Events that cannot support either route remain `context_only_projection` or
`do_not_model` and may only produce display/audit context or no downstream
model use.

## Projection Modes

M03 assigns exactly one projection mode for an event family after deterministic
coverage and leakage gates are ready:

| Mode | Meaning |
|---|---|
| `impact_function_projection` | Tier 1. The core event model. The event family has a stable enough lifecycle to be described by a time-indexed impact distribution/state function. |
| `conditional_effect_projection` | Tier 2. The internal state function is not identifiable, but PIT event parameters have a stable validated input-output association with later outcomes. |
| `context_only_projection` | Tier 3. Direct quantitative impact analysis is not reliable, but the event is known to make market, sector, target, option, or execution risk larger. |
| `do_not_model` | The event family should not enter M03 event-state projection. |

`context_only_projection` is not a prediction. It may produce downstream
uncertainty or caution context, but it must not output direction, magnitude,
half-life, utility delta, or option structure advice.

The ordering is intentional. `impact_function_projection` is the preferred
model when the event family has stable shape, clocks, and distribution class.
`conditional_effect_projection` is a fallback for families where the middle
state process cannot be separated but the standardized input-to-outcome mapping
is validated. `context_only_projection` is a risk-control output only: it says
the event matters, not how much or in which direction.

## Event Taxonomy Boundary

M03 classifies events through a fixed event taxonomy, not a flat single-level
family list. The purpose of the hierarchy is to classify each event to the
finest point-in-time semantic node while allowing modelability to fall back to
the deepest evidence-supported ancestor.

The taxonomy spine is:

```text
Domain -> Kingdom -> Phylum -> Class -> Order -> Family -> Genus -> Species
```

Rank roles:

| Rank | Role |
|---|---|
| `domain` | Whether the row belongs in the market-event universe at all. |
| `kingdom` | Broad market system such as macro, corporate, regulatory, political/geopolitical, financial-system, market-structure, commodity/energy, or technology/industry. |
| `phylum` | Information or institutional form such as official release, central-bank action, company disclosure, SEC filing, regulatory action, court/legal process, news report, market-microstructure event, analyst action, or capital-market transaction. |
| `class` | Affected scope such as broad market, sector/industry, theme/factor, single target, supply-chain network, option surface, liquidity/execution, or credit/funding. |
| `order` | Mechanism class such as inflation/growth release, monetary-policy repricing, earnings-information event, guidance reset, regulatory constraint, legal liability, capital-structure change, product-market competition, supply/demand shock, liquidity/flow shock, volatility-surface event, or credit-stress event. |
| `family` | Reusable event family with common PIT fields, clocks, scope, and channels. |
| `genus` | Finer PIT-identifiable mechanism subtype inside a family. |
| `species` | Specific reusable pattern or dossier with PIT-identifiable repeated mechanics and stronger explanatory value than the parent. |

Coarse nodes are useful when the system has not studied an event deeply enough.
For example, the first AAOI earnings event may inherit from
`company_earnings_or_financial_results`. If later evidence shows AAOI earnings
have a stable small-cap supplier/customer-concentration profile while NVDA
earnings have a stable mega-cap technology/AI-sector read-through profile, M03
should split or attach specific dossiers instead of forcing both into one
undifferentiated earnings pattern.

The taxonomy is not a strict exclusive tree. An event may carry multiple
mechanism tags and risk channels. The primary semantic node owns the packet and
lineage, while additional tags describe scope, theme, channel, and uncertainty.
Low-level source/category labels may be ancestors, but they are not sufficient
for modelability review.

Event-family IDs used for modelability packets should name the currently
accepted mechanism family or submechanism family. Tickers, company names,
sectors, venues, and dates are observation labels, affected entities, scope
fields, acquisition filters, or dossier refs until a specific dossier has passed
review. Direction is an event parameter, not a separate family boundary.

Valid mechanism-family examples:

- `target_product_price_change_news`: target product price increase/decrease
  news, with target identity stored on each observation and direction stored as
  a signed event parameter.
- `cpi_release`: CPI release events.
- `ppi_release`: PPI release events.
- `company_earnings_or_financial_results`: company financial results and
  earnings/report filings.

Valid child/dossier examples:

- `company_earnings_or_financial_results` ancestor plus a reviewed
  `nvda_earnings_sector_readthrough` dossier.
- `company_earnings_or_financial_results` ancestor plus a reviewed
  `small_cap_supplier_customer_concentration_earnings` submechanism.
- `cpi_release` ancestor plus a reviewed inflation-regime-specific dossier when
  PIT rules, sample coverage, and controls support it.

Invalid modelability-family examples:

- `news`: source class only.
- `report`: source/category bucket only.
- `target_news_or_disclosure`: source/category bucket only.
- `scheduled_macro_release`: release calendar category only.
- `macro`: domain bucket only.
- `nvda_earnings_went_up`: hindsight outcome label.
- `aaoi_earnings_crashed`: target-specific outcome label.

M03 event-family evidence packets must reject raw source/category buckets and
hindsight outcome labels before Codex review. Source rows may still feed a
concrete family packet, for example Alpaca/GDELT news rows feeding
`target_product_price_change_news`, or scheduled macro calendar rows feeding
`cpi_release`.

## Taxonomy Promotion And Lineage

Taxonomy depth is evidence-gated. M03 starts with the narrowest accepted node
whose rules are point-in-time definable. It may promote a child family or
specific dossier only when the split is reusable, operationally useful, and
defined without post-event returns.

A child family or dossier proposal must include:

- parent and fallback ancestor refs;
- definition, inclusion criteria, exclusion criteria, and near-misses;
- source/category and canonical source precedence;
- lifecycle class and clock rules;
- required interpretation fields and structured parameters;
- affected scope defaults and risk-channel defaults;
- minimum same-family coverage and cross-fold stability expectations;
- matched-control, leakage, overlap/confounder, label, and calibration gates;
- evidence that the finer node improves risk/tradability context or replay
  attribution beyond the ancestor;
- a rule for falling back to the ancestor when evidence is weak.

Historical ledgers must not silently move events between families. Each event
row must preserve the taxonomy version, original accepted classification,
current reviewed classification, ancestor chain, active modelability node, and
fallback node. Replay review consumes the fixed M03 ledger that existed for the
fold; later taxonomy promotion can only affect future folds or explicitly
rerun-managed artifacts.

Fine classification must not be outcome-driven. A split such as
`nvda_earnings_sector_readthrough` is only admissible if it can be identified
from PIT-visible facts such as market-cap/weight, sector/theme centrality,
option liquidity/IV profile, analyst/market attention, supply-chain role,
guidance/capex fields, and historical fold-separated behavior. It is not
admissible merely because a past NVDA earnings event moved the market.

Evidence-packet readiness is a deterministic program decision, not a Codex
semantic decision:

| Readiness | Meaning |
|---|---|
| `admissible_for_modelability_review` | Mechanical gates passed; Codex may judge projection mode and probability-function class. |
| `admissible_for_context_only_review` | The packet is deterministic risk context, not a quantitative impact-family candidate. |
| `blocked_missing_same_family_evidence` | Same-family count is below the required threshold. |
| `blocked_mixed_family` | The sample contains multiple incompatible mechanisms or unresolved child/dossier candidates in one packet. Signed parameters such as product-price increase versus decrease stay inside one price-change family. |
| `blocked_missing_structured_evidence` | Required structured inputs, clocks, expectations, surprise fields, or clean subtype fields are missing. |
| `blocked_missing_modelability_gates` | The family is mechanically coherent, but controls, overlap/confounder, leakage, horizon labels, or fold calibration are not ready. |

Blocked packets must not be interpreted as `context_only_projection`.
`context_only_projection` is assigned only after an admissible review decides
that the event is useful as risk context but cannot support a quantitative
impact function or conditional-effect mapping.

Every evidence packet must also publish a deterministic next-action route:

| Readiness | Required next action |
|---|---|
| `blocked_missing_same_family_evidence` | Prepare bounded same-family event acquisition when source coverage is missing; if covered sources still do not provide enough observations, park the family and wait for future same-family events. |
| `blocked_mixed_family` | Run event taxonomy / interpretation refinement, split concrete child families or dossier candidates, then rebuild separate packets with ancestor/fallback lineage. |
| `blocked_missing_structured_evidence` | Run the program enrichment route for structured PIT fields such as release clocks, expectation/consensus, actual/surprise, subtype, and fixed horizon labels. |
| `blocked_missing_modelability_gates` | Run the shared model-task feature/evidence-generation stage for deterministic modelability gates: matched controls, overlap/confounder assessment, leakage assessment, fixed horizon labels, and fold calibration. |
| `admissible_for_context_only_review` | Run `event-context-projection-review`; do not run probability-function modelability review. |
| `admissible_for_modelability_review` | Run `event-family-modelability-review` to judge projection mode and probability-function class. |

The routing field is owned by the program. The
`run_event_family_modelability_next_actions.py` route runner must consume it and
write the next program queue artifact: acquisition task keys, structured
enrichment plan, modelability-gate evidence-generation plan, or semantic-review
handoff. These routes use the same model-task lifecycle semantics as other model
groups: acquisition fills source gaps, feature/evidence generation materializes
PIT-safe deterministic inputs and labels, semantic review consumes only
admissible handoffs, and model generation remains a later model-owned training
stage. Codex may execute the named semantic review skill only when routed there,
but it must not override provider acquisition, gate generation, training, or
model activation.

For macro-release families such as `cpi_release` and `ppi_release`,
`enrich_event_family_structured_evidence.py` materializes existing reviewed
Trading Economics calendar source files into `calendar_scheduled_event` and
`calendar_event_result` before packets are rebuilt. If the source contains
actual values but lacks consensus or forecast baselines, the rebuilt packet must
remain `blocked_missing_structured_evidence` rather than being promoted to
modelability review.

## Probability Function Classes

M03 event-family modelability chooses the allowed probability-function class and
trains concrete parameters within that allowed class.

Allowed classes are:

- `continuous_symmetric`
- `continuous_skewed`
- `heavy_tail`
- `zero_inflated_or_hurdle`
- `count_driven_compound`
- `mixture`
- `regime_state_machine`
- `episode_graph`
- `empirical_quantile`
- `none`

Count distributions such as Poisson or negative binomial may describe update or
shock-arrival counts. They must not directly model signed impact intensity
unless they are part of a compound model with a separate signed severity
distribution.

## M03 Responsibilities

M03 owns pre-replay event-universe materialization, event taxonomy governance,
taxonomy-node/effect-model-node modelability, and event-state projection:

- acquire or materialize the full fold point-in-time event universe before
  replay;
- define event taxonomy, node boundaries, child-node rules, and dossier boundaries;
- preserve taxonomy version, ancestor chain, semantic node, effect-model node, and fallback lineage;
- decide whether the effect-model node can be modeled at all;
- choose `projection_mode`;
- choose allowed `probability_function_class`;
- define required clocks, scales, phase vocabulary, scope vocabulary, and
  channel vocabulary;
- require multiple PIT-valid same-node or same-dossier observations before
  assigning a probability-function class;
- verify source coverage, dedupe, matched controls, overlap/confounder status,
  and leakage gates before Codex semantic review.
- train PIT-safe mappings from M03-approved event parameters to distribution
  parameters;
- output `event_state_projection` at each replay/live decision time;
- expose calibrated sign probabilities, quantiles, uncertainty mass, tail
  risks, target exposure probability, and option-expression suitability deltas.

M03 must not:

- consume raw news, raw filings, raw macro rows, or unreviewed event text;
- train on selected trades only;
- use selected-trade outcomes, replay failures, or post-fold residuals to decide
  which upstream event rows exist;
- use future news, future filings, future prices, or future volatility as
  inference inputs;
- issue trade, order, or option-structure commands.

## Replay Review Event-Attribution Responsibilities

Replay review owns post-replay residual-event attribution:

- consume replay-review failure, miss, overblock, underblock, and path-deviation
  scopes before starting attribution;
- consume the pre-replay M03 event-impact ledger as fixed upstream evidence;
- identify relationships between event evidence and model failure modes;
- produce event-attribution rows, missed-event flags, and event-family
  follow-up candidates for later M03 evidence generation;
- verify that residual findings are not already explained by upstream M03 event
  state, M04 decision evidence, or optional M05 expression evidence.

Replay review event attribution must not:

- own pre-replay event-universe discovery;
- choose upstream event rows by looking at selected-trade outcomes;
- rewrite M03 event eligibility after replay;
- infer signed direction or magnitude for a specific event as a replay shortcut;
- choose concrete M03 function parameters;
- train M03 parameters;
- use future revisions as inference inputs;
- perform provider calls inside Codex review.

## Program And Agent Boundary

Program-controlled gates own acquisition scope, provider task keys, source
coverage, sample thresholds, PIT clocks, dedupe, overlap/confounder checks,
fold readiness, stop/retry conditions, and artifact write locations.

Codex skills are semantic reviewers. They may judge event interpretation,
taxonomy, modelability reasoning, probability-function class fit, and
context-only rationale. They must not control provider dispatch, expand scope,
train parameters, or replace deterministic gates.

## Modelability Trial Route

The first implemented trial route supports several program-built event-family evidence
packets:

- AAPL `company_earnings_or_financial_results` from SEC company financials.
- `target_product_price_change_news` from symbol-scoped Alpaca news rows.
- AAPL `target_product_launch_news` from symbol-scoped Alpaca news rows.
- AAPL `target_supply_chain_disruption_news` from symbol-scoped Alpaca news
  rows.
- AAPL `target_regulatory_antitrust_news` from symbol-scoped Alpaca news rows.
- `market_session_calendar_event` from deterministic non-weekend market
  holiday / early-close calendar rows.
- `cpi_release` and `ppi_release` from structured scheduled macro calendar
  rows.

The route is:

1. Create `model_06_event_family_modelability_acquisition_plan`.
2. Dispatch bounded provider tasks through the reviewed event-feed dispatcher.
3. Build `model_06_event_family_modelability_evidence_packet` from acquired
   same-family PIT evidence.
4. Follow the packet's deterministic `required_next_action`.
   The route runner writes `model_06_event_family_modelability_next_action_route`
   and `model_06_event_family_modelability_next_action_summary` artifacts so a
   blocked packet enters the next program queue instead of becoming a human or
   chat-level stopping point.
5. Run `event-family-modelability-review` only for packets with
   `admissible_for_modelability_review`; blocked packets must first be repaired
   by the program-owned route named by the packet.
6. If M03 accepts a projection mode and probability-function class, train M03
   parameter mappings through a separate PIT-safe training path.

The evidence packet is not a modelability decision and is not a special M06-only
workflow stage. Current artifact names may retain `model_06_event_family_*`
compatibility tokens, but the lifecycle owner is M03 event impact. Current trial reviews show that sample count alone
is not enough: impact-function or conditional-effect approval still requires
subtype homogeneity, matched controls, leakage/overlap checks, and fold-frozen
calibration/ablation evidence.
