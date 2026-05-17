# Data Kind Contract Rule

`data_kind` is reserved for final saved data shapes with accepted storage contracts.

## Admission Test

A concept may be registered as `data_kind` only when at least one condition is true:

1. `path` points to a reviewed current storage/template/contract artifact for the final shape.
2. Directly scoped registered fields define the final shape and a current repo-owned doc explains the contract.
3. A reviewed migration explicitly states that the durable category is contract-level even before a template file exists.

If none is true, do not use `data_kind`.

## Not Data Kinds

- provider documentation pages;
- provider endpoint names;
- raw trades, quotes, books, Greeks, filings, calendars, or transient scrape inputs;
- entitlement-blocked families;
- preview templates;
- wishlist concepts;
- source outputs;
- feature outputs.

Use `provider`, `data_feed`, `feed_capability`, `data_source`, or `data_feature` instead.

## Review Checklist

Before adding a `data_kind` row, confirm:

- final saved shape is accepted;
- storage owner is clear;
- schema/field contract exists or is intentionally deferred by reviewed migration;
- consuming repo is known;
- payload is stable snake_case;
- path, if present, points to a current contract artifact.
