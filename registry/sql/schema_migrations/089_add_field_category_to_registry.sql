-- Add one exclusive semantic category for every registered field row.

ALTER TABLE trading_registry
ADD COLUMN IF NOT EXISTS field_category TEXT;

ALTER TABLE trading_registry
DROP CONSTRAINT IF EXISTS trading_registry_field_category_value_check;

ALTER TABLE trading_registry
DROP CONSTRAINT IF EXISTS trading_registry_field_category_required_check;

UPDATE trading_registry
SET field_category = CASE
  WHEN key LIKE 'SOURCE_SECRET_%' THEN 'secret'
  WHEN payload IN ('first_seen_in_window') OR note ILIKE '%boolean%' THEN 'boolean'
  WHEN payload IN ('task_goal', 'task_scope', 'constraints', 'expected_output', 'test_expectation', 'credential_config_id')
    OR payload LIKE '%policy%'
    OR payload LIKE '%semantics%'
    OR payload LIKE '%behavior%'
    OR payload LIKE '%caveats%'
    OR payload LIKE '%parameters%'
    THEN 'execution_contract'
  WHEN payload IN ('allowed_paths', 'blocked_paths', 'changed_files', 'command_list', 'reviewed_commands', 'reviewed_files', 'test_commands', 'issue_list', 'dictionary_issue_list', 'memory_route_issue_list', 'split_issue_list', 'blocked_task_list', 'follow_up_task_list', 'pending_acceptance_list', 'pending_dispatch_list', 'temporary_new_names', 'impacted_universe', 'locations', 'organizations', 'persons', 'themes', 'style_tags', 'exposed_etfs', 'outputs', 'runs', 'row_counts', 'contracts')
    THEN 'collection'
  WHEN payload LIKE '%context%'
    OR payload IN ('params', 'derived', 'greeks', 'iv', 'quote', 'triggered_indicators', 'statistics', 'standard_context', 'triggering_trade', 'source_refs')
    THEN 'nested_object'
  WHEN payload IN ('status', 'analysis_status', 'dedup_status', 'task_lifecycle_state', 'review_readiness', 'test_status', 'maintenance_status', 'docs_status', 'acceptance_outcome', 'iv_error')
    OR key LIKE '%_STATUS'
    THEN 'state'
  WHEN payload IN ('timeframe', 'bar_grain', 'data_kind', 'bundle', 'metric', 'asset_class', 'sector', 'right', 'source_type', 'event_type', 'impact_scope', 'universe_type', 'exposure_type', 'language', 'source_country', 'importance', 'kind', 'category', 'abnormal_activity_type')
    OR payload LIKE '%_type'
    OR payload LIKE '%_category'
    OR payload LIKE '%_scope'
    OR payload LIKE '%_tags'
    THEN 'classification'
  WHEN payload IN ('symbol', 'ticker', 'etf_ticker', 'holding_ticker', 'underlying', 'contract_symbol', 'cusip', 'sedol', 'security_id')
    THEN 'identity'
  WHEN payload IN ('id', 'task_id', 'run_id', 'event_id', 'report_id', 'standard_id', 'article_id', 'canonical_event_id', 'workflow_identity', 'task_identity')
    OR payload LIKE '%_id'
    THEN 'identity'
  WHEN payload IN ('timestamp_et', 'interval_start_et', 'created_at', 'updated_at', 'created_at_et', 'updated_at_et', 'check_time', 'completed_at', 'started_at', 'as_of_date', 'analysis_generated_at_et', 'effective_time_et', 'event_time_et', 'seen_at_utc', 'effective_until', 'release_time', 'standard_generated_at_et', 'expiration', 'snapshot_time_et', 'available_time_et', 'trade_timestamp_et', 'event_time_et')
    OR payload LIKE '%_timestamp%'
    OR payload LIKE '%_time_et'
    OR payload LIKE '%_at_et'
    OR payload LIKE '%_at_utc'
    OR payload LIKE '%_date'
    THEN 'temporal'
  WHEN payload LIKE '%url%'
    OR payload LIKE '%path%'
    OR payload LIKE '%file%'
    OR payload LIKE '%dir%'
    OR payload LIKE '%root%'
    OR payload LIKE '%reference%'
    OR payload LIKE '%ref'
    OR payload LIKE '%refs'
    THEN 'reference'
  WHEN payload LIKE '%count%'
    OR payload LIKE '%volume%'
    OR payload LIKE '%size%'
    OR payload LIKE '%shares%'
    THEN 'quantity'
  WHEN payload IN ('open', 'high', 'low', 'close', 'vwap', 'bid', 'ask', 'mid', 'spread', 'avg_ask', 'avg_bid', 'avg_mid', 'avg_spread', 'last_ask', 'last_bid', 'last_mid', 'trade_open', 'trade_high', 'trade_low', 'trade_close', 'trade_vwap', 'trade_price', 'underlying_price', 'market_value', 'notional', 'window_notional', 'actual', 'te_forecast', 'previous', 'consensus', 'revised', 'value', 'weight', 'delta', 'epsilon', 'lambda', 'rho', 'theta', 'vega', 'implied_vol', 'tone')
    OR payload LIKE '%score%'
    OR payload LIKE '%zscore%'
    OR payload LIKE '%ratio%'
    OR payload LIKE '%percentile%'
    OR payload LIKE '%rank%'
    OR payload LIKE '%pct%'
    OR payload LIKE '%price%'
    OR payload LIKE '%spread%'
    OR payload LIKE '%vwap%'
    THEN 'numeric_measure'
  ELSE 'text'
