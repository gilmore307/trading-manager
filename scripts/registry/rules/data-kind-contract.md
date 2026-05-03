# Data Kind Contract Rules

## Purpose

This file owns the cross-kind rule for `data_kind` rows. It prevents broad provider/source concepts, transient inputs, and deprecated preview templates from being promoted into final saved data-shape contracts.

Per-kind wording lives in `../kinds/data_kind.md`; this file owns the broader data-shape routing rule.

## Active Data Kind Requirement

A `data_kind` row may be active only when it represents an accepted final saved data shape with a current storage contract.

At least one of the following must be true:

1. `path` points to a current reviewed storage/template/contract artifact for the final saved shape.
2. The row has directly scoped registered fields that define the final shape and the contract is documented in a current repo-owned file.
3. A reviewed migration or rule explicitly states that this durable category is intentionally contract-level even before a template file exists.

If none of those are true, do not register the concept as `data_kind`.

## What Does Not Qualify

Do not use `data_kind` for:

- provider documentation pages;
- provider endpoint names or record families;
- raw trades, quotes, order books, Greeks, snapshots, filings, calendar scrape inputs, or entitlement-gated families unless they become accepted final saved templates;
- transient source evidence;
- feed-interface catalog capabilities;
- broad wishlist concepts with no active route or consumer;
- deprecated preview files;
- component-local implementation details;
- control-plane-facing source outputs or deterministic feature outputs.

Route those rows as follows:

| Concept | Preferred registry kind |
|---|---|
| Provider/source owner identity | `provider` |
| Implemented feed connector | `data_feed` |
| Endpoint/record-family capability, raw input, entitlement category | `feed_capability` |
| Runnable source output requested by the manager | `data_source` |
| Deterministic model-facing feature output | `data_feature` |
| Human-only definition | `term` |

## Path Rule

`data_kind.path` should point to a current final-shape contract artifact when one exists.

Provider documentation URLs belong on `provider`, `feed_capability`, or `term` rows. Do not keep a provider documentation URL on `data_kind.path` as evidence of final saved-shape status.

## Cleanup Rule

When a review finds a weak `data_kind` row:

1. Decide whether the concept is a final saved shape, a source/feed capability, or only glossary language.
2. If it is a final saved shape, add or point to the current contract artifact and register directly scoped fields where needed.
3. If it is not a final saved shape, migrate it to the narrower active kind or remove it.
4. Preserve needed public documentation URLs on provider/feed-capability/term rows.
5. Regenerate `../current.csv` from SQL and verify downstream references before deleting or repurposing rows.

## Current Posture

The active registry may allow the `data_kind` kind even when `../current.csv` has zero current `data_kind` rows. That is acceptable: the kind remains available for future accepted final saved-shape contracts, but rows should not be added speculatively.
