# Train Replay Realtime Input Parity

Status: accepted cross-phase model-input contract
Date: 2026-06-28

## Purpose

Training, replay, and realtime trading may use different physical artifacts, but
they must resolve model decision inputs through the same declared semantics.
This prevents a model from learning one information surface, being evaluated on
another, and then trading on a third.

This is a model-input contract, not a generic runtime-data contract. Execution
guardrails such as broker/account state, hard halts, restriction checks, and
emergency kill switches may be broader than trained model inputs, but they must
not be represented as trained model signals unless accepted by the model
governance route.

## Core Rule

For a model bundle to be valid across training, replay, and realtime trading,
each consumed model input family must declare the same:

- semantic input family;
- canonical registry term;
- source identity or derived-context owner;
- feature/vector definition;
- point-in-time event time, system availability time, and tradeable time rule;
- freshness and data-quality rule;
- missing/degraded/fallback states;
- governance status: trained/accepted model input, neutral/no-signal state, or
  advisory-only runtime context;
- phase resolution for training, replay, and realtime.

Source names alone are not enough. A historical bar, replay snapshot, and live
snapshot with the same provider label are parity-compatible only when the
adjustment policy, timestamp convention, transformation, and point-in-time
availability rule match the declared model input contract.

## Phase Resolution

| Phase | Physical route | Parity requirement |
|---|---|---|
| Training | Historical source artifacts, cleaned data, feature manifests, model training rows | Broad sampling is allowed, but rows must use the declared semantic family, feature/vector definition, clocks, and fallback states. |
| Replay | Frozen replay snapshot plus bounded on-demand replay cache | Replay must consume the same semantic families under a historical clock; missing on-demand data must be represented with the same missing/degraded states used by training or explicitly marked replay-only stress. |
| Realtime | Current provider observations, realtime context refs, active model/config refs | Realtime may resolve current refs instead of historical artifacts, but the refs must map to the same semantic families and governance status before they can affect model decisions. |

Promotion readiness is the handoff point into realtime/shadow execution. A
promotion-readiness record must carry `model_input_context_bundle` with
`historical_dataset_snapshot_ref`, `frozen_model_config_ref`, and M02-M06
upstream context refs. Realtime feature snapshots consume that bundle instead
of accepting placeholder context refs or requiring an operator to manually
reconstruct the training/replay input lineage.

## Required Distinctions

- Training sample breadth may exceed live routing breadth. That is valid only
  when the feature semantics remain aligned and promotion reports both broad
  generalization and live-route simulation.
- Realtime safety context may exceed trained model context. Broker/account
  guardrails, restriction checks, halt checks, and kill switches are execution
  controls, not trained model inputs.
- Untrained event or calendar context may be present in realtime. It remains
  advisory evidence for C07/trading review until the M06/M03 governance route
  accepts it as a model input family or state overlay.
- Missing data must be semantic, not silent. Examples: `not_in_dataset`,
  `feed_outage`, `source_delayed`, `stale_but_usable`, `structurally_not_applicable`,
  and `advisory_only_untrained_context` are different states and must not be
  collapsed into a generic null.

## M06 Event Parity Matrix

M06 is the first required parity audit surface because it consumes the richest
event/calendar context and feeds both replay attribution and realtime event-risk
watch.

| Semantic family | Training resolution | Replay resolution | Realtime resolution | Governance state |
|---|---|---|---|---|
| Company/news event context | PIT Alpaca/GDELT/news artifacts and accepted event interpretation rows | Frozen replay snapshot plus bounded on-demand candidate news/event cache | Current news/event refs or accepted derived governance refs | Trained only after M06/M03 event-family acceptance; otherwise advisory |
| Company release/result context | SEC-derived filing/submission/company-financial evidence with availability clocks | Frozen SEC/company-financial refs for the replay window | SEC/company release context refs; Nasdaq current/future schedule only as pre-event shell | SEC facts may be result/context; signed surprise claims require accepted PIT baselines |
| Macro release calendar | Trading Economics calendar artifacts with actual/previous/consensus clocks where available | Frozen TE macro rows for the replay window | `realtime_calendar_context` TE macro release refs | Trained only where the model contract accepts the macro family; otherwise calendar context |
| Market structure calendar | Market session, holiday, early close, option expiry, triple-witching, and rebalance calendar rows | Frozen market-session/special-calendar rows for the replay window | `realtime_calendar_context` market-session/special-calendar refs | Calendar state/tradeability context; not a broker action by itself |
| Option activity context | PIT option-chain/quote/trade/IV/OI evidence where available | Replay-triggered option snapshots when components request option expression | ThetaData/Alpaca option refs where approved | Trained option-expression/event-risk input only when option coverage and clocks are accepted |

M01-M05 parity audits should use the same columns instead of inventing separate
phase-specific vocabulary.

## Acceptance

A training/replay/realtime input route is accepted only when:

1. The semantic family and registry term are declared.
2. The phase-specific artifact/ref route is named for training, replay, and
   realtime or explicitly marked not applicable.
3. PIT clock and availability rules are stated.
4. Missing/degraded states are enumerated and not collapsed.
5. Advisory-only runtime context is separated from trained/accepted model input.
6. Replay and realtime can cite the same model-surface feature/vector contract
   used during training.

If a route cannot meet these rules, it may still exist as diagnostic or safety
context, but it must not be represented as a trained model decision input.
