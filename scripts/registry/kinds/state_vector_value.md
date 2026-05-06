# state_vector_value

Use this kind only for reviewed **core scalar score tokens** that belong to an accepted model state-vector contract.

A `state_vector_value` row may represent:

- Layer 1/2 compact scalar score names such as `1_market_direction_score` or `2_sector_relative_direction_score`;
- Layer 3 score-family names such as `3_target_direction_score_<window>` or `3_tradability_score_<window>`.

Payloads must match the reviewed model contract exactly. Use compact numeric prefixes because core score tokens carry layer ownership directly.

Do not register every state-vector payload part here. Block names, group names, windows, enum values, diagnostics, routing/audit fields, research payloads, unresolved source-mapping placeholders, and physical storage/schema slots should stay in model-local docs/contracts unless a later manager-phase durable interface review promotes them through the appropriate narrow registry kind.

Reject from this kind:

- storage-only table columns, request parameters, ids, references, timestamps, paths, free-text fields, and ordinary schema slots; use the narrowest field-like kind instead;
- state-vector block/group names such as `market_state_features`, `target_state_features`, or `target_price_state`;
- diagnostic values such as coverage/data-quality/state-quality/evidence-count payloads;
- routing/audit values such as handoff, eligibility, reason-code, rank, enum, or window tokens;
- research-only payloads such as embeddings or cluster ids;
- unresolved source/feature mapping placeholders;
- model ids, data-feature names, data-source names, scripts, templates, or repository names;
- generic lifecycle/review/test/docs/status values;
- non-reviewed experiment labels or downstream action/strategy/position-sizing values.

A state-vector value may later be stored in tables, files, or feature/model rows, but the registry row owns only the reviewed core score token. Other contract payloads remain documented in their model-local contracts until manager-phase interface promotion.
