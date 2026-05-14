-- Register reviewed target-to-Layer-2 context and auxiliary proxy mapping.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'out_TL2CTX001',
    'shared_artifact',
    'TARGET_LAYER2_CONTEXT_MAPPING_SHARED_CSV',
    'file',
    'trading-storage/main/shared/target_layer2_context_mapping.csv',
    '/root/projects/trading-storage/main/shared/target_layer2_context_mapping.csv',
    'trading-storage;trading-manager;trading-data;trading-model;target_layer2_context_mapping;target_layer2_context_mapping_v1;crypto_target_proxy;layer_03_plus_target_study',
    'sync_artifact',
    'Reviewed target-to-Layer-2 context and auxiliary proxy mapping. Layer 3+ target studies use this to map non-equity or externally scoped targets such as BTC/ETH/SOL to Layer 2 context while keeping single-asset ETF proxies out of Layer 1/2 context universes.'
  ),
  (
    'term_TL2CTX001',
    'term',
    'TARGET_LAYER2_CONTEXT_MAPPING_V1',
    'text',
    'target_layer2_context_mapping_v1',
    'trading-storage/main/shared/target_layer2_context_mapping.csv',
    'target_layer2_context_mapping;layer_03_plus_target_study;crypto_target_proxy',
    'sync_artifact',
    'Contract type for reviewed target-to-Layer-2 context mapping rows with target-specific auxiliary proxy references.'
  ),
  (
    'fld_TL2CTX001',
    'identity_field',
    'TARGET_LAYER2_CONTEXT_TARGET_SYMBOL',
    'field_name',
    'target_symbol',
    'trading-storage/main/shared/target_layer2_context_mapping.csv',
    'target_layer2_context_mapping;target_layer2_context_mapping_v1;layer_03_plus_target_study',
    'sync_artifact',
    'Target symbol being studied by Layer 3+ target-specific workflows.'
  ),
  (
    'fld_TL2CTX002',
    'classification_field',
    'TARGET_LAYER2_CONTEXT_TARGET_ASSET_CLASS',
    'field_name',
    'target_asset_class',
    'trading-storage/main/shared/target_layer2_context_mapping.csv',
    'target_layer2_context_mapping;target_layer2_context_mapping_v1;layer_03_plus_target_study',
    'sync_artifact',
    'Target asset class such as crypto_spot.'
  ),
  (
    'fld_TL2CTX003',
    'identity_field',
    'TARGET_LAYER2_CONTEXT_SPOT_REF',
    'field_name',
    'spot_ref',
    'trading-storage/main/shared/target_layer2_context_mapping.csv',
    'target_layer2_context_mapping;target_layer2_context_mapping_v1;crypto_target_proxy',
    'sync_artifact',
    'Canonical spot or underlying reference for the target before listed proxy mapping.'
  ),
  (
    'fld_TL2CTX004',
    'identity_field',
    'TARGET_LAYER2_CONTEXT_SYMBOL',
    'field_name',
    'layer2_context_symbol',
    'trading-storage/main/shared/target_layer2_context_mapping.csv',
    'target_layer2_context_mapping;target_layer2_context_mapping_v1;layer_02_sector_context',
    'sync_artifact',
    'Layer 2 context symbol used to represent the target business/sector/theme context.'
  ),
  (
    'fld_TL2CTX005',
    'classification_field',
    'TARGET_LAYER2_MAPPING_METHOD',
    'field_name',
    'layer2_mapping_method',
    'trading-storage/main/shared/target_layer2_context_mapping.csv',
    'target_layer2_context_mapping;target_layer2_context_mapping_v1',
    'sync_artifact',
    'Reviewed method used to map the target to Layer 2 context.'
  ),
  (
    'fld_TL2CTX006',
    'identity_field',
    'TARGET_LISTED_PROXY_SYMBOL',
    'field_name',
    'listed_proxy_symbol',
    'trading-storage/main/shared/target_layer2_context_mapping.csv',
    'target_layer2_context_mapping;target_layer2_context_mapping_v1;crypto_target_proxy',
    'sync_artifact',
    'Target-specific listed-market proxy symbol. Presence here does not make the proxy a Layer 1/2 context ETF.'
  ),
  (
    'fld_TL2CTX007',
    'identity_field',
    'TARGET_OPTIONABLE_PROXY_SYMBOL',
    'field_name',
    'optionable_proxy_symbol',
    'trading-storage/main/shared/target_layer2_context_mapping.csv',
    'target_layer2_context_mapping;target_layer2_context_mapping_v1;crypto_target_proxy',
    'sync_artifact',
    'Target-specific optionable proxy candidate symbol used only when optionability status permits the provider task.'
  ),
  (
    'fld_TL2CTX008',
    'classification_field',
    'TARGET_OPTIONABLE_PROXY_STATUS',
    'field_name',
    'optionable_proxy_status',
    'trading-storage/main/shared/target_layer2_context_mapping.csv',
    'target_layer2_context_mapping;target_layer2_context_mapping_v1;crypto_target_proxy',
    'sync_artifact',
    'Reviewed option-use status for the optionable proxy candidate, e.g. accepted_optionable_proxy or verify_before_option_use.'
  ),
  (
    'fld_TL2CTX009',
    'classification_field',
    'TARGET_PROXY_ROLE',
    'field_name',
    'proxy_role',
    'trading-storage/main/shared/target_layer2_context_mapping.csv',
    'target_layer2_context_mapping;target_layer2_context_mapping_v1;crypto_target_proxy',
    'sync_artifact',
    'Role of the target-specific proxy, such as spot_etf_optionable_proxy.'
  ),
  (
    'fld_TL2CTX010',
    'text_field',
    'TARGET_PROXY_USE',
    'field_name',
    'proxy_use',
    'trading-storage/main/shared/target_layer2_context_mapping.csv',
    'target_layer2_context_mapping;target_layer2_context_mapping_v1;crypto_target_proxy',
    'sync_artifact',
    'Plain-language allowed use of the target-specific proxy evidence.'
  ),
  (
    'fld_TL2CTX011',
    'classification_field',
    'TARGET_LAYER2_CONTEXT_REVIEW_STATUS',
    'field_name',
    'review_status',
    'trading-storage/main/shared/target_layer2_context_mapping.csv',
    'target_layer2_context_mapping;target_layer2_context_mapping_v1',
    'sync_artifact',
    'Review status for the target-to-context mapping row.'
  ),
  (
    'fld_TL2CTX012',
    'text_field',
    'TARGET_LAYER2_CONTEXT_INTERPRETATION',
    'field_name',
    'interpretation',
    'trading-storage/main/shared/target_layer2_context_mapping.csv',
    'target_layer2_context_mapping;target_layer2_context_mapping_v1',
    'sync_artifact',
    'Human-readable interpretation of the target context and auxiliary proxy mapping.'
  )
ON CONFLICT (id) DO UPDATE
SET kind = EXCLUDED.kind,
    key = EXCLUDED.key,
    payload_format = EXCLUDED.payload_format,
    payload = EXCLUDED.payload,
    path = EXCLUDED.path,
    applies_to = EXCLUDED.applies_to,
    artifact_sync_policy = EXCLUDED.artifact_sync_policy,
    note = EXCLUDED.note,
    updated_at = NOW();
