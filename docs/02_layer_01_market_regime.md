# Layer 01 - Market Regime

This file records only the manager boundary for Layer 1. Data construction and model implementation live in component repositories.

## Purpose

Layer 1 builds broad-market context. It conditions all downstream work but does not pick sectors, targets, strategies, positions, options, or actions.

## Canonical Surfaces

```text
trading_data.source_01_market_regime
trading_data.feature_01_market_regime
trading_model.model_01_market_regime
trading_model.model_01_market_regime_explainability
trading_model.model_01_market_regime_diagnostics
```

## Manager Duties

- Register and preserve shared names used in requests/receipts.
- Plan historical market-regime acquisition and feature stages.
- Validate handoff payloads before provider dispatch.
- Track run/artifact/ready evidence and scheduler state.
- Block downstream use when point-in-time coverage, feature readiness, or evidence is incomplete.

## Naming Rule

Layer-owned score tokens use compact numeric prefixes, for example:

```text
1_market_direction_score
1_market_transition_risk_score
1_data_quality_score
```

Generic lineage fields such as `available_time`, `model_id`, `model_version`, and receipt metadata do not need layer prefixes.

## Hard Boundaries

Layer 1 must not emit sector ranking, target selection, strategy choice, exposure, option selection, final action, or broker/account mutation.