END
WHERE kind = 'field';

UPDATE trading_registry
SET field_category = NULL
WHERE kind <> 'field';

INSERT INTO trading_registry (
  id,
  kind,
  key,
  payload_format,
  payload,
  path,
  applies_to,
  field_category,
  artifact_sync_policy,
  note
)
VALUES (
  'fld_R4M8Q2FIELDCLASS',
  'field',
  'REGISTRY_ITEM_FIELD_CATEGORY',
  'field_name',
  'field_category',
  NULL,
  'trading_registry',
  'classification',
  'sync_artifact',
  'canonical column name for the exclusive semantic category assigned to field rows'
)
ON CONFLICT (key) DO UPDATE SET
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  field_category = EXCLUDED.field_category,
  artifact_sync_policy = EXCLUDED.artifact_sync_policy,
  note = EXCLUDED.note;

ALTER TABLE trading_registry
ADD CONSTRAINT trading_registry_field_category_value_check
CHECK (
  field_category IS NULL OR field_category IN (
    'boolean',
    'classification',
    'collection',
    'execution_contract',
    'identity',
    'nested_object',
    'numeric_measure',
    'quantity',
    'reference',
    'secret',
    'state',
    'temporal',
    'text'
  )
);

ALTER TABLE trading_registry
ADD CONSTRAINT trading_registry_field_category_required_check
CHECK (
  (kind = 'field' AND field_category IS NOT NULL AND BTRIM(field_category) <> '')
  OR
  (kind <> 'field' AND field_category IS NULL)
);

CREATE INDEX IF NOT EXISTS idx_trading_registry_field_category
ON trading_registry(field_category)
WHERE kind = 'field';

CREATE OR REPLACE FUNCTION set_trading_registry_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  IF ROW(NEW.kind, NEW.key, NEW.payload_format, NEW.payload, NEW.path, NEW.applies_to, NEW.field_category, NEW.artifact_sync_policy, NEW.note)
     IS DISTINCT FROM
     ROW(OLD.kind, OLD.key, OLD.payload_format, OLD.payload, OLD.path, OLD.applies_to, OLD.field_category, OLD.artifact_sync_policy, OLD.note) THEN
    NEW.updated_at = NOW();
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
