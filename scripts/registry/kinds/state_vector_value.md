# state_vector_value

Use this kind for reviewed value tokens that belong to an accepted model state-vector contract.

A `state_vector_value` row may represent:

- nested state-vector block names, group names, score-family names, diagnostic payload names, or derived state-vector payload names;
- fixed enum/window values accepted by the state-vector contract;
- contract-local value tokens that are consumed as state evidence rather than generic table columns.

Every payload must include the owning model layer as a numeric prefix, for example `3_market_state_features` for a Layer 3 TargetStateVector value. Do not register bare state-vector values such as `market_state_features`, `sector_confirmed`, or `5min` when the value belongs to a numbered model contract.

Reject from this kind:

- table columns, request parameters, ids, references, timestamps, paths, free-text fields, and ordinary schema slots; use the narrowest field-like kind instead;
- model ids, data-feature names, data-source names, scripts, templates, or repository names;
- generic lifecycle/review/test/docs/status values; use `status_value` unless the value is specifically part of a model state-vector payload;
- non-reviewed experiment labels or downstream action/strategy/position-sizing values.

A state-vector value may be carried by feature/model rows, but this kind classifies the semantic token inside the reviewed vector contract, not the physical storage column that contains it.
