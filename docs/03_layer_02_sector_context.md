# Layer 02 - Sector Context

This file records only the manager boundary for Layer 2. Data construction and model implementation live in component repositories.

## Purpose

Layer 2 builds sector and industry context from the broad-market state. It can produce sector/industry handoff states for downstream anonymous target construction.

## Canonical Surfaces

```text
trading_data.feature_02_sector_context
trading_model.model_02_sector_context
trading_model.model_02_sector_context_explainability
trading_model.model_02_sector_context_diagnostics
```

`source_02_target_candidate_holdings` is downstream candidate-preparation evidence. It is not the core Layer 2 model output.

## Manager Duties

- Register sector-context names and allowed handoff states.
- Plan and validate historical sector/industry data acquisition.
- Track coverage, receipts, and ready signals.
- Keep Layer 2 work targetless until downstream target stages are explicitly admitted.

## Allowed Handoff States

```text
selected | watch | blocked | insufficient_data
```

## Naming Rule

Layer-owned score tokens use compact numeric prefixes, for example:

```text
2_trend_stability_score
2_sector_handoff_state
2_state_quality_score
```

## Hard Boundaries

Layer 2 must not select final symbols, strategies, option contracts, position sizes, final actions, or broker/account mutation.
