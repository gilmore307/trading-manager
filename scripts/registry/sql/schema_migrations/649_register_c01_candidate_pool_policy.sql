-- Register C01 candidate pool maintenance policy.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
  'cfg_EXECRTC004',
  'config',
  'C01_CANDIDATE_POOL_POLICY',
  'text',
  'remaining_strong_sector_targets;recent_high_trading_volume_targets;recent_news_or_earnings_catalyst_targets;exclude_targets_from_filled_sectors',
  'trading-execution/docs/50_runtime_components.md;trading-execution/src/trading_execution/runtime/decisions.py',
  'component_01_intake;execution_intake_snapshot;watch_targets;blocked_targets;component_02_entry',
  'sync_artifact',
  'C01 maintains the equity/options watch target pool as remaining strong-sector targets plus recent high-volume targets plus recent news or earnings catalyst targets. Targets from sectors whose target opportunity mix is already filled are excluded before C02 entry evaluation.'
)
ON CONFLICT (id) DO UPDATE SET
    kind = EXCLUDED.kind,
    key = EXCLUDED.key,
    payload_format = EXCLUDED.payload_format,
    payload = EXCLUDED.payload,
    path = EXCLUDED.path,
    applies_to = EXCLUDED.applies_to,
    artifact_sync_policy = EXCLUDED.artifact_sync_policy,
    note = EXCLUDED.note,
    updated_at = CURRENT_TIMESTAMP;

UPDATE trading_registry
SET note = 'Execution runtime contract emitted by C01 Intake for account balance state, current holdings, dynamic remaining sector opportunity mix, watch targets from accepted candidate sources, and account-sleeve candidate filtering. It excludes targets from sectors whose opportunity mix is already filled and does not allocate risk budget, size positions, decide entries, manage exits, construct orders, or mutate broker/account state.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'art_EXECRTC003';

UPDATE trading_registry
SET note = 'Policy stating live trading and Replay use the same execution component graph and decision contracts, with only adapter profiles swapped. C01 Intake reads account state, current holdings, dynamic remaining sector opportunity mix, and watch targets from accepted candidate sources only; it does not allocate risk budget or manage positions. trading-evaluation owns orchestration and judgment, not duplicated trading decisions. Runtime decisions must keep crypto and equity/options in independent account sleeves without cross-account collateral, buying-power, position, or risk-budget netting.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'cfg_EXECRTC001';
