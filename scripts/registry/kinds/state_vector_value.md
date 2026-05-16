# state_vector_value

Use this kind only for reviewed **core scalar score tokens** that belong to an accepted model state/context-vector contract.

A `state_vector_value` row may represent:

- Layer 1/2 compact scalar score names such as `1_market_direction_score` or `2_sector_relative_direction_score`;
- Layer 3 score-family names such as `3_target_direction_score_<window>` or `3_tradability_score_<window>`;
- Layer 8 event-context score-family names such as `8_event_gap_risk_score_<horizon>` or `8_event_market_impact_score_<horizon>`;
- Layer 5 final adjusted alpha-confidence score-family names such as `4_alpha_direction_score_<horizon>` or `4_alpha_tradability_score_<horizon>`;
- Layer 6 position-projection score-family names such as `5_target_exposure_score_<horizon>` or `5_position_gap_score_<horizon>`;
- Layer 7 underlying-action score-family names such as `6_underlying_trade_eligibility_score_<horizon>` or `6_underlying_action_confidence_score_<horizon>`;
- Legacy `8_*` option-expression score-family names for the conceptual Layer 7 option-expression boundary, such as `7_option_contract_fit_score_<horizon>` or `7_option_expression_confidence_score_<horizon>`.

Payloads must match the reviewed model contract exactly. Use compact numeric prefixes because core score tokens carry layer ownership directly.

Do not register every state-vector payload part here. Block names, group names, windows, enum values, diagnostics, routing/audit fields, research payloads, unresolved source-mapping placeholders, and physical storage/schema slots should stay in model-local docs/contracts unless a later manager-phase durable interface review promotes them through the appropriate narrow registry kind.

Reject from this kind:

- storage-only table columns, request parameters, ids, references, timestamps, paths, free-text fields, and ordinary schema slots; use the narrowest field-like kind instead;
- state/context-vector block/group names such as `market_state_features`, `target_state_features`, `target_price_state`, `event_timing_context`, or `event_impact_scope_context`;
- diagnostic values such as coverage/data-quality/state-quality/evidence-count payloads;
- routing/audit values such as handoff, eligibility, reason-code, rank, enum, or window tokens;
- research-only payloads such as embeddings or cluster ids;
- unresolved source/feature mapping placeholders;
- model ids, data-feature names, data-source names, scripts, templates, or repository names;
- generic lifecycle/review/test/docs/status values;
- non-reviewed experiment labels, strategy labels, or concrete execution/routing values;
- concrete planned-action enums, no-trade decisions, order quantities, account-risk allocations, option-contract identifiers, strike/DTE/delta selections, order types, broker fields, fill/account state, or final verdicts. Reviewed Layer 6/7/8 scalar score-family tokens are allowed here only when they remain score tokens rather than executable instructions.

A state-vector value may later be stored in tables, files, or feature/model rows, but the registry row owns only the reviewed core score token. Other contract payloads remain documented in their model-local contracts until manager-phase interface promotion.
