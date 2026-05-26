-- Remove historical cleanup narration from active registry notes.
-- Migration history already records why these rows moved; current.csv should
-- describe only the current contract.

UPDATE trading_registry
SET note = regexp_replace(
        note,
        ' Registry cleanup 2026-04-28: restored from deleted data_kind history as feed_capability; not an active final saved data_kind\.$',
        '.'
    ),
    updated_at = NOW()
WHERE kind = 'feed_capability'
  AND note LIKE '%Registry cleanup 2026-04-28:%';

UPDATE trading_registry
SET note = regexp_replace(
        note,
        ' Registry cleanup 2026-04-28: restored from deleted data_kind history as term; not an active final saved data_kind\.$',
        '.'
    ),
    updated_at = NOW()
WHERE kind = 'term'
  AND note LIKE '%Registry cleanup 2026-04-28:%';

UPDATE trading_registry
SET note = 'Layer 3+ base-stack Model Worker stages run against the complete six-month rolling fold. Local input materializers must accept start_month/end_month ranges and must not assume one chronological month per run. Layer 10 starts after concentrated replay.',
    updated_at = NOW()
WHERE key = 'LAYER_THREE_PLUS_SIX_MONTH_FOLD_MATERIALIZATION';

UPDATE trading_registry
SET note = 'Provider dispatch executes bounded historical provider requests automatically after manager task-key preparation. It strips inactive provider-policy refs from runtime task keys and preserves broker/model-activation prohibitions.',
    updated_at = NOW()
WHERE key = 'PROVIDER_DISPATCH_EXECUTE_IS_AUTONOMOUS_HISTORICAL_ACQUISITION';
