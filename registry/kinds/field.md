# Field

## Kind Boundary

Canonical shared field names used in task records, receipts, manifests, requests, review artifacts, maintenance outputs, and helper-facing schemas.

## Range

Register field names only. Do not use this kind for status values, repository names, config values, artifact instances, or free-form documentation labels.

## Reject Or Re-scope

Reject or re-scope entries that are actually:

- status values;
- repository names;
- filesystem paths;
- config defaults;

## Usage Metadata

Every `field` entry must populate `trading_registry.applies_to`. Use semicolon-separated scopes when a field belongs to multiple tables, files, contracts, templates, or data shapes. Do not add a field entry until its first valid usage scope is known.

Every `field` entry must also populate exactly one `trading_registry.field_category` value. Non-`field` entries must leave `field_category` blank. The category records the field's primary semantic role, not every downstream use.

## Exclusive Field Categories

Allowed categories are mutually exclusive by schema constraint:

- `boolean` — true/false indicators.
- `classification` — taxonomy, type, category, scope, kind, grouping, or controlled-label fields.
- `collection` — list, array, set, or repeated-value fields.
- `execution_contract` — task/control contract fields such as goals, scopes, constraints, policies, parameters, expectations, and caveats.
- `identity` — stable identifiers, symbols, tickers, contract symbols, and other entity identity fields.
- `nested_object` — structured object/container fields with child fields.
- `numeric_measure` — prices, scores, ratios, percentages, ranks, greeks, values, and other numeric measurements.
- `quantity` — counts, sizes, shares, and volume-like quantities.
- `reference` — paths, URLs, files, directories, output references, source references, and artifact locators.
- `secret` — source-secret JSON keys or credential/config secret-addressing fields.
- `state` — lifecycle, readiness, review, acceptance, error/status, or other state-machine fields.
- `temporal` — timestamps, dates, times, intervals, expirations, and availability moments.
- `text` — human-readable names, titles, summaries, explanations, errors, domains, providers, or other free text.

When a field appears ambiguous, choose the most specific semantic category above and record the rationale in `note` if review confusion is likely. Do not duplicate one field across categories.

## Naming Rule

Prefer the broadest truthful field key.

- Reusable metrics or columns should use generic metric/category keys, such as `BAR_CLOSE`, `QUOTE_BID`, `TRADE_SIZE`, or `GREEK_DELTA`.
- Asset-class keys are acceptable when the field is inherently asset-class-specific, such as option contract fields.
- Scenario-specific prefixes belong only to fields whose meaning is specific to that scenario, such as `OPTION_EVENT_DETAIL_PRICE_VS_ASK`.
- Do not keep implementation/template-era prefixes like `OPTION_TEMPLATE_*` when the field is a reusable current data field.
