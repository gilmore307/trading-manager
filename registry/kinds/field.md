# Field

## Kind Boundary

Canonical shared non-identity, non-temporal, non-classification field names used in task records, receipts, manifests, requests, review artifacts, maintenance outputs, and helper-facing schemas.

## Range

Register field names only. Do not use this kind for status values, repository names, config values, artifact instances, or free-form documentation labels.

## Reject Or Re-scope

Reject or re-scope entries that are actually:

- status values;
- repository names;
- identity/name/title/reference fields;
- temporal/date/time fields;
- classification axes;
- filesystem paths;
- config defaults;

## Usage Metadata

Every `field` entry must populate `trading_registry.applies_to`. Use semicolon-separated scopes when a field belongs to multiple tables, files, contracts, templates, or data shapes. Do not add a field entry until its first valid usage scope is known.

## Naming Rule

Prefer the broadest truthful field key.

- Reusable metrics or columns should use generic metric/category keys, such as `BAR_CLOSE`, `QUOTE_BID`, `TRADE_SIZE`, or `GREEK_DELTA`.
- Asset-class keys are acceptable when the field is inherently asset-class-specific, such as option contract fields.
- Scenario-specific prefixes belong only to fields whose meaning is specific to that scenario, such as `OPTION_EVENT_DETAIL_PRICE_VS_ASK`.
- Do not keep implementation/template-era prefixes like `OPTION_TEMPLATE_*` when the field is a reusable current data field.
