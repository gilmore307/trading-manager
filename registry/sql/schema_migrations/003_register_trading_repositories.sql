-- Register trading component repositories.
-- Target engine: PostgreSQL.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, note)
VALUES
  ('rep_DR482U4M', 'repo', 'TRADING_MANAGER_REPO', 'text', 'trading-manager', '/root/projects/trading-manager', 'docs/01_context.md#component-repositories', 'canonical repository entry for the trading manager control-plane component; remote: https://github.com/gilmore307/trading-manager.git'),
  ('rep_QFYSFJG9', 'repo', 'TRADING_DATA_REPO', 'text', 'trading-data', '/root/projects/trading-data', 'docs/01_context.md#component-repositories', 'canonical repository entry for the trading data upstream component; remote: https://github.com/gilmore307/trading-data.git'),
  ('rep_KE3K0EGP', 'repo', 'TRADING_STORAGE_REPO', 'text', 'trading-storage', '/root/projects/trading-storage', 'docs/01_context.md#component-repositories', 'canonical repository entry for the trading shared persistence contract component; remote: https://github.com/gilmore307/trading-storage.git'),
  ('rep_FM2IMQZA', 'repo', 'TRADING_STRATEGY_REPO', 'text', 'trading-strategy', '/root/projects/trading-strategy', 'docs/01_context.md#component-repositories', 'canonical repository entry for the trading strategy research/backtest component; remote: https://github.com/gilmore307/trading-strategy.git'),
  ('rep_LDEBL6IJ', 'repo', 'TRADING_MODEL_REPO', 'text', 'trading-model', '/root/projects/trading-model', 'docs/01_context.md#component-repositories', 'canonical repository entry for the trading offline model research component; remote: https://github.com/gilmore307/trading-model.git'),
  ('rep_CNPLR48M', 'repo', 'TRADING_EXECUTION_REPO', 'text', 'trading-execution', '/root/projects/trading-execution', 'docs/01_context.md#component-repositories', 'canonical repository entry for the trading execution runtime component; remote: https://github.com/gilmore307/trading-execution.git'),
  ('rep_PONBF8ZN', 'repo', 'TRADING_DASHBOARD_REPO', 'text', 'trading-dashboard', '/root/projects/trading-dashboard', 'docs/01_context.md#component-repositories', 'canonical repository entry for the trading dashboard/UI component; remote: https://github.com/gilmore307/trading-dashboard.git')
ON CONFLICT (id) DO UPDATE SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  note = EXCLUDED.note;

UPDATE trading_registry
SET
  applies_to = 'docs/01_context.md#component-repositories',
  note = 'canonical repository entry for the trading-main project, including its repository root path; remote: https://github.com/gilmore307/trading-main.git'
WHERE id = 'rep_H6S3V8LA';
