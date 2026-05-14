-- Fix field registration for target Layer 2 context mapping after canonical field hygiene checks.

DELETE FROM trading_registry
WHERE id IN ('fld_TL2CTX001', 'fld_TL2CTX012');

UPDATE trading_registry
SET applies_to = CASE
      WHEN applies_to LIKE '%target_layer2_context_mapping%' THEN applies_to
      ELSE applies_to || ';target_layer2_context_mapping;target_layer2_context_mapping_v1;layer_03_plus_target_study'
    END,
    note = 'Target symbol being studied. Used by manager model-training workflow state/plan surfaces and target-to-Layer-2 context mapping rows.',
    updated_at = NOW()
WHERE key = 'TARGET_SYMBOL';

UPDATE trading_registry
SET applies_to = CASE
      WHEN applies_to LIKE '%target_layer2_context_mapping%' THEN applies_to
      ELSE applies_to || ';target_layer2_context_mapping;target_layer2_context_mapping_v1'
    END,
    note = 'Human-readable interpretation text for reviewed shared mapping or market-context rows.',
    updated_at = NOW()
WHERE key = 'INTERPRETATION';

UPDATE trading_registry
SET key = 'TARGET_LAYER2_MAPPING_METHOD_TYPE',
    payload = 'layer2_mapping_method_type',
    note = 'Reviewed method type used to map the target to Layer 2 context.',
    updated_at = NOW()
WHERE id = 'fld_TL2CTX005';

UPDATE trading_registry
SET key = 'TARGET_PROXY_ROLE_TYPE',
    payload = 'proxy_role_type',
    note = 'Role type of the target-specific proxy, such as spot_etf_optionable_proxy_type.',
    updated_at = NOW()
WHERE id = 'fld_TL2CTX009';
