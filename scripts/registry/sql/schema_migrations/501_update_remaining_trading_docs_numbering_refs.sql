-- Replace remaining registry references to pre-rule docs numbering across payload-like columns.
-- Active docs now follow the shared rule: 00-69 current spine, 80-89 ledgers, 90-99 appendices only, no 100+ active docs.

UPDATE trading_registry
SET
  path = replace(path, 'trading-dashboard/docs/09_dashboard_read_models.md', 'trading-dashboard/docs/06_dashboard_read_models.md'),
  payload = replace(payload, 'trading-dashboard/docs/09_dashboard_read_models.md', 'trading-dashboard/docs/06_dashboard_read_models.md'),
  applies_to = replace(applies_to, 'trading-dashboard/docs/09_dashboard_read_models.md', 'trading-dashboard/docs/06_dashboard_read_models.md'),
  note = replace(note, 'trading-dashboard/docs/09_dashboard_read_models.md', 'trading-dashboard/docs/06_dashboard_read_models.md')
WHERE path LIKE '%trading-dashboard/docs/09_dashboard_read_models.md%'
   OR payload LIKE '%trading-dashboard/docs/09_dashboard_read_models.md%'
   OR applies_to LIKE '%trading-dashboard/docs/09_dashboard_read_models.md%'
   OR note LIKE '%trading-dashboard/docs/09_dashboard_read_models.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-dashboard/docs/05_decision.md', 'trading-dashboard/docs/81_decision.md'),
  payload = replace(payload, 'trading-dashboard/docs/05_decision.md', 'trading-dashboard/docs/81_decision.md'),
  applies_to = replace(applies_to, 'trading-dashboard/docs/05_decision.md', 'trading-dashboard/docs/81_decision.md'),
  note = replace(note, 'trading-dashboard/docs/05_decision.md', 'trading-dashboard/docs/81_decision.md')
WHERE path LIKE '%trading-dashboard/docs/05_decision.md%'
   OR payload LIKE '%trading-dashboard/docs/05_decision.md%'
   OR applies_to LIKE '%trading-dashboard/docs/05_decision.md%'
   OR note LIKE '%trading-dashboard/docs/05_decision.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-execution/docs/10_broker_interfaces.md', 'trading-execution/docs/07_broker_interfaces.md'),
  payload = replace(payload, 'trading-execution/docs/10_broker_interfaces.md', 'trading-execution/docs/07_broker_interfaces.md'),
  applies_to = replace(applies_to, 'trading-execution/docs/10_broker_interfaces.md', 'trading-execution/docs/07_broker_interfaces.md'),
  note = replace(note, 'trading-execution/docs/10_broker_interfaces.md', 'trading-execution/docs/07_broker_interfaces.md')
WHERE path LIKE '%trading-execution/docs/10_broker_interfaces.md%'
   OR payload LIKE '%trading-execution/docs/10_broker_interfaces.md%'
   OR applies_to LIKE '%trading-execution/docs/10_broker_interfaces.md%'
   OR note LIKE '%trading-execution/docs/10_broker_interfaces.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-execution/docs/05_decision.md', 'trading-execution/docs/81_decision.md'),
  payload = replace(payload, 'trading-execution/docs/05_decision.md', 'trading-execution/docs/81_decision.md'),
  applies_to = replace(applies_to, 'trading-execution/docs/05_decision.md', 'trading-execution/docs/81_decision.md'),
  note = replace(note, 'trading-execution/docs/05_decision.md', 'trading-execution/docs/81_decision.md')
WHERE path LIKE '%trading-execution/docs/05_decision.md%'
   OR payload LIKE '%trading-execution/docs/05_decision.md%'
   OR applies_to LIKE '%trading-execution/docs/05_decision.md%'
   OR note LIKE '%trading-execution/docs/05_decision.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-model/docs/92_vector_taxonomy.md', 'trading-model/docs/13_vector_taxonomy.md'),
  payload = replace(payload, 'trading-model/docs/92_vector_taxonomy.md', 'trading-model/docs/13_vector_taxonomy.md'),
  applies_to = replace(applies_to, 'trading-model/docs/92_vector_taxonomy.md', 'trading-model/docs/13_vector_taxonomy.md'),
  note = replace(note, 'trading-model/docs/92_vector_taxonomy.md', 'trading-model/docs/13_vector_taxonomy.md')
WHERE path LIKE '%trading-model/docs/92_vector_taxonomy.md%'
   OR payload LIKE '%trading-model/docs/92_vector_taxonomy.md%'
   OR applies_to LIKE '%trading-model/docs/92_vector_taxonomy.md%'
   OR note LIKE '%trading-model/docs/92_vector_taxonomy.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-model/docs/97_historical_dataset_scope.md', 'trading-model/docs/18_historical_dataset_scope.md'),
  payload = replace(payload, 'trading-model/docs/97_historical_dataset_scope.md', 'trading-model/docs/18_historical_dataset_scope.md'),
  applies_to = replace(applies_to, 'trading-model/docs/97_historical_dataset_scope.md', 'trading-model/docs/18_historical_dataset_scope.md'),
  note = replace(note, 'trading-model/docs/97_historical_dataset_scope.md', 'trading-model/docs/18_historical_dataset_scope.md')
WHERE path LIKE '%trading-model/docs/97_historical_dataset_scope.md%'
   OR payload LIKE '%trading-model/docs/97_historical_dataset_scope.md%'
   OR applies_to LIKE '%trading-model/docs/97_historical_dataset_scope.md%'
   OR note LIKE '%trading-model/docs/97_historical_dataset_scope.md%';
