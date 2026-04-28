-- Prune deprecated macro_data-era references that are not used by the current
-- Trading Economics/event-overlay plan and have no active source/interface/data
-- contract role. These were briefly restored as terms during the data_kind
-- cleanup correction, but deprecated_macro_* scopes are not active registry
-- semantics.

DELETE FROM trading_registry
WHERE kind = 'term'
  AND (
    applies_to = 'deprecated_macro_data_source_reference'
    OR applies_to = 'deprecated_macro_data_transient_evidence'
  );
