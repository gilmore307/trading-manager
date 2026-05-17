-- Replace remaining execution docs references after the shared docs numbering cleanup.

UPDATE trading_registry
SET
  path = replace(path, 'trading-execution/docs/09_realtime_data.md', 'trading-execution/docs/06_realtime_data.md'),
  payload = replace(payload, 'trading-execution/docs/09_realtime_data.md', 'trading-execution/docs/06_realtime_data.md'),
  applies_to = replace(applies_to, 'trading-execution/docs/09_realtime_data.md', 'trading-execution/docs/06_realtime_data.md'),
  note = replace(note, 'trading-execution/docs/09_realtime_data.md', 'trading-execution/docs/06_realtime_data.md')
WHERE path LIKE '%trading-execution/docs/09_realtime_data.md%'
   OR payload LIKE '%trading-execution/docs/09_realtime_data.md%'
   OR applies_to LIKE '%trading-execution/docs/09_realtime_data.md%'
   OR note LIKE '%trading-execution/docs/09_realtime_data.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-execution/docs/07_trade_risk_cap.md', 'trading-execution/docs/04_trade_risk_cap.md'),
  payload = replace(payload, 'trading-execution/docs/07_trade_risk_cap.md', 'trading-execution/docs/04_trade_risk_cap.md'),
  applies_to = replace(applies_to, 'trading-execution/docs/07_trade_risk_cap.md', 'trading-execution/docs/04_trade_risk_cap.md'),
  note = replace(note, 'trading-execution/docs/07_trade_risk_cap.md', 'trading-execution/docs/04_trade_risk_cap.md')
WHERE path LIKE '%trading-execution/docs/07_trade_risk_cap.md%'
   OR payload LIKE '%trading-execution/docs/07_trade_risk_cap.md%'
   OR applies_to LIKE '%trading-execution/docs/07_trade_risk_cap.md%'
   OR note LIKE '%trading-execution/docs/07_trade_risk_cap.md%';
