# state_vector_value

Use this kind for reviewed value tokens that belong to an accepted model state-vector contract.

A `state_vector_value` row may represent:

- nested state-vector block names, group names, score-family names, diagnostic payload names, or derived state-vector payload names;
- fixed enum/window values accepted by the state-vector contract;
- contract-local value tokens that are consumed as state evidence rather than generic table columns.

Keys and payloads must carry the owning model-layer prefix. Registry keys use `MODEL_NN_<TOKEN>_VALUE`, for example `MODEL_01_MARKET_DIRECTION_SCORE_VALUE`, `MODEL_02_SECTOR_HANDOFF_STATE_SELECTED_VALUE`, or `MODEL_03_MARKET_STATE_FEATURES_VALUE`. Payloads use compact numeric prefixes such as `1_market_direction_score`, `2_sector_relative_direction_score`, `2_sector_handoff_state_selected`, `3_market_state_features`, or `3_state_window_5min`. Do not keep bare payload tokens inside `state_vector_value`.

When a reviewed model-output payload token is part of the state-vector contract, classify that registry row as `state_vector_value` instead of also keeping it as `field`. Use field-like kinds only for storage/schema slots whose primary reviewed role is physical carriage rather than state-vector semantics.

Reject from this kind:

- storage-only table columns, request parameters, ids, references, timestamps, paths, free-text fields, and ordinary schema slots; use the narrowest field-like kind instead;
- model ids, data-feature names, data-source names, scripts, templates, or repository names;
- generic lifecycle/review/test/docs/status values; use `status_value` unless the value is specifically part of a model state-vector payload;
- non-reviewed experiment labels or downstream action/strategy/position-sizing values.

A state-vector value may later be stored in tables, files, or feature/model rows, but the registry row owns the reviewed contract token rather than duplicating a separate generic field registration for the same token.
