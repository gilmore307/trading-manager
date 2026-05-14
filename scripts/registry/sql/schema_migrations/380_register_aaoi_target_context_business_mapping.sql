-- Register AAOI-style multi-row target context business mappings.

UPDATE trading_registry
SET applies_to = CASE
      WHEN applies_to LIKE '%target_context_business_mapping%' THEN applies_to
      ELSE applies_to || ';target_context_business_mapping;equity_business_context'
    END,
    note = 'Reviewed target-to-Layer-2 context and auxiliary proxy mapping. Layer 3+ target studies use this to map non-equity or externally scoped targets such as BTC/ETH/SOL to Layer 2 context while keeping single-asset ETF proxies out of Layer 1/2 context universes. It also supports multi-row equity business mappings such as AAOI to AIQ/XLK/SMH/XLC when each row has a reviewed context role.',
    updated_at = NOW()
WHERE key = 'TARGET_LAYER2_CONTEXT_MAPPING_SHARED_CSV';

UPDATE trading_registry
SET applies_to = CASE
      WHEN applies_to LIKE '%target_context_business_mapping%' THEN applies_to
      ELSE applies_to || ';target_context_business_mapping;equity_business_context'
    END,
    note = 'Contract type for reviewed target-to-Layer-2 context mapping rows with target-specific auxiliary proxy references or direct equity business-context rows. target_symbol is not unique; consumers must preserve multiple rows for one target.',
    updated_at = NOW()
WHERE key = 'TARGET_LAYER2_CONTEXT_MAPPING_V1';

UPDATE trading_registry
SET applies_to = CASE
      WHEN applies_to LIKE '%target_context_business_mapping%' THEN applies_to
      ELSE applies_to || ';target_context_business_mapping;equity_business_context'
    END,
    note = 'Manager-owned script-called agent review boundary for target-to-Layer-2 context mapping rows, target-specific auxiliary proxies, and multi-row equity business mappings.',
    updated_at = NOW()
WHERE key = 'TARGET_LAYER2_CONTEXT_AGENT_REVIEW';

UPDATE trading_registry
SET note = 'Target asset class such as crypto_spot or equity_common.',
    updated_at = NOW()
WHERE key = 'TARGET_LAYER2_CONTEXT_TARGET_ASSET_CLASS';

UPDATE trading_registry
SET note = 'Reviewed method type used to map the target to Layer 2 context, such as crypto_business_context, primary_business_context, secondary_sector_context, industry_chain_context, or weak_demand_side_context.',
    updated_at = NOW()
WHERE key = 'TARGET_LAYER2_MAPPING_METHOD_TYPE';

UPDATE trading_registry
SET note = 'Reviewed option-use status for the optionable proxy candidate, e.g. accepted_optionable_proxy, verify_before_option_use, or not_applicable when no auxiliary proxy is used.',
    updated_at = NOW()
WHERE key = 'TARGET_OPTIONABLE_PROXY_STATUS';

UPDATE trading_registry
SET note = 'Role type of the target-specific proxy or direct-equity no-proxy row, such as spot_etf_optionable_proxy_type or no_auxiliary_proxy_type.',
    updated_at = NOW()
WHERE key = 'TARGET_PROXY_ROLE_TYPE';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'term_TL2CTX002',
    'term',
    'TARGET_CONTEXT_BUSINESS_MAPPING',
    'text',
    'target_context_business_mapping',
    'trading-storage/main/shared/layer_02_target_context_mapping.csv',
    'target_layer2_context_mapping;target_layer2_context_mapping_v1;equity_business_context;layer_03_plus_target_study',
    'sync_artifact',
    'Reviewed mapping pattern for targets that need one or more business/theme Layer 2 context rows instead of implicit holdings-derived context. AAOI to AIQ/XLK/SMH/XLC is the first accepted example.'
  ),
  (
    'term_TL2CTX003',
    'term',
    'TARGET_CONTEXT_MULTI_ROW_BY_TARGET',
    'text',
    'target_context_multi_row_by_target',
    'trading-storage/main/shared/layer_02_target_context_mapping.csv',
    'target_layer2_context_mapping;target_context_business_mapping;target_layer2_context_agent_review',
    'sync_artifact',
    'The target context mapping CSV is row-per-target-context. target_symbol is not unique, and consumers must preserve all reviewed context rows for a selected target.'
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
