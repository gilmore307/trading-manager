# Event Impact Distribution

This file owns the current M03/M06 event-model contract. It is a contract
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

M04 and M05 consume distribution summaries such as mean, quantiles, sign
probabilities, uncertainty mass, and adverse/favorable tail probabilities. They
do not consume raw event text.

## Projection Modes

M06 assigns exactly one projection mode for an event family after deterministic
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

## Event Family Boundary

An event family is a concrete repeated phenomenon with comparable mechanics,
not a data source, feed, or broad bucket.

Valid family examples:

- `target_product_price_change_news`: product price increase/decrease news for
  a target such as Apple.
- `cpi_release`: CPI release events.
- `ppi_release`: PPI release events.
- `company_earnings_or_financial_results`: company financial results and
  earnings/report filings.

Invalid family examples:

- `news`: source class only.
- `target_news_or_disclosure`: source/category bucket only.
- `scheduled_macro_release`: release calendar category only.
- `macro`: domain bucket only.

M06 evidence packets must reject source/category buckets before Codex review.
Source rows may still feed a concrete family packet, for example Alpaca/GDELT
news rows feeding `target_product_price_change_news`, or scheduled macro
calendar rows feeding `cpi_release`.

## Probability Function Classes

M06 chooses the allowed probability-function class. M03 trains concrete
parameters within that allowed class.

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

## M06 Responsibilities

M06 owns event-family modelability governance:

- define event family and taxonomy boundaries;
- decide whether the family can be modeled at all;
- choose `projection_mode`;
- choose allowed `probability_function_class`;
- define required clocks, scales, phase vocabulary, scope vocabulary, and
  channel vocabulary;
- require multiple PIT-valid same-family observations before assigning a
  probability-function class;
- verify source coverage, dedupe, matched controls, overlap/confounder status,
  and leakage gates before Codex semantic review.

M06 must not:

- infer signed direction or magnitude for a specific event;
- choose concrete function parameters;
- train M03 parameters;
- use selected-trade outcomes to filter earlier event-family evidence;
- use future revisions as inference inputs;
- perform provider calls inside Codex review.

## M03 Responsibilities

M03 owns event-state projection:

- consume standardized event parameters and M06-approved family specs;
- train PIT-safe mappings from event parameters to distribution parameters;
- output `event_state_projection` at each replay/live decision time;
- expose calibrated sign probabilities, quantiles, uncertainty mass, tail
  risks, target exposure probability, and option-expression suitability deltas.

M03 must not:

- decide event-family modelability;
- invent a distribution class not allowed by M06;
- train on selected trades only;
- use future news, future filings, future prices, or future volatility as
  inference inputs;
- issue trade, order, or option-structure commands.

## Program And Agent Boundary

Program-controlled gates own acquisition scope, provider task keys, source
coverage, sample thresholds, PIT clocks, dedupe, overlap/confounder checks,
fold readiness, stop/retry conditions, and artifact write locations.

Codex skills are semantic reviewers. They may judge event interpretation,
taxonomy, modelability reasoning, probability-function class fit, and
context-only rationale. They must not control provider dispatch, expand scope,
train parameters, or replace deterministic gates.

## Modelability Trial Route

The first implemented trial route supports several program-built M06 evidence
packets:

- AAPL `company_earnings_or_financial_results` from SEC company financials.
- AAPL `target_product_price_change_news` from symbol-scoped Alpaca news rows.
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
4. Run `event-family-modelability-review`.
5. If M06 accepts a projection mode and probability-function class, train M03
   parameter mappings through a separate PIT-safe training path.

The evidence packet is not a modelability decision. It is only the deterministic
input bundle for Codex semantic review. Current trial reviews show that sample
count alone is not enough: impact-function or conditional-effect approval still
requires subtype homogeneity, matched controls, leakage/overlap checks, and
fold-frozen calibration/ablation evidence.
