-- Remove drift/version suffixes from the active model-output quality semantic names.

UPDATE trading_registry
SET applies_to = replace(replace(applies_to, 'model_output_table_quality_audit_v1', 'model_output_table_quality_audit'), 'model_output_quality_gate_v1', 'model_output_quality_gate'),
    note = replace(replace(note, 'model_output_table_quality_audit_v1', 'model_output_table_quality_audit'), 'model_output_quality_gate_v1', 'model_output_quality_gate'),
    updated_at = NOW()
WHERE id IN ('scr_MOTQA001', 'scr_MOTQG001');
