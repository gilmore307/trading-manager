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
