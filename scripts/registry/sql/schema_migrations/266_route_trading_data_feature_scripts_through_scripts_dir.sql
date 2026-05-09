-- Route accepted trading-data feature generation entrypoints through scripts/ wrappers consistently.

UPDATE trading_registry
SET payload = 'python3 scripts/generate_feature_03_target_state_vector.py',
    path = '/root/projects/trading-data/scripts/generate_feature_03_target_state_vector.py',
    note = 'Stable callable entrypoint for reading source_03_target_state plus optional Layer 1/2 context rows and writing feature_03_target_state_vector JSONB market/sector/target/cross-state blocks. The script is a thin wrapper over the importable SQL implementation.',
    updated_at = NOW()
WHERE id = 'scr_F3TSVGEN'
  AND kind = 'script'
  AND key = 'FEATURE_03_TARGET_STATE_VECTOR_GENERATE';

UPDATE trading_registry
SET payload = 'python3 scripts/generate_feature_04_event_overlay.py',
    path = '/root/projects/trading-data/scripts/generate_feature_04_event_overlay.py',
    note = 'Stable callable entrypoint for reading source_04_event_overlay rows and writing feature_04_event_overlay JSONB event overview feature blocks. The script is a thin wrapper over the importable SQL implementation.',
    updated_at = NOW()
WHERE id = 'scr_F4EOGEN'
  AND kind = 'script'
  AND key = 'FEATURE_04_EVENT_OVERLAY_GENERATE';

UPDATE trading_registry
SET payload = 'python3 scripts/generate_feature_08_option_expression.py',
    path = '/root/projects/trading-data/scripts/generate_feature_08_option_expression.py',
    note = 'Stable callable entrypoint for reading source_05_option_expression rows and writing feature_08_option_expression JSONB option-candidate feature blocks. The script is a thin wrapper over the importable SQL implementation.',
    updated_at = NOW()
WHERE id = 'scr_F8OEGEN'
  AND kind = 'script'
  AND key = 'FEATURE_08_OPTION_EXPRESSION_GENERATE';
