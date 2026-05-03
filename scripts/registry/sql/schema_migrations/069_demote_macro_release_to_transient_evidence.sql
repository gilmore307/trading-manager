-- Demote macro_release from final saved data kind to transient source evidence.
-- Target engine: PostgreSQL.

UPDATE trading_registry
SET path = '',
    applies_to = 'macro_data_transient_evidence',
    artifact_sync_policy = 'review_on_merge',
    note = 'Transient cleaned source-evidence row for macro API actual values; not a final saved/model-facing data kind. macro_release_event is the final event-layer output and owns market-impact semantics. Do not use macro_release as an independent alpha table alongside event/reaction models.'
WHERE kind = 'data_kind'
  AND key = 'MACRO_RELEASE';
