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

For `field` entries, populate `trading_registry.applies_to` when the field is tied to a known table, file, contract, template, or data shape. Leave it empty only when the usage surface is intentionally broad or not yet settled.
