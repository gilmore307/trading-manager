-- Tighten classification_field semantics around the classification axis, not the
-- component/template that first used it.

-- GDELT's impact-scope hint is the same semantic axis as event impact_scope.
UPDATE trading_registry
SET applies_to = 'trading_event_template;event_factor_template;event_analysis_report_template;gdelt_article_template',
    note = 'event impact layer or upstream extraction hint such as market, sector, industry, theme, security, multi_security, macro, or unknown; used to avoid treating broad-market events as single-stock events. Classification value should use a stable lowercase token vocabulary unless the source contract explicitly requires another reviewed encoding.'
WHERE id = 'fld_EVT043';

DELETE FROM trading_registry
WHERE id = 'fld_GDLT014';

-- Source-provider event/category labels are source event types; `category` is
-- too vague for a shared semantic registry field.
UPDATE trading_registry
SET key = 'SOURCE_EVENT_TYPE',
    payload = 'source_event_type',
    note = 'source-provided event/category type label before normalized event taxonomy mapping. Classification value should use a stable lowercase token vocabulary unless the source contract explicitly requires another reviewed encoding.'
WHERE id = 'fld_TEC004';

-- `side_hint` is a trade-side classification in the option event detail.
UPDATE trading_registry
SET key = 'TRADE_SIDE_TYPE',
    payload = 'trade_side_type',
    note = 'trade-side classification such as ask_side when an option event fired. Classification value should use a stable lowercase token vocabulary unless the source contract explicitly requires another reviewed encoding.'
WHERE id = 'fld_OPD009';
