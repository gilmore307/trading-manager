-- Align active registry doc references with the first-principles docs trunk/module numbering rule.

UPDATE trading_registry
SET
  path = replace(path, 'trading-dashboard/docs/02_workflow.md', 'trading-dashboard/docs/02_architecture.md'),
  payload = replace(payload, 'trading-dashboard/docs/02_workflow.md', 'trading-dashboard/docs/02_architecture.md'),
  applies_to = replace(applies_to, 'trading-dashboard/docs/02_workflow.md', 'trading-dashboard/docs/02_architecture.md'),
  note = replace(note, 'trading-dashboard/docs/02_workflow.md', 'trading-dashboard/docs/02_architecture.md')
WHERE path LIKE '%trading-dashboard/docs/02_workflow.md%' OR payload LIKE '%trading-dashboard/docs/02_workflow.md%' OR applies_to LIKE '%trading-dashboard/docs/02_workflow.md%' OR note LIKE '%trading-dashboard/docs/02_workflow.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-dashboard/docs/02_workflow.md', '/root/projects/trading-dashboard/docs/02_architecture.md'),
  payload = replace(payload, '/root/projects/trading-dashboard/docs/02_workflow.md', '/root/projects/trading-dashboard/docs/02_architecture.md'),
  applies_to = replace(applies_to, '/root/projects/trading-dashboard/docs/02_workflow.md', '/root/projects/trading-dashboard/docs/02_architecture.md'),
  note = replace(note, '/root/projects/trading-dashboard/docs/02_workflow.md', '/root/projects/trading-dashboard/docs/02_architecture.md')
WHERE path LIKE '%/root/projects/trading-dashboard/docs/02_workflow.md%' OR payload LIKE '%/root/projects/trading-dashboard/docs/02_workflow.md%' OR applies_to LIKE '%/root/projects/trading-dashboard/docs/02_workflow.md%' OR note LIKE '%/root/projects/trading-dashboard/docs/02_workflow.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-dashboard/docs/02_workflow.md', 'file:/root/projects/trading-dashboard/docs/02_architecture.md'),
  payload = replace(payload, 'file:/root/projects/trading-dashboard/docs/02_workflow.md', 'file:/root/projects/trading-dashboard/docs/02_architecture.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-dashboard/docs/02_workflow.md', 'file:/root/projects/trading-dashboard/docs/02_architecture.md'),
  note = replace(note, 'file:/root/projects/trading-dashboard/docs/02_workflow.md', 'file:/root/projects/trading-dashboard/docs/02_architecture.md')
WHERE path LIKE '%file:/root/projects/trading-dashboard/docs/02_workflow.md%' OR payload LIKE '%file:/root/projects/trading-dashboard/docs/02_workflow.md%' OR applies_to LIKE '%file:/root/projects/trading-dashboard/docs/02_workflow.md%' OR note LIKE '%file:/root/projects/trading-dashboard/docs/02_workflow.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-dashboard/docs/03_acceptance.md', 'trading-dashboard/docs/03_contracts.md'),
  payload = replace(payload, 'trading-dashboard/docs/03_acceptance.md', 'trading-dashboard/docs/03_contracts.md'),
  applies_to = replace(applies_to, 'trading-dashboard/docs/03_acceptance.md', 'trading-dashboard/docs/03_contracts.md'),
  note = replace(note, 'trading-dashboard/docs/03_acceptance.md', 'trading-dashboard/docs/03_contracts.md')
WHERE path LIKE '%trading-dashboard/docs/03_acceptance.md%' OR payload LIKE '%trading-dashboard/docs/03_acceptance.md%' OR applies_to LIKE '%trading-dashboard/docs/03_acceptance.md%' OR note LIKE '%trading-dashboard/docs/03_acceptance.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-dashboard/docs/03_acceptance.md', '/root/projects/trading-dashboard/docs/03_contracts.md'),
  payload = replace(payload, '/root/projects/trading-dashboard/docs/03_acceptance.md', '/root/projects/trading-dashboard/docs/03_contracts.md'),
  applies_to = replace(applies_to, '/root/projects/trading-dashboard/docs/03_acceptance.md', '/root/projects/trading-dashboard/docs/03_contracts.md'),
  note = replace(note, '/root/projects/trading-dashboard/docs/03_acceptance.md', '/root/projects/trading-dashboard/docs/03_contracts.md')
WHERE path LIKE '%/root/projects/trading-dashboard/docs/03_acceptance.md%' OR payload LIKE '%/root/projects/trading-dashboard/docs/03_acceptance.md%' OR applies_to LIKE '%/root/projects/trading-dashboard/docs/03_acceptance.md%' OR note LIKE '%/root/projects/trading-dashboard/docs/03_acceptance.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-dashboard/docs/03_acceptance.md', 'file:/root/projects/trading-dashboard/docs/03_contracts.md'),
  payload = replace(payload, 'file:/root/projects/trading-dashboard/docs/03_acceptance.md', 'file:/root/projects/trading-dashboard/docs/03_contracts.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-dashboard/docs/03_acceptance.md', 'file:/root/projects/trading-dashboard/docs/03_contracts.md'),
  note = replace(note, 'file:/root/projects/trading-dashboard/docs/03_acceptance.md', 'file:/root/projects/trading-dashboard/docs/03_contracts.md')
WHERE path LIKE '%file:/root/projects/trading-dashboard/docs/03_acceptance.md%' OR payload LIKE '%file:/root/projects/trading-dashboard/docs/03_acceptance.md%' OR applies_to LIKE '%file:/root/projects/trading-dashboard/docs/03_acceptance.md%' OR note LIKE '%file:/root/projects/trading-dashboard/docs/03_acceptance.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-dashboard/docs/80_task.md', 'trading-dashboard/docs/04_task.md'),
  payload = replace(payload, 'trading-dashboard/docs/80_task.md', 'trading-dashboard/docs/04_task.md'),
  applies_to = replace(applies_to, 'trading-dashboard/docs/80_task.md', 'trading-dashboard/docs/04_task.md'),
  note = replace(note, 'trading-dashboard/docs/80_task.md', 'trading-dashboard/docs/04_task.md')
WHERE path LIKE '%trading-dashboard/docs/80_task.md%' OR payload LIKE '%trading-dashboard/docs/80_task.md%' OR applies_to LIKE '%trading-dashboard/docs/80_task.md%' OR note LIKE '%trading-dashboard/docs/80_task.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-dashboard/docs/80_task.md', '/root/projects/trading-dashboard/docs/04_task.md'),
  payload = replace(payload, '/root/projects/trading-dashboard/docs/80_task.md', '/root/projects/trading-dashboard/docs/04_task.md'),
  applies_to = replace(applies_to, '/root/projects/trading-dashboard/docs/80_task.md', '/root/projects/trading-dashboard/docs/04_task.md'),
  note = replace(note, '/root/projects/trading-dashboard/docs/80_task.md', '/root/projects/trading-dashboard/docs/04_task.md')
WHERE path LIKE '%/root/projects/trading-dashboard/docs/80_task.md%' OR payload LIKE '%/root/projects/trading-dashboard/docs/80_task.md%' OR applies_to LIKE '%/root/projects/trading-dashboard/docs/80_task.md%' OR note LIKE '%/root/projects/trading-dashboard/docs/80_task.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-dashboard/docs/80_task.md', 'file:/root/projects/trading-dashboard/docs/04_task.md'),
  payload = replace(payload, 'file:/root/projects/trading-dashboard/docs/80_task.md', 'file:/root/projects/trading-dashboard/docs/04_task.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-dashboard/docs/80_task.md', 'file:/root/projects/trading-dashboard/docs/04_task.md'),
  note = replace(note, 'file:/root/projects/trading-dashboard/docs/80_task.md', 'file:/root/projects/trading-dashboard/docs/04_task.md')
WHERE path LIKE '%file:/root/projects/trading-dashboard/docs/80_task.md%' OR payload LIKE '%file:/root/projects/trading-dashboard/docs/80_task.md%' OR applies_to LIKE '%file:/root/projects/trading-dashboard/docs/80_task.md%' OR note LIKE '%file:/root/projects/trading-dashboard/docs/80_task.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-dashboard/docs/81_decision.md', 'trading-dashboard/docs/05_decision.md'),
  payload = replace(payload, 'trading-dashboard/docs/81_decision.md', 'trading-dashboard/docs/05_decision.md'),
  applies_to = replace(applies_to, 'trading-dashboard/docs/81_decision.md', 'trading-dashboard/docs/05_decision.md'),
  note = replace(note, 'trading-dashboard/docs/81_decision.md', 'trading-dashboard/docs/05_decision.md')
WHERE path LIKE '%trading-dashboard/docs/81_decision.md%' OR payload LIKE '%trading-dashboard/docs/81_decision.md%' OR applies_to LIKE '%trading-dashboard/docs/81_decision.md%' OR note LIKE '%trading-dashboard/docs/81_decision.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-dashboard/docs/81_decision.md', '/root/projects/trading-dashboard/docs/05_decision.md'),
  payload = replace(payload, '/root/projects/trading-dashboard/docs/81_decision.md', '/root/projects/trading-dashboard/docs/05_decision.md'),
  applies_to = replace(applies_to, '/root/projects/trading-dashboard/docs/81_decision.md', '/root/projects/trading-dashboard/docs/05_decision.md'),
  note = replace(note, '/root/projects/trading-dashboard/docs/81_decision.md', '/root/projects/trading-dashboard/docs/05_decision.md')
WHERE path LIKE '%/root/projects/trading-dashboard/docs/81_decision.md%' OR payload LIKE '%/root/projects/trading-dashboard/docs/81_decision.md%' OR applies_to LIKE '%/root/projects/trading-dashboard/docs/81_decision.md%' OR note LIKE '%/root/projects/trading-dashboard/docs/81_decision.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-dashboard/docs/81_decision.md', 'file:/root/projects/trading-dashboard/docs/05_decision.md'),
  payload = replace(payload, 'file:/root/projects/trading-dashboard/docs/81_decision.md', 'file:/root/projects/trading-dashboard/docs/05_decision.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-dashboard/docs/81_decision.md', 'file:/root/projects/trading-dashboard/docs/05_decision.md'),
  note = replace(note, 'file:/root/projects/trading-dashboard/docs/81_decision.md', 'file:/root/projects/trading-dashboard/docs/05_decision.md')
WHERE path LIKE '%file:/root/projects/trading-dashboard/docs/81_decision.md%' OR payload LIKE '%file:/root/projects/trading-dashboard/docs/81_decision.md%' OR applies_to LIKE '%file:/root/projects/trading-dashboard/docs/81_decision.md%' OR note LIKE '%file:/root/projects/trading-dashboard/docs/81_decision.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-dashboard/docs/82_memory.md', 'trading-dashboard/docs/06_memory.md'),
  payload = replace(payload, 'trading-dashboard/docs/82_memory.md', 'trading-dashboard/docs/06_memory.md'),
  applies_to = replace(applies_to, 'trading-dashboard/docs/82_memory.md', 'trading-dashboard/docs/06_memory.md'),
  note = replace(note, 'trading-dashboard/docs/82_memory.md', 'trading-dashboard/docs/06_memory.md')
WHERE path LIKE '%trading-dashboard/docs/82_memory.md%' OR payload LIKE '%trading-dashboard/docs/82_memory.md%' OR applies_to LIKE '%trading-dashboard/docs/82_memory.md%' OR note LIKE '%trading-dashboard/docs/82_memory.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-dashboard/docs/82_memory.md', '/root/projects/trading-dashboard/docs/06_memory.md'),
  payload = replace(payload, '/root/projects/trading-dashboard/docs/82_memory.md', '/root/projects/trading-dashboard/docs/06_memory.md'),
  applies_to = replace(applies_to, '/root/projects/trading-dashboard/docs/82_memory.md', '/root/projects/trading-dashboard/docs/06_memory.md'),
  note = replace(note, '/root/projects/trading-dashboard/docs/82_memory.md', '/root/projects/trading-dashboard/docs/06_memory.md')
WHERE path LIKE '%/root/projects/trading-dashboard/docs/82_memory.md%' OR payload LIKE '%/root/projects/trading-dashboard/docs/82_memory.md%' OR applies_to LIKE '%/root/projects/trading-dashboard/docs/82_memory.md%' OR note LIKE '%/root/projects/trading-dashboard/docs/82_memory.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-dashboard/docs/82_memory.md', 'file:/root/projects/trading-dashboard/docs/06_memory.md'),
  payload = replace(payload, 'file:/root/projects/trading-dashboard/docs/82_memory.md', 'file:/root/projects/trading-dashboard/docs/06_memory.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-dashboard/docs/82_memory.md', 'file:/root/projects/trading-dashboard/docs/06_memory.md'),
  note = replace(note, 'file:/root/projects/trading-dashboard/docs/82_memory.md', 'file:/root/projects/trading-dashboard/docs/06_memory.md')
WHERE path LIKE '%file:/root/projects/trading-dashboard/docs/82_memory.md%' OR payload LIKE '%file:/root/projects/trading-dashboard/docs/82_memory.md%' OR applies_to LIKE '%file:/root/projects/trading-dashboard/docs/82_memory.md%' OR note LIKE '%file:/root/projects/trading-dashboard/docs/82_memory.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-dashboard/docs/04_dashboard_closeout.md', 'trading-dashboard/docs/10_dashboard_acceptance.md'),
  payload = replace(payload, 'trading-dashboard/docs/04_dashboard_closeout.md', 'trading-dashboard/docs/10_dashboard_acceptance.md'),
  applies_to = replace(applies_to, 'trading-dashboard/docs/04_dashboard_closeout.md', 'trading-dashboard/docs/10_dashboard_acceptance.md'),
  note = replace(note, 'trading-dashboard/docs/04_dashboard_closeout.md', 'trading-dashboard/docs/10_dashboard_acceptance.md')
WHERE path LIKE '%trading-dashboard/docs/04_dashboard_closeout.md%' OR payload LIKE '%trading-dashboard/docs/04_dashboard_closeout.md%' OR applies_to LIKE '%trading-dashboard/docs/04_dashboard_closeout.md%' OR note LIKE '%trading-dashboard/docs/04_dashboard_closeout.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-dashboard/docs/04_dashboard_closeout.md', '/root/projects/trading-dashboard/docs/10_dashboard_acceptance.md'),
  payload = replace(payload, '/root/projects/trading-dashboard/docs/04_dashboard_closeout.md', '/root/projects/trading-dashboard/docs/10_dashboard_acceptance.md'),
  applies_to = replace(applies_to, '/root/projects/trading-dashboard/docs/04_dashboard_closeout.md', '/root/projects/trading-dashboard/docs/10_dashboard_acceptance.md'),
  note = replace(note, '/root/projects/trading-dashboard/docs/04_dashboard_closeout.md', '/root/projects/trading-dashboard/docs/10_dashboard_acceptance.md')
WHERE path LIKE '%/root/projects/trading-dashboard/docs/04_dashboard_closeout.md%' OR payload LIKE '%/root/projects/trading-dashboard/docs/04_dashboard_closeout.md%' OR applies_to LIKE '%/root/projects/trading-dashboard/docs/04_dashboard_closeout.md%' OR note LIKE '%/root/projects/trading-dashboard/docs/04_dashboard_closeout.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-dashboard/docs/04_dashboard_closeout.md', 'file:/root/projects/trading-dashboard/docs/10_dashboard_acceptance.md'),
  payload = replace(payload, 'file:/root/projects/trading-dashboard/docs/04_dashboard_closeout.md', 'file:/root/projects/trading-dashboard/docs/10_dashboard_acceptance.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-dashboard/docs/04_dashboard_closeout.md', 'file:/root/projects/trading-dashboard/docs/10_dashboard_acceptance.md'),
  note = replace(note, 'file:/root/projects/trading-dashboard/docs/04_dashboard_closeout.md', 'file:/root/projects/trading-dashboard/docs/10_dashboard_acceptance.md')
WHERE path LIKE '%file:/root/projects/trading-dashboard/docs/04_dashboard_closeout.md%' OR payload LIKE '%file:/root/projects/trading-dashboard/docs/04_dashboard_closeout.md%' OR applies_to LIKE '%file:/root/projects/trading-dashboard/docs/04_dashboard_closeout.md%' OR note LIKE '%file:/root/projects/trading-dashboard/docs/04_dashboard_closeout.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-dashboard/docs/05_information_architecture.md', 'trading-dashboard/docs/20_information_architecture.md'),
  payload = replace(payload, 'trading-dashboard/docs/05_information_architecture.md', 'trading-dashboard/docs/20_information_architecture.md'),
  applies_to = replace(applies_to, 'trading-dashboard/docs/05_information_architecture.md', 'trading-dashboard/docs/20_information_architecture.md'),
  note = replace(note, 'trading-dashboard/docs/05_information_architecture.md', 'trading-dashboard/docs/20_information_architecture.md')
WHERE path LIKE '%trading-dashboard/docs/05_information_architecture.md%' OR payload LIKE '%trading-dashboard/docs/05_information_architecture.md%' OR applies_to LIKE '%trading-dashboard/docs/05_information_architecture.md%' OR note LIKE '%trading-dashboard/docs/05_information_architecture.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-dashboard/docs/05_information_architecture.md', '/root/projects/trading-dashboard/docs/20_information_architecture.md'),
  payload = replace(payload, '/root/projects/trading-dashboard/docs/05_information_architecture.md', '/root/projects/trading-dashboard/docs/20_information_architecture.md'),
  applies_to = replace(applies_to, '/root/projects/trading-dashboard/docs/05_information_architecture.md', '/root/projects/trading-dashboard/docs/20_information_architecture.md'),
  note = replace(note, '/root/projects/trading-dashboard/docs/05_information_architecture.md', '/root/projects/trading-dashboard/docs/20_information_architecture.md')
WHERE path LIKE '%/root/projects/trading-dashboard/docs/05_information_architecture.md%' OR payload LIKE '%/root/projects/trading-dashboard/docs/05_information_architecture.md%' OR applies_to LIKE '%/root/projects/trading-dashboard/docs/05_information_architecture.md%' OR note LIKE '%/root/projects/trading-dashboard/docs/05_information_architecture.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-dashboard/docs/05_information_architecture.md', 'file:/root/projects/trading-dashboard/docs/20_information_architecture.md'),
  payload = replace(payload, 'file:/root/projects/trading-dashboard/docs/05_information_architecture.md', 'file:/root/projects/trading-dashboard/docs/20_information_architecture.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-dashboard/docs/05_information_architecture.md', 'file:/root/projects/trading-dashboard/docs/20_information_architecture.md'),
  note = replace(note, 'file:/root/projects/trading-dashboard/docs/05_information_architecture.md', 'file:/root/projects/trading-dashboard/docs/20_information_architecture.md')
WHERE path LIKE '%file:/root/projects/trading-dashboard/docs/05_information_architecture.md%' OR payload LIKE '%file:/root/projects/trading-dashboard/docs/05_information_architecture.md%' OR applies_to LIKE '%file:/root/projects/trading-dashboard/docs/05_information_architecture.md%' OR note LIKE '%file:/root/projects/trading-dashboard/docs/05_information_architecture.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-dashboard/docs/06_dashboard_read_models.md', 'trading-dashboard/docs/30_dashboard_read_models.md'),
  payload = replace(payload, 'trading-dashboard/docs/06_dashboard_read_models.md', 'trading-dashboard/docs/30_dashboard_read_models.md'),
  applies_to = replace(applies_to, 'trading-dashboard/docs/06_dashboard_read_models.md', 'trading-dashboard/docs/30_dashboard_read_models.md'),
  note = replace(note, 'trading-dashboard/docs/06_dashboard_read_models.md', 'trading-dashboard/docs/30_dashboard_read_models.md')
WHERE path LIKE '%trading-dashboard/docs/06_dashboard_read_models.md%' OR payload LIKE '%trading-dashboard/docs/06_dashboard_read_models.md%' OR applies_to LIKE '%trading-dashboard/docs/06_dashboard_read_models.md%' OR note LIKE '%trading-dashboard/docs/06_dashboard_read_models.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-dashboard/docs/06_dashboard_read_models.md', '/root/projects/trading-dashboard/docs/30_dashboard_read_models.md'),
  payload = replace(payload, '/root/projects/trading-dashboard/docs/06_dashboard_read_models.md', '/root/projects/trading-dashboard/docs/30_dashboard_read_models.md'),
  applies_to = replace(applies_to, '/root/projects/trading-dashboard/docs/06_dashboard_read_models.md', '/root/projects/trading-dashboard/docs/30_dashboard_read_models.md'),
  note = replace(note, '/root/projects/trading-dashboard/docs/06_dashboard_read_models.md', '/root/projects/trading-dashboard/docs/30_dashboard_read_models.md')
WHERE path LIKE '%/root/projects/trading-dashboard/docs/06_dashboard_read_models.md%' OR payload LIKE '%/root/projects/trading-dashboard/docs/06_dashboard_read_models.md%' OR applies_to LIKE '%/root/projects/trading-dashboard/docs/06_dashboard_read_models.md%' OR note LIKE '%/root/projects/trading-dashboard/docs/06_dashboard_read_models.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-dashboard/docs/06_dashboard_read_models.md', 'file:/root/projects/trading-dashboard/docs/30_dashboard_read_models.md'),
  payload = replace(payload, 'file:/root/projects/trading-dashboard/docs/06_dashboard_read_models.md', 'file:/root/projects/trading-dashboard/docs/30_dashboard_read_models.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-dashboard/docs/06_dashboard_read_models.md', 'file:/root/projects/trading-dashboard/docs/30_dashboard_read_models.md'),
  note = replace(note, 'file:/root/projects/trading-dashboard/docs/06_dashboard_read_models.md', 'file:/root/projects/trading-dashboard/docs/30_dashboard_read_models.md')
WHERE path LIKE '%file:/root/projects/trading-dashboard/docs/06_dashboard_read_models.md%' OR payload LIKE '%file:/root/projects/trading-dashboard/docs/06_dashboard_read_models.md%' OR applies_to LIKE '%file:/root/projects/trading-dashboard/docs/06_dashboard_read_models.md%' OR note LIKE '%file:/root/projects/trading-dashboard/docs/06_dashboard_read_models.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-execution/docs/02_workflow.md', 'trading-execution/docs/02_architecture.md'),
  payload = replace(payload, 'trading-execution/docs/02_workflow.md', 'trading-execution/docs/02_architecture.md'),
  applies_to = replace(applies_to, 'trading-execution/docs/02_workflow.md', 'trading-execution/docs/02_architecture.md'),
  note = replace(note, 'trading-execution/docs/02_workflow.md', 'trading-execution/docs/02_architecture.md')
WHERE path LIKE '%trading-execution/docs/02_workflow.md%' OR payload LIKE '%trading-execution/docs/02_workflow.md%' OR applies_to LIKE '%trading-execution/docs/02_workflow.md%' OR note LIKE '%trading-execution/docs/02_workflow.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-execution/docs/02_workflow.md', '/root/projects/trading-execution/docs/02_architecture.md'),
  payload = replace(payload, '/root/projects/trading-execution/docs/02_workflow.md', '/root/projects/trading-execution/docs/02_architecture.md'),
  applies_to = replace(applies_to, '/root/projects/trading-execution/docs/02_workflow.md', '/root/projects/trading-execution/docs/02_architecture.md'),
  note = replace(note, '/root/projects/trading-execution/docs/02_workflow.md', '/root/projects/trading-execution/docs/02_architecture.md')
WHERE path LIKE '%/root/projects/trading-execution/docs/02_workflow.md%' OR payload LIKE '%/root/projects/trading-execution/docs/02_workflow.md%' OR applies_to LIKE '%/root/projects/trading-execution/docs/02_workflow.md%' OR note LIKE '%/root/projects/trading-execution/docs/02_workflow.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-execution/docs/02_workflow.md', 'file:/root/projects/trading-execution/docs/02_architecture.md'),
  payload = replace(payload, 'file:/root/projects/trading-execution/docs/02_workflow.md', 'file:/root/projects/trading-execution/docs/02_architecture.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-execution/docs/02_workflow.md', 'file:/root/projects/trading-execution/docs/02_architecture.md'),
  note = replace(note, 'file:/root/projects/trading-execution/docs/02_workflow.md', 'file:/root/projects/trading-execution/docs/02_architecture.md')
WHERE path LIKE '%file:/root/projects/trading-execution/docs/02_workflow.md%' OR payload LIKE '%file:/root/projects/trading-execution/docs/02_workflow.md%' OR applies_to LIKE '%file:/root/projects/trading-execution/docs/02_workflow.md%' OR note LIKE '%file:/root/projects/trading-execution/docs/02_workflow.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-execution/docs/03_acceptance.md', 'trading-execution/docs/03_contracts.md'),
  payload = replace(payload, 'trading-execution/docs/03_acceptance.md', 'trading-execution/docs/03_contracts.md'),
  applies_to = replace(applies_to, 'trading-execution/docs/03_acceptance.md', 'trading-execution/docs/03_contracts.md'),
  note = replace(note, 'trading-execution/docs/03_acceptance.md', 'trading-execution/docs/03_contracts.md')
WHERE path LIKE '%trading-execution/docs/03_acceptance.md%' OR payload LIKE '%trading-execution/docs/03_acceptance.md%' OR applies_to LIKE '%trading-execution/docs/03_acceptance.md%' OR note LIKE '%trading-execution/docs/03_acceptance.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-execution/docs/03_acceptance.md', '/root/projects/trading-execution/docs/03_contracts.md'),
  payload = replace(payload, '/root/projects/trading-execution/docs/03_acceptance.md', '/root/projects/trading-execution/docs/03_contracts.md'),
  applies_to = replace(applies_to, '/root/projects/trading-execution/docs/03_acceptance.md', '/root/projects/trading-execution/docs/03_contracts.md'),
  note = replace(note, '/root/projects/trading-execution/docs/03_acceptance.md', '/root/projects/trading-execution/docs/03_contracts.md')
WHERE path LIKE '%/root/projects/trading-execution/docs/03_acceptance.md%' OR payload LIKE '%/root/projects/trading-execution/docs/03_acceptance.md%' OR applies_to LIKE '%/root/projects/trading-execution/docs/03_acceptance.md%' OR note LIKE '%/root/projects/trading-execution/docs/03_acceptance.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-execution/docs/03_acceptance.md', 'file:/root/projects/trading-execution/docs/03_contracts.md'),
  payload = replace(payload, 'file:/root/projects/trading-execution/docs/03_acceptance.md', 'file:/root/projects/trading-execution/docs/03_contracts.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-execution/docs/03_acceptance.md', 'file:/root/projects/trading-execution/docs/03_contracts.md'),
  note = replace(note, 'file:/root/projects/trading-execution/docs/03_acceptance.md', 'file:/root/projects/trading-execution/docs/03_contracts.md')
WHERE path LIKE '%file:/root/projects/trading-execution/docs/03_acceptance.md%' OR payload LIKE '%file:/root/projects/trading-execution/docs/03_acceptance.md%' OR applies_to LIKE '%file:/root/projects/trading-execution/docs/03_acceptance.md%' OR note LIKE '%file:/root/projects/trading-execution/docs/03_acceptance.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-execution/docs/80_task.md', 'trading-execution/docs/04_task.md'),
  payload = replace(payload, 'trading-execution/docs/80_task.md', 'trading-execution/docs/04_task.md'),
  applies_to = replace(applies_to, 'trading-execution/docs/80_task.md', 'trading-execution/docs/04_task.md'),
  note = replace(note, 'trading-execution/docs/80_task.md', 'trading-execution/docs/04_task.md')
WHERE path LIKE '%trading-execution/docs/80_task.md%' OR payload LIKE '%trading-execution/docs/80_task.md%' OR applies_to LIKE '%trading-execution/docs/80_task.md%' OR note LIKE '%trading-execution/docs/80_task.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-execution/docs/80_task.md', '/root/projects/trading-execution/docs/04_task.md'),
  payload = replace(payload, '/root/projects/trading-execution/docs/80_task.md', '/root/projects/trading-execution/docs/04_task.md'),
  applies_to = replace(applies_to, '/root/projects/trading-execution/docs/80_task.md', '/root/projects/trading-execution/docs/04_task.md'),
  note = replace(note, '/root/projects/trading-execution/docs/80_task.md', '/root/projects/trading-execution/docs/04_task.md')
WHERE path LIKE '%/root/projects/trading-execution/docs/80_task.md%' OR payload LIKE '%/root/projects/trading-execution/docs/80_task.md%' OR applies_to LIKE '%/root/projects/trading-execution/docs/80_task.md%' OR note LIKE '%/root/projects/trading-execution/docs/80_task.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-execution/docs/80_task.md', 'file:/root/projects/trading-execution/docs/04_task.md'),
  payload = replace(payload, 'file:/root/projects/trading-execution/docs/80_task.md', 'file:/root/projects/trading-execution/docs/04_task.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-execution/docs/80_task.md', 'file:/root/projects/trading-execution/docs/04_task.md'),
  note = replace(note, 'file:/root/projects/trading-execution/docs/80_task.md', 'file:/root/projects/trading-execution/docs/04_task.md')
WHERE path LIKE '%file:/root/projects/trading-execution/docs/80_task.md%' OR payload LIKE '%file:/root/projects/trading-execution/docs/80_task.md%' OR applies_to LIKE '%file:/root/projects/trading-execution/docs/80_task.md%' OR note LIKE '%file:/root/projects/trading-execution/docs/80_task.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-execution/docs/81_decision.md', 'trading-execution/docs/05_decision.md'),
  payload = replace(payload, 'trading-execution/docs/81_decision.md', 'trading-execution/docs/05_decision.md'),
  applies_to = replace(applies_to, 'trading-execution/docs/81_decision.md', 'trading-execution/docs/05_decision.md'),
  note = replace(note, 'trading-execution/docs/81_decision.md', 'trading-execution/docs/05_decision.md')
WHERE path LIKE '%trading-execution/docs/81_decision.md%' OR payload LIKE '%trading-execution/docs/81_decision.md%' OR applies_to LIKE '%trading-execution/docs/81_decision.md%' OR note LIKE '%trading-execution/docs/81_decision.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-execution/docs/81_decision.md', '/root/projects/trading-execution/docs/05_decision.md'),
  payload = replace(payload, '/root/projects/trading-execution/docs/81_decision.md', '/root/projects/trading-execution/docs/05_decision.md'),
  applies_to = replace(applies_to, '/root/projects/trading-execution/docs/81_decision.md', '/root/projects/trading-execution/docs/05_decision.md'),
  note = replace(note, '/root/projects/trading-execution/docs/81_decision.md', '/root/projects/trading-execution/docs/05_decision.md')
WHERE path LIKE '%/root/projects/trading-execution/docs/81_decision.md%' OR payload LIKE '%/root/projects/trading-execution/docs/81_decision.md%' OR applies_to LIKE '%/root/projects/trading-execution/docs/81_decision.md%' OR note LIKE '%/root/projects/trading-execution/docs/81_decision.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-execution/docs/81_decision.md', 'file:/root/projects/trading-execution/docs/05_decision.md'),
  payload = replace(payload, 'file:/root/projects/trading-execution/docs/81_decision.md', 'file:/root/projects/trading-execution/docs/05_decision.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-execution/docs/81_decision.md', 'file:/root/projects/trading-execution/docs/05_decision.md'),
  note = replace(note, 'file:/root/projects/trading-execution/docs/81_decision.md', 'file:/root/projects/trading-execution/docs/05_decision.md')
WHERE path LIKE '%file:/root/projects/trading-execution/docs/81_decision.md%' OR payload LIKE '%file:/root/projects/trading-execution/docs/81_decision.md%' OR applies_to LIKE '%file:/root/projects/trading-execution/docs/81_decision.md%' OR note LIKE '%file:/root/projects/trading-execution/docs/81_decision.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-execution/docs/82_memory.md', 'trading-execution/docs/06_memory.md'),
  payload = replace(payload, 'trading-execution/docs/82_memory.md', 'trading-execution/docs/06_memory.md'),
  applies_to = replace(applies_to, 'trading-execution/docs/82_memory.md', 'trading-execution/docs/06_memory.md'),
  note = replace(note, 'trading-execution/docs/82_memory.md', 'trading-execution/docs/06_memory.md')
WHERE path LIKE '%trading-execution/docs/82_memory.md%' OR payload LIKE '%trading-execution/docs/82_memory.md%' OR applies_to LIKE '%trading-execution/docs/82_memory.md%' OR note LIKE '%trading-execution/docs/82_memory.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-execution/docs/82_memory.md', '/root/projects/trading-execution/docs/06_memory.md'),
  payload = replace(payload, '/root/projects/trading-execution/docs/82_memory.md', '/root/projects/trading-execution/docs/06_memory.md'),
  applies_to = replace(applies_to, '/root/projects/trading-execution/docs/82_memory.md', '/root/projects/trading-execution/docs/06_memory.md'),
  note = replace(note, '/root/projects/trading-execution/docs/82_memory.md', '/root/projects/trading-execution/docs/06_memory.md')
WHERE path LIKE '%/root/projects/trading-execution/docs/82_memory.md%' OR payload LIKE '%/root/projects/trading-execution/docs/82_memory.md%' OR applies_to LIKE '%/root/projects/trading-execution/docs/82_memory.md%' OR note LIKE '%/root/projects/trading-execution/docs/82_memory.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-execution/docs/82_memory.md', 'file:/root/projects/trading-execution/docs/06_memory.md'),
  payload = replace(payload, 'file:/root/projects/trading-execution/docs/82_memory.md', 'file:/root/projects/trading-execution/docs/06_memory.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-execution/docs/82_memory.md', 'file:/root/projects/trading-execution/docs/06_memory.md'),
  note = replace(note, 'file:/root/projects/trading-execution/docs/82_memory.md', 'file:/root/projects/trading-execution/docs/06_memory.md')
WHERE path LIKE '%file:/root/projects/trading-execution/docs/82_memory.md%' OR payload LIKE '%file:/root/projects/trading-execution/docs/82_memory.md%' OR applies_to LIKE '%file:/root/projects/trading-execution/docs/82_memory.md%' OR note LIKE '%file:/root/projects/trading-execution/docs/82_memory.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-execution/docs/04_trade_risk_cap.md', 'trading-execution/docs/10_trade_risk_cap.md'),
  payload = replace(payload, 'trading-execution/docs/04_trade_risk_cap.md', 'trading-execution/docs/10_trade_risk_cap.md'),
  applies_to = replace(applies_to, 'trading-execution/docs/04_trade_risk_cap.md', 'trading-execution/docs/10_trade_risk_cap.md'),
  note = replace(note, 'trading-execution/docs/04_trade_risk_cap.md', 'trading-execution/docs/10_trade_risk_cap.md')
WHERE path LIKE '%trading-execution/docs/04_trade_risk_cap.md%' OR payload LIKE '%trading-execution/docs/04_trade_risk_cap.md%' OR applies_to LIKE '%trading-execution/docs/04_trade_risk_cap.md%' OR note LIKE '%trading-execution/docs/04_trade_risk_cap.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-execution/docs/04_trade_risk_cap.md', '/root/projects/trading-execution/docs/10_trade_risk_cap.md'),
  payload = replace(payload, '/root/projects/trading-execution/docs/04_trade_risk_cap.md', '/root/projects/trading-execution/docs/10_trade_risk_cap.md'),
  applies_to = replace(applies_to, '/root/projects/trading-execution/docs/04_trade_risk_cap.md', '/root/projects/trading-execution/docs/10_trade_risk_cap.md'),
  note = replace(note, '/root/projects/trading-execution/docs/04_trade_risk_cap.md', '/root/projects/trading-execution/docs/10_trade_risk_cap.md')
WHERE path LIKE '%/root/projects/trading-execution/docs/04_trade_risk_cap.md%' OR payload LIKE '%/root/projects/trading-execution/docs/04_trade_risk_cap.md%' OR applies_to LIKE '%/root/projects/trading-execution/docs/04_trade_risk_cap.md%' OR note LIKE '%/root/projects/trading-execution/docs/04_trade_risk_cap.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-execution/docs/04_trade_risk_cap.md', 'file:/root/projects/trading-execution/docs/10_trade_risk_cap.md'),
  payload = replace(payload, 'file:/root/projects/trading-execution/docs/04_trade_risk_cap.md', 'file:/root/projects/trading-execution/docs/10_trade_risk_cap.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-execution/docs/04_trade_risk_cap.md', 'file:/root/projects/trading-execution/docs/10_trade_risk_cap.md'),
  note = replace(note, 'file:/root/projects/trading-execution/docs/04_trade_risk_cap.md', 'file:/root/projects/trading-execution/docs/10_trade_risk_cap.md')
WHERE path LIKE '%file:/root/projects/trading-execution/docs/04_trade_risk_cap.md%' OR payload LIKE '%file:/root/projects/trading-execution/docs/04_trade_risk_cap.md%' OR applies_to LIKE '%file:/root/projects/trading-execution/docs/04_trade_risk_cap.md%' OR note LIKE '%file:/root/projects/trading-execution/docs/04_trade_risk_cap.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-execution/docs/05_execution_acceptance.md', 'trading-execution/docs/11_execution_acceptance.md'),
  payload = replace(payload, 'trading-execution/docs/05_execution_acceptance.md', 'trading-execution/docs/11_execution_acceptance.md'),
  applies_to = replace(applies_to, 'trading-execution/docs/05_execution_acceptance.md', 'trading-execution/docs/11_execution_acceptance.md'),
  note = replace(note, 'trading-execution/docs/05_execution_acceptance.md', 'trading-execution/docs/11_execution_acceptance.md')
WHERE path LIKE '%trading-execution/docs/05_execution_acceptance.md%' OR payload LIKE '%trading-execution/docs/05_execution_acceptance.md%' OR applies_to LIKE '%trading-execution/docs/05_execution_acceptance.md%' OR note LIKE '%trading-execution/docs/05_execution_acceptance.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-execution/docs/05_execution_acceptance.md', '/root/projects/trading-execution/docs/11_execution_acceptance.md'),
  payload = replace(payload, '/root/projects/trading-execution/docs/05_execution_acceptance.md', '/root/projects/trading-execution/docs/11_execution_acceptance.md'),
  applies_to = replace(applies_to, '/root/projects/trading-execution/docs/05_execution_acceptance.md', '/root/projects/trading-execution/docs/11_execution_acceptance.md'),
  note = replace(note, '/root/projects/trading-execution/docs/05_execution_acceptance.md', '/root/projects/trading-execution/docs/11_execution_acceptance.md')
WHERE path LIKE '%/root/projects/trading-execution/docs/05_execution_acceptance.md%' OR payload LIKE '%/root/projects/trading-execution/docs/05_execution_acceptance.md%' OR applies_to LIKE '%/root/projects/trading-execution/docs/05_execution_acceptance.md%' OR note LIKE '%/root/projects/trading-execution/docs/05_execution_acceptance.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-execution/docs/05_execution_acceptance.md', 'file:/root/projects/trading-execution/docs/11_execution_acceptance.md'),
  payload = replace(payload, 'file:/root/projects/trading-execution/docs/05_execution_acceptance.md', 'file:/root/projects/trading-execution/docs/11_execution_acceptance.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-execution/docs/05_execution_acceptance.md', 'file:/root/projects/trading-execution/docs/11_execution_acceptance.md'),
  note = replace(note, 'file:/root/projects/trading-execution/docs/05_execution_acceptance.md', 'file:/root/projects/trading-execution/docs/11_execution_acceptance.md')
WHERE path LIKE '%file:/root/projects/trading-execution/docs/05_execution_acceptance.md%' OR payload LIKE '%file:/root/projects/trading-execution/docs/05_execution_acceptance.md%' OR applies_to LIKE '%file:/root/projects/trading-execution/docs/05_execution_acceptance.md%' OR note LIKE '%file:/root/projects/trading-execution/docs/05_execution_acceptance.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-execution/docs/06_realtime_data.md', 'trading-execution/docs/20_realtime_data.md'),
  payload = replace(payload, 'trading-execution/docs/06_realtime_data.md', 'trading-execution/docs/20_realtime_data.md'),
  applies_to = replace(applies_to, 'trading-execution/docs/06_realtime_data.md', 'trading-execution/docs/20_realtime_data.md'),
  note = replace(note, 'trading-execution/docs/06_realtime_data.md', 'trading-execution/docs/20_realtime_data.md')
WHERE path LIKE '%trading-execution/docs/06_realtime_data.md%' OR payload LIKE '%trading-execution/docs/06_realtime_data.md%' OR applies_to LIKE '%trading-execution/docs/06_realtime_data.md%' OR note LIKE '%trading-execution/docs/06_realtime_data.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-execution/docs/06_realtime_data.md', '/root/projects/trading-execution/docs/20_realtime_data.md'),
  payload = replace(payload, '/root/projects/trading-execution/docs/06_realtime_data.md', '/root/projects/trading-execution/docs/20_realtime_data.md'),
  applies_to = replace(applies_to, '/root/projects/trading-execution/docs/06_realtime_data.md', '/root/projects/trading-execution/docs/20_realtime_data.md'),
  note = replace(note, '/root/projects/trading-execution/docs/06_realtime_data.md', '/root/projects/trading-execution/docs/20_realtime_data.md')
WHERE path LIKE '%/root/projects/trading-execution/docs/06_realtime_data.md%' OR payload LIKE '%/root/projects/trading-execution/docs/06_realtime_data.md%' OR applies_to LIKE '%/root/projects/trading-execution/docs/06_realtime_data.md%' OR note LIKE '%/root/projects/trading-execution/docs/06_realtime_data.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-execution/docs/06_realtime_data.md', 'file:/root/projects/trading-execution/docs/20_realtime_data.md'),
  payload = replace(payload, 'file:/root/projects/trading-execution/docs/06_realtime_data.md', 'file:/root/projects/trading-execution/docs/20_realtime_data.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-execution/docs/06_realtime_data.md', 'file:/root/projects/trading-execution/docs/20_realtime_data.md'),
  note = replace(note, 'file:/root/projects/trading-execution/docs/06_realtime_data.md', 'file:/root/projects/trading-execution/docs/20_realtime_data.md')
WHERE path LIKE '%file:/root/projects/trading-execution/docs/06_realtime_data.md%' OR payload LIKE '%file:/root/projects/trading-execution/docs/06_realtime_data.md%' OR applies_to LIKE '%file:/root/projects/trading-execution/docs/06_realtime_data.md%' OR note LIKE '%file:/root/projects/trading-execution/docs/06_realtime_data.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-execution/docs/07_broker_interfaces.md', 'trading-execution/docs/30_broker_interfaces.md'),
  payload = replace(payload, 'trading-execution/docs/07_broker_interfaces.md', 'trading-execution/docs/30_broker_interfaces.md'),
  applies_to = replace(applies_to, 'trading-execution/docs/07_broker_interfaces.md', 'trading-execution/docs/30_broker_interfaces.md'),
  note = replace(note, 'trading-execution/docs/07_broker_interfaces.md', 'trading-execution/docs/30_broker_interfaces.md')
WHERE path LIKE '%trading-execution/docs/07_broker_interfaces.md%' OR payload LIKE '%trading-execution/docs/07_broker_interfaces.md%' OR applies_to LIKE '%trading-execution/docs/07_broker_interfaces.md%' OR note LIKE '%trading-execution/docs/07_broker_interfaces.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-execution/docs/07_broker_interfaces.md', '/root/projects/trading-execution/docs/30_broker_interfaces.md'),
  payload = replace(payload, '/root/projects/trading-execution/docs/07_broker_interfaces.md', '/root/projects/trading-execution/docs/30_broker_interfaces.md'),
  applies_to = replace(applies_to, '/root/projects/trading-execution/docs/07_broker_interfaces.md', '/root/projects/trading-execution/docs/30_broker_interfaces.md'),
  note = replace(note, '/root/projects/trading-execution/docs/07_broker_interfaces.md', '/root/projects/trading-execution/docs/30_broker_interfaces.md')
WHERE path LIKE '%/root/projects/trading-execution/docs/07_broker_interfaces.md%' OR payload LIKE '%/root/projects/trading-execution/docs/07_broker_interfaces.md%' OR applies_to LIKE '%/root/projects/trading-execution/docs/07_broker_interfaces.md%' OR note LIKE '%/root/projects/trading-execution/docs/07_broker_interfaces.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-execution/docs/07_broker_interfaces.md', 'file:/root/projects/trading-execution/docs/30_broker_interfaces.md'),
  payload = replace(payload, 'file:/root/projects/trading-execution/docs/07_broker_interfaces.md', 'file:/root/projects/trading-execution/docs/30_broker_interfaces.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-execution/docs/07_broker_interfaces.md', 'file:/root/projects/trading-execution/docs/30_broker_interfaces.md'),
  note = replace(note, 'file:/root/projects/trading-execution/docs/07_broker_interfaces.md', 'file:/root/projects/trading-execution/docs/30_broker_interfaces.md')
WHERE path LIKE '%file:/root/projects/trading-execution/docs/07_broker_interfaces.md%' OR payload LIKE '%file:/root/projects/trading-execution/docs/07_broker_interfaces.md%' OR applies_to LIKE '%file:/root/projects/trading-execution/docs/07_broker_interfaces.md%' OR note LIKE '%file:/root/projects/trading-execution/docs/07_broker_interfaces.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-data/docs/11_data_organization.md', 'trading-data/docs/02_architecture.md'),
  payload = replace(payload, 'trading-data/docs/11_data_organization.md', 'trading-data/docs/02_architecture.md'),
  applies_to = replace(applies_to, 'trading-data/docs/11_data_organization.md', 'trading-data/docs/02_architecture.md'),
  note = replace(note, 'trading-data/docs/11_data_organization.md', 'trading-data/docs/02_architecture.md')
WHERE path LIKE '%trading-data/docs/11_data_organization.md%' OR payload LIKE '%trading-data/docs/11_data_organization.md%' OR applies_to LIKE '%trading-data/docs/11_data_organization.md%' OR note LIKE '%trading-data/docs/11_data_organization.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-data/docs/11_data_organization.md', '/root/projects/trading-data/docs/02_architecture.md'),
  payload = replace(payload, '/root/projects/trading-data/docs/11_data_organization.md', '/root/projects/trading-data/docs/02_architecture.md'),
  applies_to = replace(applies_to, '/root/projects/trading-data/docs/11_data_organization.md', '/root/projects/trading-data/docs/02_architecture.md'),
  note = replace(note, '/root/projects/trading-data/docs/11_data_organization.md', '/root/projects/trading-data/docs/02_architecture.md')
WHERE path LIKE '%/root/projects/trading-data/docs/11_data_organization.md%' OR payload LIKE '%/root/projects/trading-data/docs/11_data_organization.md%' OR applies_to LIKE '%/root/projects/trading-data/docs/11_data_organization.md%' OR note LIKE '%/root/projects/trading-data/docs/11_data_organization.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-data/docs/11_data_organization.md', 'file:/root/projects/trading-data/docs/02_architecture.md'),
  payload = replace(payload, 'file:/root/projects/trading-data/docs/11_data_organization.md', 'file:/root/projects/trading-data/docs/02_architecture.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-data/docs/11_data_organization.md', 'file:/root/projects/trading-data/docs/02_architecture.md'),
  note = replace(note, 'file:/root/projects/trading-data/docs/11_data_organization.md', 'file:/root/projects/trading-data/docs/02_architecture.md')
WHERE path LIKE '%file:/root/projects/trading-data/docs/11_data_organization.md%' OR payload LIKE '%file:/root/projects/trading-data/docs/11_data_organization.md%' OR applies_to LIKE '%file:/root/projects/trading-data/docs/11_data_organization.md%' OR note LIKE '%file:/root/projects/trading-data/docs/11_data_organization.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-data/docs/16_data_stack_acceptance.md', 'trading-data/docs/03_contracts.md'),
  payload = replace(payload, 'trading-data/docs/16_data_stack_acceptance.md', 'trading-data/docs/03_contracts.md'),
  applies_to = replace(applies_to, 'trading-data/docs/16_data_stack_acceptance.md', 'trading-data/docs/03_contracts.md'),
  note = replace(note, 'trading-data/docs/16_data_stack_acceptance.md', 'trading-data/docs/03_contracts.md')
WHERE path LIKE '%trading-data/docs/16_data_stack_acceptance.md%' OR payload LIKE '%trading-data/docs/16_data_stack_acceptance.md%' OR applies_to LIKE '%trading-data/docs/16_data_stack_acceptance.md%' OR note LIKE '%trading-data/docs/16_data_stack_acceptance.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-data/docs/16_data_stack_acceptance.md', '/root/projects/trading-data/docs/03_contracts.md'),
  payload = replace(payload, '/root/projects/trading-data/docs/16_data_stack_acceptance.md', '/root/projects/trading-data/docs/03_contracts.md'),
  applies_to = replace(applies_to, '/root/projects/trading-data/docs/16_data_stack_acceptance.md', '/root/projects/trading-data/docs/03_contracts.md'),
  note = replace(note, '/root/projects/trading-data/docs/16_data_stack_acceptance.md', '/root/projects/trading-data/docs/03_contracts.md')
WHERE path LIKE '%/root/projects/trading-data/docs/16_data_stack_acceptance.md%' OR payload LIKE '%/root/projects/trading-data/docs/16_data_stack_acceptance.md%' OR applies_to LIKE '%/root/projects/trading-data/docs/16_data_stack_acceptance.md%' OR note LIKE '%/root/projects/trading-data/docs/16_data_stack_acceptance.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-data/docs/16_data_stack_acceptance.md', 'file:/root/projects/trading-data/docs/03_contracts.md'),
  payload = replace(payload, 'file:/root/projects/trading-data/docs/16_data_stack_acceptance.md', 'file:/root/projects/trading-data/docs/03_contracts.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-data/docs/16_data_stack_acceptance.md', 'file:/root/projects/trading-data/docs/03_contracts.md'),
  note = replace(note, 'file:/root/projects/trading-data/docs/16_data_stack_acceptance.md', 'file:/root/projects/trading-data/docs/03_contracts.md')
WHERE path LIKE '%file:/root/projects/trading-data/docs/16_data_stack_acceptance.md%' OR payload LIKE '%file:/root/projects/trading-data/docs/16_data_stack_acceptance.md%' OR applies_to LIKE '%file:/root/projects/trading-data/docs/16_data_stack_acceptance.md%' OR note LIKE '%file:/root/projects/trading-data/docs/16_data_stack_acceptance.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-data/docs/80_task.md', 'trading-data/docs/04_task.md'),
  payload = replace(payload, 'trading-data/docs/80_task.md', 'trading-data/docs/04_task.md'),
  applies_to = replace(applies_to, 'trading-data/docs/80_task.md', 'trading-data/docs/04_task.md'),
  note = replace(note, 'trading-data/docs/80_task.md', 'trading-data/docs/04_task.md')
WHERE path LIKE '%trading-data/docs/80_task.md%' OR payload LIKE '%trading-data/docs/80_task.md%' OR applies_to LIKE '%trading-data/docs/80_task.md%' OR note LIKE '%trading-data/docs/80_task.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-data/docs/80_task.md', '/root/projects/trading-data/docs/04_task.md'),
  payload = replace(payload, '/root/projects/trading-data/docs/80_task.md', '/root/projects/trading-data/docs/04_task.md'),
  applies_to = replace(applies_to, '/root/projects/trading-data/docs/80_task.md', '/root/projects/trading-data/docs/04_task.md'),
  note = replace(note, '/root/projects/trading-data/docs/80_task.md', '/root/projects/trading-data/docs/04_task.md')
WHERE path LIKE '%/root/projects/trading-data/docs/80_task.md%' OR payload LIKE '%/root/projects/trading-data/docs/80_task.md%' OR applies_to LIKE '%/root/projects/trading-data/docs/80_task.md%' OR note LIKE '%/root/projects/trading-data/docs/80_task.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-data/docs/80_task.md', 'file:/root/projects/trading-data/docs/04_task.md'),
  payload = replace(payload, 'file:/root/projects/trading-data/docs/80_task.md', 'file:/root/projects/trading-data/docs/04_task.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-data/docs/80_task.md', 'file:/root/projects/trading-data/docs/04_task.md'),
  note = replace(note, 'file:/root/projects/trading-data/docs/80_task.md', 'file:/root/projects/trading-data/docs/04_task.md')
WHERE path LIKE '%file:/root/projects/trading-data/docs/80_task.md%' OR payload LIKE '%file:/root/projects/trading-data/docs/80_task.md%' OR applies_to LIKE '%file:/root/projects/trading-data/docs/80_task.md%' OR note LIKE '%file:/root/projects/trading-data/docs/80_task.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-data/docs/81_decision.md', 'trading-data/docs/05_decision.md'),
  payload = replace(payload, 'trading-data/docs/81_decision.md', 'trading-data/docs/05_decision.md'),
  applies_to = replace(applies_to, 'trading-data/docs/81_decision.md', 'trading-data/docs/05_decision.md'),
  note = replace(note, 'trading-data/docs/81_decision.md', 'trading-data/docs/05_decision.md')
WHERE path LIKE '%trading-data/docs/81_decision.md%' OR payload LIKE '%trading-data/docs/81_decision.md%' OR applies_to LIKE '%trading-data/docs/81_decision.md%' OR note LIKE '%trading-data/docs/81_decision.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-data/docs/81_decision.md', '/root/projects/trading-data/docs/05_decision.md'),
  payload = replace(payload, '/root/projects/trading-data/docs/81_decision.md', '/root/projects/trading-data/docs/05_decision.md'),
  applies_to = replace(applies_to, '/root/projects/trading-data/docs/81_decision.md', '/root/projects/trading-data/docs/05_decision.md'),
  note = replace(note, '/root/projects/trading-data/docs/81_decision.md', '/root/projects/trading-data/docs/05_decision.md')
WHERE path LIKE '%/root/projects/trading-data/docs/81_decision.md%' OR payload LIKE '%/root/projects/trading-data/docs/81_decision.md%' OR applies_to LIKE '%/root/projects/trading-data/docs/81_decision.md%' OR note LIKE '%/root/projects/trading-data/docs/81_decision.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-data/docs/81_decision.md', 'file:/root/projects/trading-data/docs/05_decision.md'),
  payload = replace(payload, 'file:/root/projects/trading-data/docs/81_decision.md', 'file:/root/projects/trading-data/docs/05_decision.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-data/docs/81_decision.md', 'file:/root/projects/trading-data/docs/05_decision.md'),
  note = replace(note, 'file:/root/projects/trading-data/docs/81_decision.md', 'file:/root/projects/trading-data/docs/05_decision.md')
WHERE path LIKE '%file:/root/projects/trading-data/docs/81_decision.md%' OR payload LIKE '%file:/root/projects/trading-data/docs/81_decision.md%' OR applies_to LIKE '%file:/root/projects/trading-data/docs/81_decision.md%' OR note LIKE '%file:/root/projects/trading-data/docs/81_decision.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-data/docs/82_memory.md', 'trading-data/docs/06_memory.md'),
  payload = replace(payload, 'trading-data/docs/82_memory.md', 'trading-data/docs/06_memory.md'),
  applies_to = replace(applies_to, 'trading-data/docs/82_memory.md', 'trading-data/docs/06_memory.md'),
  note = replace(note, 'trading-data/docs/82_memory.md', 'trading-data/docs/06_memory.md')
WHERE path LIKE '%trading-data/docs/82_memory.md%' OR payload LIKE '%trading-data/docs/82_memory.md%' OR applies_to LIKE '%trading-data/docs/82_memory.md%' OR note LIKE '%trading-data/docs/82_memory.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-data/docs/82_memory.md', '/root/projects/trading-data/docs/06_memory.md'),
  payload = replace(payload, '/root/projects/trading-data/docs/82_memory.md', '/root/projects/trading-data/docs/06_memory.md'),
  applies_to = replace(applies_to, '/root/projects/trading-data/docs/82_memory.md', '/root/projects/trading-data/docs/06_memory.md'),
  note = replace(note, '/root/projects/trading-data/docs/82_memory.md', '/root/projects/trading-data/docs/06_memory.md')
WHERE path LIKE '%/root/projects/trading-data/docs/82_memory.md%' OR payload LIKE '%/root/projects/trading-data/docs/82_memory.md%' OR applies_to LIKE '%/root/projects/trading-data/docs/82_memory.md%' OR note LIKE '%/root/projects/trading-data/docs/82_memory.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-data/docs/82_memory.md', 'file:/root/projects/trading-data/docs/06_memory.md'),
  payload = replace(payload, 'file:/root/projects/trading-data/docs/82_memory.md', 'file:/root/projects/trading-data/docs/06_memory.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-data/docs/82_memory.md', 'file:/root/projects/trading-data/docs/06_memory.md'),
  note = replace(note, 'file:/root/projects/trading-data/docs/82_memory.md', 'file:/root/projects/trading-data/docs/06_memory.md')
WHERE path LIKE '%file:/root/projects/trading-data/docs/82_memory.md%' OR payload LIKE '%file:/root/projects/trading-data/docs/82_memory.md%' OR applies_to LIKE '%file:/root/projects/trading-data/docs/82_memory.md%' OR note LIKE '%file:/root/projects/trading-data/docs/82_memory.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-data/docs/02_layer_01_market_regime.md', 'trading-data/docs/10_layer_01_market_regime.md'),
  payload = replace(payload, 'trading-data/docs/02_layer_01_market_regime.md', 'trading-data/docs/10_layer_01_market_regime.md'),
  applies_to = replace(applies_to, 'trading-data/docs/02_layer_01_market_regime.md', 'trading-data/docs/10_layer_01_market_regime.md'),
  note = replace(note, 'trading-data/docs/02_layer_01_market_regime.md', 'trading-data/docs/10_layer_01_market_regime.md')
WHERE path LIKE '%trading-data/docs/02_layer_01_market_regime.md%' OR payload LIKE '%trading-data/docs/02_layer_01_market_regime.md%' OR applies_to LIKE '%trading-data/docs/02_layer_01_market_regime.md%' OR note LIKE '%trading-data/docs/02_layer_01_market_regime.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-data/docs/02_layer_01_market_regime.md', '/root/projects/trading-data/docs/10_layer_01_market_regime.md'),
  payload = replace(payload, '/root/projects/trading-data/docs/02_layer_01_market_regime.md', '/root/projects/trading-data/docs/10_layer_01_market_regime.md'),
  applies_to = replace(applies_to, '/root/projects/trading-data/docs/02_layer_01_market_regime.md', '/root/projects/trading-data/docs/10_layer_01_market_regime.md'),
  note = replace(note, '/root/projects/trading-data/docs/02_layer_01_market_regime.md', '/root/projects/trading-data/docs/10_layer_01_market_regime.md')
WHERE path LIKE '%/root/projects/trading-data/docs/02_layer_01_market_regime.md%' OR payload LIKE '%/root/projects/trading-data/docs/02_layer_01_market_regime.md%' OR applies_to LIKE '%/root/projects/trading-data/docs/02_layer_01_market_regime.md%' OR note LIKE '%/root/projects/trading-data/docs/02_layer_01_market_regime.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-data/docs/02_layer_01_market_regime.md', 'file:/root/projects/trading-data/docs/10_layer_01_market_regime.md'),
  payload = replace(payload, 'file:/root/projects/trading-data/docs/02_layer_01_market_regime.md', 'file:/root/projects/trading-data/docs/10_layer_01_market_regime.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-data/docs/02_layer_01_market_regime.md', 'file:/root/projects/trading-data/docs/10_layer_01_market_regime.md'),
  note = replace(note, 'file:/root/projects/trading-data/docs/02_layer_01_market_regime.md', 'file:/root/projects/trading-data/docs/10_layer_01_market_regime.md')
WHERE path LIKE '%file:/root/projects/trading-data/docs/02_layer_01_market_regime.md%' OR payload LIKE '%file:/root/projects/trading-data/docs/02_layer_01_market_regime.md%' OR applies_to LIKE '%file:/root/projects/trading-data/docs/02_layer_01_market_regime.md%' OR note LIKE '%file:/root/projects/trading-data/docs/02_layer_01_market_regime.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-data/docs/03_layer_02_sector_context.md', 'trading-data/docs/11_layer_02_sector_context.md'),
  payload = replace(payload, 'trading-data/docs/03_layer_02_sector_context.md', 'trading-data/docs/11_layer_02_sector_context.md'),
  applies_to = replace(applies_to, 'trading-data/docs/03_layer_02_sector_context.md', 'trading-data/docs/11_layer_02_sector_context.md'),
  note = replace(note, 'trading-data/docs/03_layer_02_sector_context.md', 'trading-data/docs/11_layer_02_sector_context.md')
WHERE path LIKE '%trading-data/docs/03_layer_02_sector_context.md%' OR payload LIKE '%trading-data/docs/03_layer_02_sector_context.md%' OR applies_to LIKE '%trading-data/docs/03_layer_02_sector_context.md%' OR note LIKE '%trading-data/docs/03_layer_02_sector_context.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-data/docs/03_layer_02_sector_context.md', '/root/projects/trading-data/docs/11_layer_02_sector_context.md'),
  payload = replace(payload, '/root/projects/trading-data/docs/03_layer_02_sector_context.md', '/root/projects/trading-data/docs/11_layer_02_sector_context.md'),
  applies_to = replace(applies_to, '/root/projects/trading-data/docs/03_layer_02_sector_context.md', '/root/projects/trading-data/docs/11_layer_02_sector_context.md'),
  note = replace(note, '/root/projects/trading-data/docs/03_layer_02_sector_context.md', '/root/projects/trading-data/docs/11_layer_02_sector_context.md')
WHERE path LIKE '%/root/projects/trading-data/docs/03_layer_02_sector_context.md%' OR payload LIKE '%/root/projects/trading-data/docs/03_layer_02_sector_context.md%' OR applies_to LIKE '%/root/projects/trading-data/docs/03_layer_02_sector_context.md%' OR note LIKE '%/root/projects/trading-data/docs/03_layer_02_sector_context.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-data/docs/03_layer_02_sector_context.md', 'file:/root/projects/trading-data/docs/11_layer_02_sector_context.md'),
  payload = replace(payload, 'file:/root/projects/trading-data/docs/03_layer_02_sector_context.md', 'file:/root/projects/trading-data/docs/11_layer_02_sector_context.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-data/docs/03_layer_02_sector_context.md', 'file:/root/projects/trading-data/docs/11_layer_02_sector_context.md'),
  note = replace(note, 'file:/root/projects/trading-data/docs/03_layer_02_sector_context.md', 'file:/root/projects/trading-data/docs/11_layer_02_sector_context.md')
WHERE path LIKE '%file:/root/projects/trading-data/docs/03_layer_02_sector_context.md%' OR payload LIKE '%file:/root/projects/trading-data/docs/03_layer_02_sector_context.md%' OR applies_to LIKE '%file:/root/projects/trading-data/docs/03_layer_02_sector_context.md%' OR note LIKE '%file:/root/projects/trading-data/docs/03_layer_02_sector_context.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-data/docs/04_layer_03_target_state_vector.md', 'trading-data/docs/12_layer_03_target_state_vector.md'),
  payload = replace(payload, 'trading-data/docs/04_layer_03_target_state_vector.md', 'trading-data/docs/12_layer_03_target_state_vector.md'),
  applies_to = replace(applies_to, 'trading-data/docs/04_layer_03_target_state_vector.md', 'trading-data/docs/12_layer_03_target_state_vector.md'),
  note = replace(note, 'trading-data/docs/04_layer_03_target_state_vector.md', 'trading-data/docs/12_layer_03_target_state_vector.md')
WHERE path LIKE '%trading-data/docs/04_layer_03_target_state_vector.md%' OR payload LIKE '%trading-data/docs/04_layer_03_target_state_vector.md%' OR applies_to LIKE '%trading-data/docs/04_layer_03_target_state_vector.md%' OR note LIKE '%trading-data/docs/04_layer_03_target_state_vector.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-data/docs/04_layer_03_target_state_vector.md', '/root/projects/trading-data/docs/12_layer_03_target_state_vector.md'),
  payload = replace(payload, '/root/projects/trading-data/docs/04_layer_03_target_state_vector.md', '/root/projects/trading-data/docs/12_layer_03_target_state_vector.md'),
  applies_to = replace(applies_to, '/root/projects/trading-data/docs/04_layer_03_target_state_vector.md', '/root/projects/trading-data/docs/12_layer_03_target_state_vector.md'),
  note = replace(note, '/root/projects/trading-data/docs/04_layer_03_target_state_vector.md', '/root/projects/trading-data/docs/12_layer_03_target_state_vector.md')
WHERE path LIKE '%/root/projects/trading-data/docs/04_layer_03_target_state_vector.md%' OR payload LIKE '%/root/projects/trading-data/docs/04_layer_03_target_state_vector.md%' OR applies_to LIKE '%/root/projects/trading-data/docs/04_layer_03_target_state_vector.md%' OR note LIKE '%/root/projects/trading-data/docs/04_layer_03_target_state_vector.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-data/docs/04_layer_03_target_state_vector.md', 'file:/root/projects/trading-data/docs/12_layer_03_target_state_vector.md'),
  payload = replace(payload, 'file:/root/projects/trading-data/docs/04_layer_03_target_state_vector.md', 'file:/root/projects/trading-data/docs/12_layer_03_target_state_vector.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-data/docs/04_layer_03_target_state_vector.md', 'file:/root/projects/trading-data/docs/12_layer_03_target_state_vector.md'),
  note = replace(note, 'file:/root/projects/trading-data/docs/04_layer_03_target_state_vector.md', 'file:/root/projects/trading-data/docs/12_layer_03_target_state_vector.md')
WHERE path LIKE '%file:/root/projects/trading-data/docs/04_layer_03_target_state_vector.md%' OR payload LIKE '%file:/root/projects/trading-data/docs/04_layer_03_target_state_vector.md%' OR applies_to LIKE '%file:/root/projects/trading-data/docs/04_layer_03_target_state_vector.md%' OR note LIKE '%file:/root/projects/trading-data/docs/04_layer_03_target_state_vector.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-data/docs/05_layer_04_event_failure_risk.md', 'trading-data/docs/13_layer_04_event_failure_risk.md'),
  payload = replace(payload, 'trading-data/docs/05_layer_04_event_failure_risk.md', 'trading-data/docs/13_layer_04_event_failure_risk.md'),
  applies_to = replace(applies_to, 'trading-data/docs/05_layer_04_event_failure_risk.md', 'trading-data/docs/13_layer_04_event_failure_risk.md'),
  note = replace(note, 'trading-data/docs/05_layer_04_event_failure_risk.md', 'trading-data/docs/13_layer_04_event_failure_risk.md')
WHERE path LIKE '%trading-data/docs/05_layer_04_event_failure_risk.md%' OR payload LIKE '%trading-data/docs/05_layer_04_event_failure_risk.md%' OR applies_to LIKE '%trading-data/docs/05_layer_04_event_failure_risk.md%' OR note LIKE '%trading-data/docs/05_layer_04_event_failure_risk.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-data/docs/05_layer_04_event_failure_risk.md', '/root/projects/trading-data/docs/13_layer_04_event_failure_risk.md'),
  payload = replace(payload, '/root/projects/trading-data/docs/05_layer_04_event_failure_risk.md', '/root/projects/trading-data/docs/13_layer_04_event_failure_risk.md'),
  applies_to = replace(applies_to, '/root/projects/trading-data/docs/05_layer_04_event_failure_risk.md', '/root/projects/trading-data/docs/13_layer_04_event_failure_risk.md'),
  note = replace(note, '/root/projects/trading-data/docs/05_layer_04_event_failure_risk.md', '/root/projects/trading-data/docs/13_layer_04_event_failure_risk.md')
WHERE path LIKE '%/root/projects/trading-data/docs/05_layer_04_event_failure_risk.md%' OR payload LIKE '%/root/projects/trading-data/docs/05_layer_04_event_failure_risk.md%' OR applies_to LIKE '%/root/projects/trading-data/docs/05_layer_04_event_failure_risk.md%' OR note LIKE '%/root/projects/trading-data/docs/05_layer_04_event_failure_risk.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-data/docs/05_layer_04_event_failure_risk.md', 'file:/root/projects/trading-data/docs/13_layer_04_event_failure_risk.md'),
  payload = replace(payload, 'file:/root/projects/trading-data/docs/05_layer_04_event_failure_risk.md', 'file:/root/projects/trading-data/docs/13_layer_04_event_failure_risk.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-data/docs/05_layer_04_event_failure_risk.md', 'file:/root/projects/trading-data/docs/13_layer_04_event_failure_risk.md'),
  note = replace(note, 'file:/root/projects/trading-data/docs/05_layer_04_event_failure_risk.md', 'file:/root/projects/trading-data/docs/13_layer_04_event_failure_risk.md')
WHERE path LIKE '%file:/root/projects/trading-data/docs/05_layer_04_event_failure_risk.md%' OR payload LIKE '%file:/root/projects/trading-data/docs/05_layer_04_event_failure_risk.md%' OR applies_to LIKE '%file:/root/projects/trading-data/docs/05_layer_04_event_failure_risk.md%' OR note LIKE '%file:/root/projects/trading-data/docs/05_layer_04_event_failure_risk.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-data/docs/06_layer_05_alpha_confidence.md', 'trading-data/docs/14_layer_05_alpha_confidence.md'),
  payload = replace(payload, 'trading-data/docs/06_layer_05_alpha_confidence.md', 'trading-data/docs/14_layer_05_alpha_confidence.md'),
  applies_to = replace(applies_to, 'trading-data/docs/06_layer_05_alpha_confidence.md', 'trading-data/docs/14_layer_05_alpha_confidence.md'),
  note = replace(note, 'trading-data/docs/06_layer_05_alpha_confidence.md', 'trading-data/docs/14_layer_05_alpha_confidence.md')
WHERE path LIKE '%trading-data/docs/06_layer_05_alpha_confidence.md%' OR payload LIKE '%trading-data/docs/06_layer_05_alpha_confidence.md%' OR applies_to LIKE '%trading-data/docs/06_layer_05_alpha_confidence.md%' OR note LIKE '%trading-data/docs/06_layer_05_alpha_confidence.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-data/docs/06_layer_05_alpha_confidence.md', '/root/projects/trading-data/docs/14_layer_05_alpha_confidence.md'),
  payload = replace(payload, '/root/projects/trading-data/docs/06_layer_05_alpha_confidence.md', '/root/projects/trading-data/docs/14_layer_05_alpha_confidence.md'),
  applies_to = replace(applies_to, '/root/projects/trading-data/docs/06_layer_05_alpha_confidence.md', '/root/projects/trading-data/docs/14_layer_05_alpha_confidence.md'),
  note = replace(note, '/root/projects/trading-data/docs/06_layer_05_alpha_confidence.md', '/root/projects/trading-data/docs/14_layer_05_alpha_confidence.md')
WHERE path LIKE '%/root/projects/trading-data/docs/06_layer_05_alpha_confidence.md%' OR payload LIKE '%/root/projects/trading-data/docs/06_layer_05_alpha_confidence.md%' OR applies_to LIKE '%/root/projects/trading-data/docs/06_layer_05_alpha_confidence.md%' OR note LIKE '%/root/projects/trading-data/docs/06_layer_05_alpha_confidence.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-data/docs/06_layer_05_alpha_confidence.md', 'file:/root/projects/trading-data/docs/14_layer_05_alpha_confidence.md'),
  payload = replace(payload, 'file:/root/projects/trading-data/docs/06_layer_05_alpha_confidence.md', 'file:/root/projects/trading-data/docs/14_layer_05_alpha_confidence.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-data/docs/06_layer_05_alpha_confidence.md', 'file:/root/projects/trading-data/docs/14_layer_05_alpha_confidence.md'),
  note = replace(note, 'file:/root/projects/trading-data/docs/06_layer_05_alpha_confidence.md', 'file:/root/projects/trading-data/docs/14_layer_05_alpha_confidence.md')
WHERE path LIKE '%file:/root/projects/trading-data/docs/06_layer_05_alpha_confidence.md%' OR payload LIKE '%file:/root/projects/trading-data/docs/06_layer_05_alpha_confidence.md%' OR applies_to LIKE '%file:/root/projects/trading-data/docs/06_layer_05_alpha_confidence.md%' OR note LIKE '%file:/root/projects/trading-data/docs/06_layer_05_alpha_confidence.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-data/docs/07_layer_06_position_projection.md', 'trading-data/docs/15_layer_06_position_projection.md'),
  payload = replace(payload, 'trading-data/docs/07_layer_06_position_projection.md', 'trading-data/docs/15_layer_06_position_projection.md'),
  applies_to = replace(applies_to, 'trading-data/docs/07_layer_06_position_projection.md', 'trading-data/docs/15_layer_06_position_projection.md'),
  note = replace(note, 'trading-data/docs/07_layer_06_position_projection.md', 'trading-data/docs/15_layer_06_position_projection.md')
WHERE path LIKE '%trading-data/docs/07_layer_06_position_projection.md%' OR payload LIKE '%trading-data/docs/07_layer_06_position_projection.md%' OR applies_to LIKE '%trading-data/docs/07_layer_06_position_projection.md%' OR note LIKE '%trading-data/docs/07_layer_06_position_projection.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-data/docs/07_layer_06_position_projection.md', '/root/projects/trading-data/docs/15_layer_06_position_projection.md'),
  payload = replace(payload, '/root/projects/trading-data/docs/07_layer_06_position_projection.md', '/root/projects/trading-data/docs/15_layer_06_position_projection.md'),
  applies_to = replace(applies_to, '/root/projects/trading-data/docs/07_layer_06_position_projection.md', '/root/projects/trading-data/docs/15_layer_06_position_projection.md'),
  note = replace(note, '/root/projects/trading-data/docs/07_layer_06_position_projection.md', '/root/projects/trading-data/docs/15_layer_06_position_projection.md')
WHERE path LIKE '%/root/projects/trading-data/docs/07_layer_06_position_projection.md%' OR payload LIKE '%/root/projects/trading-data/docs/07_layer_06_position_projection.md%' OR applies_to LIKE '%/root/projects/trading-data/docs/07_layer_06_position_projection.md%' OR note LIKE '%/root/projects/trading-data/docs/07_layer_06_position_projection.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-data/docs/07_layer_06_position_projection.md', 'file:/root/projects/trading-data/docs/15_layer_06_position_projection.md'),
  payload = replace(payload, 'file:/root/projects/trading-data/docs/07_layer_06_position_projection.md', 'file:/root/projects/trading-data/docs/15_layer_06_position_projection.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-data/docs/07_layer_06_position_projection.md', 'file:/root/projects/trading-data/docs/15_layer_06_position_projection.md'),
  note = replace(note, 'file:/root/projects/trading-data/docs/07_layer_06_position_projection.md', 'file:/root/projects/trading-data/docs/15_layer_06_position_projection.md')
WHERE path LIKE '%file:/root/projects/trading-data/docs/07_layer_06_position_projection.md%' OR payload LIKE '%file:/root/projects/trading-data/docs/07_layer_06_position_projection.md%' OR applies_to LIKE '%file:/root/projects/trading-data/docs/07_layer_06_position_projection.md%' OR note LIKE '%file:/root/projects/trading-data/docs/07_layer_06_position_projection.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-data/docs/08_layer_07_underlying_action.md', 'trading-data/docs/16_layer_07_underlying_action.md'),
  payload = replace(payload, 'trading-data/docs/08_layer_07_underlying_action.md', 'trading-data/docs/16_layer_07_underlying_action.md'),
  applies_to = replace(applies_to, 'trading-data/docs/08_layer_07_underlying_action.md', 'trading-data/docs/16_layer_07_underlying_action.md'),
  note = replace(note, 'trading-data/docs/08_layer_07_underlying_action.md', 'trading-data/docs/16_layer_07_underlying_action.md')
WHERE path LIKE '%trading-data/docs/08_layer_07_underlying_action.md%' OR payload LIKE '%trading-data/docs/08_layer_07_underlying_action.md%' OR applies_to LIKE '%trading-data/docs/08_layer_07_underlying_action.md%' OR note LIKE '%trading-data/docs/08_layer_07_underlying_action.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-data/docs/08_layer_07_underlying_action.md', '/root/projects/trading-data/docs/16_layer_07_underlying_action.md'),
  payload = replace(payload, '/root/projects/trading-data/docs/08_layer_07_underlying_action.md', '/root/projects/trading-data/docs/16_layer_07_underlying_action.md'),
  applies_to = replace(applies_to, '/root/projects/trading-data/docs/08_layer_07_underlying_action.md', '/root/projects/trading-data/docs/16_layer_07_underlying_action.md'),
  note = replace(note, '/root/projects/trading-data/docs/08_layer_07_underlying_action.md', '/root/projects/trading-data/docs/16_layer_07_underlying_action.md')
WHERE path LIKE '%/root/projects/trading-data/docs/08_layer_07_underlying_action.md%' OR payload LIKE '%/root/projects/trading-data/docs/08_layer_07_underlying_action.md%' OR applies_to LIKE '%/root/projects/trading-data/docs/08_layer_07_underlying_action.md%' OR note LIKE '%/root/projects/trading-data/docs/08_layer_07_underlying_action.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-data/docs/08_layer_07_underlying_action.md', 'file:/root/projects/trading-data/docs/16_layer_07_underlying_action.md'),
  payload = replace(payload, 'file:/root/projects/trading-data/docs/08_layer_07_underlying_action.md', 'file:/root/projects/trading-data/docs/16_layer_07_underlying_action.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-data/docs/08_layer_07_underlying_action.md', 'file:/root/projects/trading-data/docs/16_layer_07_underlying_action.md'),
  note = replace(note, 'file:/root/projects/trading-data/docs/08_layer_07_underlying_action.md', 'file:/root/projects/trading-data/docs/16_layer_07_underlying_action.md')
WHERE path LIKE '%file:/root/projects/trading-data/docs/08_layer_07_underlying_action.md%' OR payload LIKE '%file:/root/projects/trading-data/docs/08_layer_07_underlying_action.md%' OR applies_to LIKE '%file:/root/projects/trading-data/docs/08_layer_07_underlying_action.md%' OR note LIKE '%file:/root/projects/trading-data/docs/08_layer_07_underlying_action.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-data/docs/09_layer_08_trading_guidance.md', 'trading-data/docs/17_layer_08_trading_guidance.md'),
  payload = replace(payload, 'trading-data/docs/09_layer_08_trading_guidance.md', 'trading-data/docs/17_layer_08_trading_guidance.md'),
  applies_to = replace(applies_to, 'trading-data/docs/09_layer_08_trading_guidance.md', 'trading-data/docs/17_layer_08_trading_guidance.md'),
  note = replace(note, 'trading-data/docs/09_layer_08_trading_guidance.md', 'trading-data/docs/17_layer_08_trading_guidance.md')
WHERE path LIKE '%trading-data/docs/09_layer_08_trading_guidance.md%' OR payload LIKE '%trading-data/docs/09_layer_08_trading_guidance.md%' OR applies_to LIKE '%trading-data/docs/09_layer_08_trading_guidance.md%' OR note LIKE '%trading-data/docs/09_layer_08_trading_guidance.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-data/docs/09_layer_08_trading_guidance.md', '/root/projects/trading-data/docs/17_layer_08_trading_guidance.md'),
  payload = replace(payload, '/root/projects/trading-data/docs/09_layer_08_trading_guidance.md', '/root/projects/trading-data/docs/17_layer_08_trading_guidance.md'),
  applies_to = replace(applies_to, '/root/projects/trading-data/docs/09_layer_08_trading_guidance.md', '/root/projects/trading-data/docs/17_layer_08_trading_guidance.md'),
  note = replace(note, '/root/projects/trading-data/docs/09_layer_08_trading_guidance.md', '/root/projects/trading-data/docs/17_layer_08_trading_guidance.md')
WHERE path LIKE '%/root/projects/trading-data/docs/09_layer_08_trading_guidance.md%' OR payload LIKE '%/root/projects/trading-data/docs/09_layer_08_trading_guidance.md%' OR applies_to LIKE '%/root/projects/trading-data/docs/09_layer_08_trading_guidance.md%' OR note LIKE '%/root/projects/trading-data/docs/09_layer_08_trading_guidance.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-data/docs/09_layer_08_trading_guidance.md', 'file:/root/projects/trading-data/docs/17_layer_08_trading_guidance.md'),
  payload = replace(payload, 'file:/root/projects/trading-data/docs/09_layer_08_trading_guidance.md', 'file:/root/projects/trading-data/docs/17_layer_08_trading_guidance.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-data/docs/09_layer_08_trading_guidance.md', 'file:/root/projects/trading-data/docs/17_layer_08_trading_guidance.md'),
  note = replace(note, 'file:/root/projects/trading-data/docs/09_layer_08_trading_guidance.md', 'file:/root/projects/trading-data/docs/17_layer_08_trading_guidance.md')
WHERE path LIKE '%file:/root/projects/trading-data/docs/09_layer_08_trading_guidance.md%' OR payload LIKE '%file:/root/projects/trading-data/docs/09_layer_08_trading_guidance.md%' OR applies_to LIKE '%file:/root/projects/trading-data/docs/09_layer_08_trading_guidance.md%' OR note LIKE '%file:/root/projects/trading-data/docs/09_layer_08_trading_guidance.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-data/docs/10_layer_09_event_risk_governor.md', 'trading-data/docs/18_layer_09_event_risk_governor.md'),
  payload = replace(payload, 'trading-data/docs/10_layer_09_event_risk_governor.md', 'trading-data/docs/18_layer_09_event_risk_governor.md'),
  applies_to = replace(applies_to, 'trading-data/docs/10_layer_09_event_risk_governor.md', 'trading-data/docs/18_layer_09_event_risk_governor.md'),
  note = replace(note, 'trading-data/docs/10_layer_09_event_risk_governor.md', 'trading-data/docs/18_layer_09_event_risk_governor.md')
WHERE path LIKE '%trading-data/docs/10_layer_09_event_risk_governor.md%' OR payload LIKE '%trading-data/docs/10_layer_09_event_risk_governor.md%' OR applies_to LIKE '%trading-data/docs/10_layer_09_event_risk_governor.md%' OR note LIKE '%trading-data/docs/10_layer_09_event_risk_governor.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-data/docs/10_layer_09_event_risk_governor.md', '/root/projects/trading-data/docs/18_layer_09_event_risk_governor.md'),
  payload = replace(payload, '/root/projects/trading-data/docs/10_layer_09_event_risk_governor.md', '/root/projects/trading-data/docs/18_layer_09_event_risk_governor.md'),
  applies_to = replace(applies_to, '/root/projects/trading-data/docs/10_layer_09_event_risk_governor.md', '/root/projects/trading-data/docs/18_layer_09_event_risk_governor.md'),
  note = replace(note, '/root/projects/trading-data/docs/10_layer_09_event_risk_governor.md', '/root/projects/trading-data/docs/18_layer_09_event_risk_governor.md')
WHERE path LIKE '%/root/projects/trading-data/docs/10_layer_09_event_risk_governor.md%' OR payload LIKE '%/root/projects/trading-data/docs/10_layer_09_event_risk_governor.md%' OR applies_to LIKE '%/root/projects/trading-data/docs/10_layer_09_event_risk_governor.md%' OR note LIKE '%/root/projects/trading-data/docs/10_layer_09_event_risk_governor.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-data/docs/10_layer_09_event_risk_governor.md', 'file:/root/projects/trading-data/docs/18_layer_09_event_risk_governor.md'),
  payload = replace(payload, 'file:/root/projects/trading-data/docs/10_layer_09_event_risk_governor.md', 'file:/root/projects/trading-data/docs/18_layer_09_event_risk_governor.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-data/docs/10_layer_09_event_risk_governor.md', 'file:/root/projects/trading-data/docs/18_layer_09_event_risk_governor.md'),
  note = replace(note, 'file:/root/projects/trading-data/docs/10_layer_09_event_risk_governor.md', 'file:/root/projects/trading-data/docs/18_layer_09_event_risk_governor.md')
WHERE path LIKE '%file:/root/projects/trading-data/docs/10_layer_09_event_risk_governor.md%' OR payload LIKE '%file:/root/projects/trading-data/docs/10_layer_09_event_risk_governor.md%' OR applies_to LIKE '%file:/root/projects/trading-data/docs/10_layer_09_event_risk_governor.md%' OR note LIKE '%file:/root/projects/trading-data/docs/10_layer_09_event_risk_governor.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-data/docs/12_data_feed.md', 'trading-data/docs/20_data_feed.md'),
  payload = replace(payload, 'trading-data/docs/12_data_feed.md', 'trading-data/docs/20_data_feed.md'),
  applies_to = replace(applies_to, 'trading-data/docs/12_data_feed.md', 'trading-data/docs/20_data_feed.md'),
  note = replace(note, 'trading-data/docs/12_data_feed.md', 'trading-data/docs/20_data_feed.md')
WHERE path LIKE '%trading-data/docs/12_data_feed.md%' OR payload LIKE '%trading-data/docs/12_data_feed.md%' OR applies_to LIKE '%trading-data/docs/12_data_feed.md%' OR note LIKE '%trading-data/docs/12_data_feed.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-data/docs/12_data_feed.md', '/root/projects/trading-data/docs/20_data_feed.md'),
  payload = replace(payload, '/root/projects/trading-data/docs/12_data_feed.md', '/root/projects/trading-data/docs/20_data_feed.md'),
  applies_to = replace(applies_to, '/root/projects/trading-data/docs/12_data_feed.md', '/root/projects/trading-data/docs/20_data_feed.md'),
  note = replace(note, '/root/projects/trading-data/docs/12_data_feed.md', '/root/projects/trading-data/docs/20_data_feed.md')
WHERE path LIKE '%/root/projects/trading-data/docs/12_data_feed.md%' OR payload LIKE '%/root/projects/trading-data/docs/12_data_feed.md%' OR applies_to LIKE '%/root/projects/trading-data/docs/12_data_feed.md%' OR note LIKE '%/root/projects/trading-data/docs/12_data_feed.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-data/docs/12_data_feed.md', 'file:/root/projects/trading-data/docs/20_data_feed.md'),
  payload = replace(payload, 'file:/root/projects/trading-data/docs/12_data_feed.md', 'file:/root/projects/trading-data/docs/20_data_feed.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-data/docs/12_data_feed.md', 'file:/root/projects/trading-data/docs/20_data_feed.md'),
  note = replace(note, 'file:/root/projects/trading-data/docs/12_data_feed.md', 'file:/root/projects/trading-data/docs/20_data_feed.md')
WHERE path LIKE '%file:/root/projects/trading-data/docs/12_data_feed.md%' OR payload LIKE '%file:/root/projects/trading-data/docs/12_data_feed.md%' OR applies_to LIKE '%file:/root/projects/trading-data/docs/12_data_feed.md%' OR note LIKE '%file:/root/projects/trading-data/docs/12_data_feed.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-data/docs/13_api_templates.md', 'trading-data/docs/21_api_templates.md'),
  payload = replace(payload, 'trading-data/docs/13_api_templates.md', 'trading-data/docs/21_api_templates.md'),
  applies_to = replace(applies_to, 'trading-data/docs/13_api_templates.md', 'trading-data/docs/21_api_templates.md'),
  note = replace(note, 'trading-data/docs/13_api_templates.md', 'trading-data/docs/21_api_templates.md')
WHERE path LIKE '%trading-data/docs/13_api_templates.md%' OR payload LIKE '%trading-data/docs/13_api_templates.md%' OR applies_to LIKE '%trading-data/docs/13_api_templates.md%' OR note LIKE '%trading-data/docs/13_api_templates.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-data/docs/13_api_templates.md', '/root/projects/trading-data/docs/21_api_templates.md'),
  payload = replace(payload, '/root/projects/trading-data/docs/13_api_templates.md', '/root/projects/trading-data/docs/21_api_templates.md'),
  applies_to = replace(applies_to, '/root/projects/trading-data/docs/13_api_templates.md', '/root/projects/trading-data/docs/21_api_templates.md'),
  note = replace(note, '/root/projects/trading-data/docs/13_api_templates.md', '/root/projects/trading-data/docs/21_api_templates.md')
WHERE path LIKE '%/root/projects/trading-data/docs/13_api_templates.md%' OR payload LIKE '%/root/projects/trading-data/docs/13_api_templates.md%' OR applies_to LIKE '%/root/projects/trading-data/docs/13_api_templates.md%' OR note LIKE '%/root/projects/trading-data/docs/13_api_templates.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-data/docs/13_api_templates.md', 'file:/root/projects/trading-data/docs/21_api_templates.md'),
  payload = replace(payload, 'file:/root/projects/trading-data/docs/13_api_templates.md', 'file:/root/projects/trading-data/docs/21_api_templates.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-data/docs/13_api_templates.md', 'file:/root/projects/trading-data/docs/21_api_templates.md'),
  note = replace(note, 'file:/root/projects/trading-data/docs/13_api_templates.md', 'file:/root/projects/trading-data/docs/21_api_templates.md')
WHERE path LIKE '%file:/root/projects/trading-data/docs/13_api_templates.md%' OR payload LIKE '%file:/root/projects/trading-data/docs/13_api_templates.md%' OR applies_to LIKE '%file:/root/projects/trading-data/docs/13_api_templates.md%' OR note LIKE '%file:/root/projects/trading-data/docs/13_api_templates.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-data/docs/14_feed_availability.md', 'trading-data/docs/22_feed_availability.md'),
  payload = replace(payload, 'trading-data/docs/14_feed_availability.md', 'trading-data/docs/22_feed_availability.md'),
  applies_to = replace(applies_to, 'trading-data/docs/14_feed_availability.md', 'trading-data/docs/22_feed_availability.md'),
  note = replace(note, 'trading-data/docs/14_feed_availability.md', 'trading-data/docs/22_feed_availability.md')
WHERE path LIKE '%trading-data/docs/14_feed_availability.md%' OR payload LIKE '%trading-data/docs/14_feed_availability.md%' OR applies_to LIKE '%trading-data/docs/14_feed_availability.md%' OR note LIKE '%trading-data/docs/14_feed_availability.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-data/docs/14_feed_availability.md', '/root/projects/trading-data/docs/22_feed_availability.md'),
  payload = replace(payload, '/root/projects/trading-data/docs/14_feed_availability.md', '/root/projects/trading-data/docs/22_feed_availability.md'),
  applies_to = replace(applies_to, '/root/projects/trading-data/docs/14_feed_availability.md', '/root/projects/trading-data/docs/22_feed_availability.md'),
  note = replace(note, '/root/projects/trading-data/docs/14_feed_availability.md', '/root/projects/trading-data/docs/22_feed_availability.md')
WHERE path LIKE '%/root/projects/trading-data/docs/14_feed_availability.md%' OR payload LIKE '%/root/projects/trading-data/docs/14_feed_availability.md%' OR applies_to LIKE '%/root/projects/trading-data/docs/14_feed_availability.md%' OR note LIKE '%/root/projects/trading-data/docs/14_feed_availability.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-data/docs/14_feed_availability.md', 'file:/root/projects/trading-data/docs/22_feed_availability.md'),
  payload = replace(payload, 'file:/root/projects/trading-data/docs/14_feed_availability.md', 'file:/root/projects/trading-data/docs/22_feed_availability.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-data/docs/14_feed_availability.md', 'file:/root/projects/trading-data/docs/22_feed_availability.md'),
  note = replace(note, 'file:/root/projects/trading-data/docs/14_feed_availability.md', 'file:/root/projects/trading-data/docs/22_feed_availability.md')
WHERE path LIKE '%file:/root/projects/trading-data/docs/14_feed_availability.md%' OR payload LIKE '%file:/root/projects/trading-data/docs/14_feed_availability.md%' OR applies_to LIKE '%file:/root/projects/trading-data/docs/14_feed_availability.md%' OR note LIKE '%file:/root/projects/trading-data/docs/14_feed_availability.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-data/docs/15_model_inputs.md', 'trading-data/docs/30_model_inputs.md'),
  payload = replace(payload, 'trading-data/docs/15_model_inputs.md', 'trading-data/docs/30_model_inputs.md'),
  applies_to = replace(applies_to, 'trading-data/docs/15_model_inputs.md', 'trading-data/docs/30_model_inputs.md'),
  note = replace(note, 'trading-data/docs/15_model_inputs.md', 'trading-data/docs/30_model_inputs.md')
WHERE path LIKE '%trading-data/docs/15_model_inputs.md%' OR payload LIKE '%trading-data/docs/15_model_inputs.md%' OR applies_to LIKE '%trading-data/docs/15_model_inputs.md%' OR note LIKE '%trading-data/docs/15_model_inputs.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-data/docs/15_model_inputs.md', '/root/projects/trading-data/docs/30_model_inputs.md'),
  payload = replace(payload, '/root/projects/trading-data/docs/15_model_inputs.md', '/root/projects/trading-data/docs/30_model_inputs.md'),
  applies_to = replace(applies_to, '/root/projects/trading-data/docs/15_model_inputs.md', '/root/projects/trading-data/docs/30_model_inputs.md'),
  note = replace(note, '/root/projects/trading-data/docs/15_model_inputs.md', '/root/projects/trading-data/docs/30_model_inputs.md')
WHERE path LIKE '%/root/projects/trading-data/docs/15_model_inputs.md%' OR payload LIKE '%/root/projects/trading-data/docs/15_model_inputs.md%' OR applies_to LIKE '%/root/projects/trading-data/docs/15_model_inputs.md%' OR note LIKE '%/root/projects/trading-data/docs/15_model_inputs.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-data/docs/15_model_inputs.md', 'file:/root/projects/trading-data/docs/30_model_inputs.md'),
  payload = replace(payload, 'file:/root/projects/trading-data/docs/15_model_inputs.md', 'file:/root/projects/trading-data/docs/30_model_inputs.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-data/docs/15_model_inputs.md', 'file:/root/projects/trading-data/docs/30_model_inputs.md'),
  note = replace(note, 'file:/root/projects/trading-data/docs/15_model_inputs.md', 'file:/root/projects/trading-data/docs/30_model_inputs.md')
WHERE path LIKE '%file:/root/projects/trading-data/docs/15_model_inputs.md%' OR payload LIKE '%file:/root/projects/trading-data/docs/15_model_inputs.md%' OR applies_to LIKE '%file:/root/projects/trading-data/docs/15_model_inputs.md%' OR note LIKE '%file:/root/projects/trading-data/docs/15_model_inputs.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-data/docs/17_production_hardening.md', 'trading-data/docs/40_production_hardening.md'),
  payload = replace(payload, 'trading-data/docs/17_production_hardening.md', 'trading-data/docs/40_production_hardening.md'),
  applies_to = replace(applies_to, 'trading-data/docs/17_production_hardening.md', 'trading-data/docs/40_production_hardening.md'),
  note = replace(note, 'trading-data/docs/17_production_hardening.md', 'trading-data/docs/40_production_hardening.md')
WHERE path LIKE '%trading-data/docs/17_production_hardening.md%' OR payload LIKE '%trading-data/docs/17_production_hardening.md%' OR applies_to LIKE '%trading-data/docs/17_production_hardening.md%' OR note LIKE '%trading-data/docs/17_production_hardening.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-data/docs/17_production_hardening.md', '/root/projects/trading-data/docs/40_production_hardening.md'),
  payload = replace(payload, '/root/projects/trading-data/docs/17_production_hardening.md', '/root/projects/trading-data/docs/40_production_hardening.md'),
  applies_to = replace(applies_to, '/root/projects/trading-data/docs/17_production_hardening.md', '/root/projects/trading-data/docs/40_production_hardening.md'),
  note = replace(note, '/root/projects/trading-data/docs/17_production_hardening.md', '/root/projects/trading-data/docs/40_production_hardening.md')
WHERE path LIKE '%/root/projects/trading-data/docs/17_production_hardening.md%' OR payload LIKE '%/root/projects/trading-data/docs/17_production_hardening.md%' OR applies_to LIKE '%/root/projects/trading-data/docs/17_production_hardening.md%' OR note LIKE '%/root/projects/trading-data/docs/17_production_hardening.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-data/docs/17_production_hardening.md', 'file:/root/projects/trading-data/docs/40_production_hardening.md'),
  payload = replace(payload, 'file:/root/projects/trading-data/docs/17_production_hardening.md', 'file:/root/projects/trading-data/docs/40_production_hardening.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-data/docs/17_production_hardening.md', 'file:/root/projects/trading-data/docs/40_production_hardening.md'),
  note = replace(note, 'file:/root/projects/trading-data/docs/17_production_hardening.md', 'file:/root/projects/trading-data/docs/40_production_hardening.md')
WHERE path LIKE '%file:/root/projects/trading-data/docs/17_production_hardening.md%' OR payload LIKE '%file:/root/projects/trading-data/docs/17_production_hardening.md%' OR applies_to LIKE '%file:/root/projects/trading-data/docs/17_production_hardening.md%' OR note LIKE '%file:/root/projects/trading-data/docs/17_production_hardening.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-model/docs/11_system_model_architecture.md', 'trading-model/docs/02_architecture.md'),
  payload = replace(payload, 'trading-model/docs/11_system_model_architecture.md', 'trading-model/docs/02_architecture.md'),
  applies_to = replace(applies_to, 'trading-model/docs/11_system_model_architecture.md', 'trading-model/docs/02_architecture.md'),
  note = replace(note, 'trading-model/docs/11_system_model_architecture.md', 'trading-model/docs/02_architecture.md')
WHERE path LIKE '%trading-model/docs/11_system_model_architecture.md%' OR payload LIKE '%trading-model/docs/11_system_model_architecture.md%' OR applies_to LIKE '%trading-model/docs/11_system_model_architecture.md%' OR note LIKE '%trading-model/docs/11_system_model_architecture.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-model/docs/11_system_model_architecture.md', '/root/projects/trading-model/docs/02_architecture.md'),
  payload = replace(payload, '/root/projects/trading-model/docs/11_system_model_architecture.md', '/root/projects/trading-model/docs/02_architecture.md'),
  applies_to = replace(applies_to, '/root/projects/trading-model/docs/11_system_model_architecture.md', '/root/projects/trading-model/docs/02_architecture.md'),
  note = replace(note, '/root/projects/trading-model/docs/11_system_model_architecture.md', '/root/projects/trading-model/docs/02_architecture.md')
WHERE path LIKE '%/root/projects/trading-model/docs/11_system_model_architecture.md%' OR payload LIKE '%/root/projects/trading-model/docs/11_system_model_architecture.md%' OR applies_to LIKE '%/root/projects/trading-model/docs/11_system_model_architecture.md%' OR note LIKE '%/root/projects/trading-model/docs/11_system_model_architecture.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-model/docs/11_system_model_architecture.md', 'file:/root/projects/trading-model/docs/02_architecture.md'),
  payload = replace(payload, 'file:/root/projects/trading-model/docs/11_system_model_architecture.md', 'file:/root/projects/trading-model/docs/02_architecture.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-model/docs/11_system_model_architecture.md', 'file:/root/projects/trading-model/docs/02_architecture.md'),
  note = replace(note, 'file:/root/projects/trading-model/docs/11_system_model_architecture.md', 'file:/root/projects/trading-model/docs/02_architecture.md')
WHERE path LIKE '%file:/root/projects/trading-model/docs/11_system_model_architecture.md%' OR payload LIKE '%file:/root/projects/trading-model/docs/11_system_model_architecture.md%' OR applies_to LIKE '%file:/root/projects/trading-model/docs/11_system_model_architecture.md%' OR note LIKE '%file:/root/projects/trading-model/docs/11_system_model_architecture.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-model/docs/15_model_stack_acceptance.md', 'trading-model/docs/03_contracts.md'),
  payload = replace(payload, 'trading-model/docs/15_model_stack_acceptance.md', 'trading-model/docs/03_contracts.md'),
  applies_to = replace(applies_to, 'trading-model/docs/15_model_stack_acceptance.md', 'trading-model/docs/03_contracts.md'),
  note = replace(note, 'trading-model/docs/15_model_stack_acceptance.md', 'trading-model/docs/03_contracts.md')
WHERE path LIKE '%trading-model/docs/15_model_stack_acceptance.md%' OR payload LIKE '%trading-model/docs/15_model_stack_acceptance.md%' OR applies_to LIKE '%trading-model/docs/15_model_stack_acceptance.md%' OR note LIKE '%trading-model/docs/15_model_stack_acceptance.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-model/docs/15_model_stack_acceptance.md', '/root/projects/trading-model/docs/03_contracts.md'),
  payload = replace(payload, '/root/projects/trading-model/docs/15_model_stack_acceptance.md', '/root/projects/trading-model/docs/03_contracts.md'),
  applies_to = replace(applies_to, '/root/projects/trading-model/docs/15_model_stack_acceptance.md', '/root/projects/trading-model/docs/03_contracts.md'),
  note = replace(note, '/root/projects/trading-model/docs/15_model_stack_acceptance.md', '/root/projects/trading-model/docs/03_contracts.md')
WHERE path LIKE '%/root/projects/trading-model/docs/15_model_stack_acceptance.md%' OR payload LIKE '%/root/projects/trading-model/docs/15_model_stack_acceptance.md%' OR applies_to LIKE '%/root/projects/trading-model/docs/15_model_stack_acceptance.md%' OR note LIKE '%/root/projects/trading-model/docs/15_model_stack_acceptance.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-model/docs/15_model_stack_acceptance.md', 'file:/root/projects/trading-model/docs/03_contracts.md'),
  payload = replace(payload, 'file:/root/projects/trading-model/docs/15_model_stack_acceptance.md', 'file:/root/projects/trading-model/docs/03_contracts.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-model/docs/15_model_stack_acceptance.md', 'file:/root/projects/trading-model/docs/03_contracts.md'),
  note = replace(note, 'file:/root/projects/trading-model/docs/15_model_stack_acceptance.md', 'file:/root/projects/trading-model/docs/03_contracts.md')
WHERE path LIKE '%file:/root/projects/trading-model/docs/15_model_stack_acceptance.md%' OR payload LIKE '%file:/root/projects/trading-model/docs/15_model_stack_acceptance.md%' OR applies_to LIKE '%file:/root/projects/trading-model/docs/15_model_stack_acceptance.md%' OR note LIKE '%file:/root/projects/trading-model/docs/15_model_stack_acceptance.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-model/docs/80_task.md', 'trading-model/docs/04_task.md'),
  payload = replace(payload, 'trading-model/docs/80_task.md', 'trading-model/docs/04_task.md'),
  applies_to = replace(applies_to, 'trading-model/docs/80_task.md', 'trading-model/docs/04_task.md'),
  note = replace(note, 'trading-model/docs/80_task.md', 'trading-model/docs/04_task.md')
WHERE path LIKE '%trading-model/docs/80_task.md%' OR payload LIKE '%trading-model/docs/80_task.md%' OR applies_to LIKE '%trading-model/docs/80_task.md%' OR note LIKE '%trading-model/docs/80_task.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-model/docs/80_task.md', '/root/projects/trading-model/docs/04_task.md'),
  payload = replace(payload, '/root/projects/trading-model/docs/80_task.md', '/root/projects/trading-model/docs/04_task.md'),
  applies_to = replace(applies_to, '/root/projects/trading-model/docs/80_task.md', '/root/projects/trading-model/docs/04_task.md'),
  note = replace(note, '/root/projects/trading-model/docs/80_task.md', '/root/projects/trading-model/docs/04_task.md')
WHERE path LIKE '%/root/projects/trading-model/docs/80_task.md%' OR payload LIKE '%/root/projects/trading-model/docs/80_task.md%' OR applies_to LIKE '%/root/projects/trading-model/docs/80_task.md%' OR note LIKE '%/root/projects/trading-model/docs/80_task.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-model/docs/80_task.md', 'file:/root/projects/trading-model/docs/04_task.md'),
  payload = replace(payload, 'file:/root/projects/trading-model/docs/80_task.md', 'file:/root/projects/trading-model/docs/04_task.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-model/docs/80_task.md', 'file:/root/projects/trading-model/docs/04_task.md'),
  note = replace(note, 'file:/root/projects/trading-model/docs/80_task.md', 'file:/root/projects/trading-model/docs/04_task.md')
WHERE path LIKE '%file:/root/projects/trading-model/docs/80_task.md%' OR payload LIKE '%file:/root/projects/trading-model/docs/80_task.md%' OR applies_to LIKE '%file:/root/projects/trading-model/docs/80_task.md%' OR note LIKE '%file:/root/projects/trading-model/docs/80_task.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-model/docs/81_decision.md', 'trading-model/docs/05_decision.md'),
  payload = replace(payload, 'trading-model/docs/81_decision.md', 'trading-model/docs/05_decision.md'),
  applies_to = replace(applies_to, 'trading-model/docs/81_decision.md', 'trading-model/docs/05_decision.md'),
  note = replace(note, 'trading-model/docs/81_decision.md', 'trading-model/docs/05_decision.md')
WHERE path LIKE '%trading-model/docs/81_decision.md%' OR payload LIKE '%trading-model/docs/81_decision.md%' OR applies_to LIKE '%trading-model/docs/81_decision.md%' OR note LIKE '%trading-model/docs/81_decision.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-model/docs/81_decision.md', '/root/projects/trading-model/docs/05_decision.md'),
  payload = replace(payload, '/root/projects/trading-model/docs/81_decision.md', '/root/projects/trading-model/docs/05_decision.md'),
  applies_to = replace(applies_to, '/root/projects/trading-model/docs/81_decision.md', '/root/projects/trading-model/docs/05_decision.md'),
  note = replace(note, '/root/projects/trading-model/docs/81_decision.md', '/root/projects/trading-model/docs/05_decision.md')
WHERE path LIKE '%/root/projects/trading-model/docs/81_decision.md%' OR payload LIKE '%/root/projects/trading-model/docs/81_decision.md%' OR applies_to LIKE '%/root/projects/trading-model/docs/81_decision.md%' OR note LIKE '%/root/projects/trading-model/docs/81_decision.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-model/docs/81_decision.md', 'file:/root/projects/trading-model/docs/05_decision.md'),
  payload = replace(payload, 'file:/root/projects/trading-model/docs/81_decision.md', 'file:/root/projects/trading-model/docs/05_decision.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-model/docs/81_decision.md', 'file:/root/projects/trading-model/docs/05_decision.md'),
  note = replace(note, 'file:/root/projects/trading-model/docs/81_decision.md', 'file:/root/projects/trading-model/docs/05_decision.md')
WHERE path LIKE '%file:/root/projects/trading-model/docs/81_decision.md%' OR payload LIKE '%file:/root/projects/trading-model/docs/81_decision.md%' OR applies_to LIKE '%file:/root/projects/trading-model/docs/81_decision.md%' OR note LIKE '%file:/root/projects/trading-model/docs/81_decision.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-model/docs/82_memory.md', 'trading-model/docs/06_memory.md'),
  payload = replace(payload, 'trading-model/docs/82_memory.md', 'trading-model/docs/06_memory.md'),
  applies_to = replace(applies_to, 'trading-model/docs/82_memory.md', 'trading-model/docs/06_memory.md'),
  note = replace(note, 'trading-model/docs/82_memory.md', 'trading-model/docs/06_memory.md')
WHERE path LIKE '%trading-model/docs/82_memory.md%' OR payload LIKE '%trading-model/docs/82_memory.md%' OR applies_to LIKE '%trading-model/docs/82_memory.md%' OR note LIKE '%trading-model/docs/82_memory.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-model/docs/82_memory.md', '/root/projects/trading-model/docs/06_memory.md'),
  payload = replace(payload, '/root/projects/trading-model/docs/82_memory.md', '/root/projects/trading-model/docs/06_memory.md'),
  applies_to = replace(applies_to, '/root/projects/trading-model/docs/82_memory.md', '/root/projects/trading-model/docs/06_memory.md'),
  note = replace(note, '/root/projects/trading-model/docs/82_memory.md', '/root/projects/trading-model/docs/06_memory.md')
WHERE path LIKE '%/root/projects/trading-model/docs/82_memory.md%' OR payload LIKE '%/root/projects/trading-model/docs/82_memory.md%' OR applies_to LIKE '%/root/projects/trading-model/docs/82_memory.md%' OR note LIKE '%/root/projects/trading-model/docs/82_memory.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-model/docs/82_memory.md', 'file:/root/projects/trading-model/docs/06_memory.md'),
  payload = replace(payload, 'file:/root/projects/trading-model/docs/82_memory.md', 'file:/root/projects/trading-model/docs/06_memory.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-model/docs/82_memory.md', 'file:/root/projects/trading-model/docs/06_memory.md'),
  note = replace(note, 'file:/root/projects/trading-model/docs/82_memory.md', 'file:/root/projects/trading-model/docs/06_memory.md')
WHERE path LIKE '%file:/root/projects/trading-model/docs/82_memory.md%' OR payload LIKE '%file:/root/projects/trading-model/docs/82_memory.md%' OR applies_to LIKE '%file:/root/projects/trading-model/docs/82_memory.md%' OR note LIKE '%file:/root/projects/trading-model/docs/82_memory.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-model/docs/02_layer_01_market_regime.md', 'trading-model/docs/10_layer_01_market_regime.md'),
  payload = replace(payload, 'trading-model/docs/02_layer_01_market_regime.md', 'trading-model/docs/10_layer_01_market_regime.md'),
  applies_to = replace(applies_to, 'trading-model/docs/02_layer_01_market_regime.md', 'trading-model/docs/10_layer_01_market_regime.md'),
  note = replace(note, 'trading-model/docs/02_layer_01_market_regime.md', 'trading-model/docs/10_layer_01_market_regime.md')
WHERE path LIKE '%trading-model/docs/02_layer_01_market_regime.md%' OR payload LIKE '%trading-model/docs/02_layer_01_market_regime.md%' OR applies_to LIKE '%trading-model/docs/02_layer_01_market_regime.md%' OR note LIKE '%trading-model/docs/02_layer_01_market_regime.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-model/docs/02_layer_01_market_regime.md', '/root/projects/trading-model/docs/10_layer_01_market_regime.md'),
  payload = replace(payload, '/root/projects/trading-model/docs/02_layer_01_market_regime.md', '/root/projects/trading-model/docs/10_layer_01_market_regime.md'),
  applies_to = replace(applies_to, '/root/projects/trading-model/docs/02_layer_01_market_regime.md', '/root/projects/trading-model/docs/10_layer_01_market_regime.md'),
  note = replace(note, '/root/projects/trading-model/docs/02_layer_01_market_regime.md', '/root/projects/trading-model/docs/10_layer_01_market_regime.md')
WHERE path LIKE '%/root/projects/trading-model/docs/02_layer_01_market_regime.md%' OR payload LIKE '%/root/projects/trading-model/docs/02_layer_01_market_regime.md%' OR applies_to LIKE '%/root/projects/trading-model/docs/02_layer_01_market_regime.md%' OR note LIKE '%/root/projects/trading-model/docs/02_layer_01_market_regime.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-model/docs/02_layer_01_market_regime.md', 'file:/root/projects/trading-model/docs/10_layer_01_market_regime.md'),
  payload = replace(payload, 'file:/root/projects/trading-model/docs/02_layer_01_market_regime.md', 'file:/root/projects/trading-model/docs/10_layer_01_market_regime.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-model/docs/02_layer_01_market_regime.md', 'file:/root/projects/trading-model/docs/10_layer_01_market_regime.md'),
  note = replace(note, 'file:/root/projects/trading-model/docs/02_layer_01_market_regime.md', 'file:/root/projects/trading-model/docs/10_layer_01_market_regime.md')
WHERE path LIKE '%file:/root/projects/trading-model/docs/02_layer_01_market_regime.md%' OR payload LIKE '%file:/root/projects/trading-model/docs/02_layer_01_market_regime.md%' OR applies_to LIKE '%file:/root/projects/trading-model/docs/02_layer_01_market_regime.md%' OR note LIKE '%file:/root/projects/trading-model/docs/02_layer_01_market_regime.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-model/docs/03_layer_02_sector_context.md', 'trading-model/docs/11_layer_02_sector_context.md'),
  payload = replace(payload, 'trading-model/docs/03_layer_02_sector_context.md', 'trading-model/docs/11_layer_02_sector_context.md'),
  applies_to = replace(applies_to, 'trading-model/docs/03_layer_02_sector_context.md', 'trading-model/docs/11_layer_02_sector_context.md'),
  note = replace(note, 'trading-model/docs/03_layer_02_sector_context.md', 'trading-model/docs/11_layer_02_sector_context.md')
WHERE path LIKE '%trading-model/docs/03_layer_02_sector_context.md%' OR payload LIKE '%trading-model/docs/03_layer_02_sector_context.md%' OR applies_to LIKE '%trading-model/docs/03_layer_02_sector_context.md%' OR note LIKE '%trading-model/docs/03_layer_02_sector_context.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-model/docs/03_layer_02_sector_context.md', '/root/projects/trading-model/docs/11_layer_02_sector_context.md'),
  payload = replace(payload, '/root/projects/trading-model/docs/03_layer_02_sector_context.md', '/root/projects/trading-model/docs/11_layer_02_sector_context.md'),
  applies_to = replace(applies_to, '/root/projects/trading-model/docs/03_layer_02_sector_context.md', '/root/projects/trading-model/docs/11_layer_02_sector_context.md'),
  note = replace(note, '/root/projects/trading-model/docs/03_layer_02_sector_context.md', '/root/projects/trading-model/docs/11_layer_02_sector_context.md')
WHERE path LIKE '%/root/projects/trading-model/docs/03_layer_02_sector_context.md%' OR payload LIKE '%/root/projects/trading-model/docs/03_layer_02_sector_context.md%' OR applies_to LIKE '%/root/projects/trading-model/docs/03_layer_02_sector_context.md%' OR note LIKE '%/root/projects/trading-model/docs/03_layer_02_sector_context.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-model/docs/03_layer_02_sector_context.md', 'file:/root/projects/trading-model/docs/11_layer_02_sector_context.md'),
  payload = replace(payload, 'file:/root/projects/trading-model/docs/03_layer_02_sector_context.md', 'file:/root/projects/trading-model/docs/11_layer_02_sector_context.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-model/docs/03_layer_02_sector_context.md', 'file:/root/projects/trading-model/docs/11_layer_02_sector_context.md'),
  note = replace(note, 'file:/root/projects/trading-model/docs/03_layer_02_sector_context.md', 'file:/root/projects/trading-model/docs/11_layer_02_sector_context.md')
WHERE path LIKE '%file:/root/projects/trading-model/docs/03_layer_02_sector_context.md%' OR payload LIKE '%file:/root/projects/trading-model/docs/03_layer_02_sector_context.md%' OR applies_to LIKE '%file:/root/projects/trading-model/docs/03_layer_02_sector_context.md%' OR note LIKE '%file:/root/projects/trading-model/docs/03_layer_02_sector_context.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-model/docs/04_layer_03_target_state_vector.md', 'trading-model/docs/12_layer_03_target_state_vector.md'),
  payload = replace(payload, 'trading-model/docs/04_layer_03_target_state_vector.md', 'trading-model/docs/12_layer_03_target_state_vector.md'),
  applies_to = replace(applies_to, 'trading-model/docs/04_layer_03_target_state_vector.md', 'trading-model/docs/12_layer_03_target_state_vector.md'),
  note = replace(note, 'trading-model/docs/04_layer_03_target_state_vector.md', 'trading-model/docs/12_layer_03_target_state_vector.md')
WHERE path LIKE '%trading-model/docs/04_layer_03_target_state_vector.md%' OR payload LIKE '%trading-model/docs/04_layer_03_target_state_vector.md%' OR applies_to LIKE '%trading-model/docs/04_layer_03_target_state_vector.md%' OR note LIKE '%trading-model/docs/04_layer_03_target_state_vector.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-model/docs/04_layer_03_target_state_vector.md', '/root/projects/trading-model/docs/12_layer_03_target_state_vector.md'),
  payload = replace(payload, '/root/projects/trading-model/docs/04_layer_03_target_state_vector.md', '/root/projects/trading-model/docs/12_layer_03_target_state_vector.md'),
  applies_to = replace(applies_to, '/root/projects/trading-model/docs/04_layer_03_target_state_vector.md', '/root/projects/trading-model/docs/12_layer_03_target_state_vector.md'),
  note = replace(note, '/root/projects/trading-model/docs/04_layer_03_target_state_vector.md', '/root/projects/trading-model/docs/12_layer_03_target_state_vector.md')
WHERE path LIKE '%/root/projects/trading-model/docs/04_layer_03_target_state_vector.md%' OR payload LIKE '%/root/projects/trading-model/docs/04_layer_03_target_state_vector.md%' OR applies_to LIKE '%/root/projects/trading-model/docs/04_layer_03_target_state_vector.md%' OR note LIKE '%/root/projects/trading-model/docs/04_layer_03_target_state_vector.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-model/docs/04_layer_03_target_state_vector.md', 'file:/root/projects/trading-model/docs/12_layer_03_target_state_vector.md'),
  payload = replace(payload, 'file:/root/projects/trading-model/docs/04_layer_03_target_state_vector.md', 'file:/root/projects/trading-model/docs/12_layer_03_target_state_vector.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-model/docs/04_layer_03_target_state_vector.md', 'file:/root/projects/trading-model/docs/12_layer_03_target_state_vector.md'),
  note = replace(note, 'file:/root/projects/trading-model/docs/04_layer_03_target_state_vector.md', 'file:/root/projects/trading-model/docs/12_layer_03_target_state_vector.md')
WHERE path LIKE '%file:/root/projects/trading-model/docs/04_layer_03_target_state_vector.md%' OR payload LIKE '%file:/root/projects/trading-model/docs/04_layer_03_target_state_vector.md%' OR applies_to LIKE '%file:/root/projects/trading-model/docs/04_layer_03_target_state_vector.md%' OR note LIKE '%file:/root/projects/trading-model/docs/04_layer_03_target_state_vector.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-model/docs/05_layer_04_event_failure_risk.md', 'trading-model/docs/13_layer_04_event_failure_risk.md'),
  payload = replace(payload, 'trading-model/docs/05_layer_04_event_failure_risk.md', 'trading-model/docs/13_layer_04_event_failure_risk.md'),
  applies_to = replace(applies_to, 'trading-model/docs/05_layer_04_event_failure_risk.md', 'trading-model/docs/13_layer_04_event_failure_risk.md'),
  note = replace(note, 'trading-model/docs/05_layer_04_event_failure_risk.md', 'trading-model/docs/13_layer_04_event_failure_risk.md')
WHERE path LIKE '%trading-model/docs/05_layer_04_event_failure_risk.md%' OR payload LIKE '%trading-model/docs/05_layer_04_event_failure_risk.md%' OR applies_to LIKE '%trading-model/docs/05_layer_04_event_failure_risk.md%' OR note LIKE '%trading-model/docs/05_layer_04_event_failure_risk.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-model/docs/05_layer_04_event_failure_risk.md', '/root/projects/trading-model/docs/13_layer_04_event_failure_risk.md'),
  payload = replace(payload, '/root/projects/trading-model/docs/05_layer_04_event_failure_risk.md', '/root/projects/trading-model/docs/13_layer_04_event_failure_risk.md'),
  applies_to = replace(applies_to, '/root/projects/trading-model/docs/05_layer_04_event_failure_risk.md', '/root/projects/trading-model/docs/13_layer_04_event_failure_risk.md'),
  note = replace(note, '/root/projects/trading-model/docs/05_layer_04_event_failure_risk.md', '/root/projects/trading-model/docs/13_layer_04_event_failure_risk.md')
WHERE path LIKE '%/root/projects/trading-model/docs/05_layer_04_event_failure_risk.md%' OR payload LIKE '%/root/projects/trading-model/docs/05_layer_04_event_failure_risk.md%' OR applies_to LIKE '%/root/projects/trading-model/docs/05_layer_04_event_failure_risk.md%' OR note LIKE '%/root/projects/trading-model/docs/05_layer_04_event_failure_risk.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-model/docs/05_layer_04_event_failure_risk.md', 'file:/root/projects/trading-model/docs/13_layer_04_event_failure_risk.md'),
  payload = replace(payload, 'file:/root/projects/trading-model/docs/05_layer_04_event_failure_risk.md', 'file:/root/projects/trading-model/docs/13_layer_04_event_failure_risk.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-model/docs/05_layer_04_event_failure_risk.md', 'file:/root/projects/trading-model/docs/13_layer_04_event_failure_risk.md'),
  note = replace(note, 'file:/root/projects/trading-model/docs/05_layer_04_event_failure_risk.md', 'file:/root/projects/trading-model/docs/13_layer_04_event_failure_risk.md')
WHERE path LIKE '%file:/root/projects/trading-model/docs/05_layer_04_event_failure_risk.md%' OR payload LIKE '%file:/root/projects/trading-model/docs/05_layer_04_event_failure_risk.md%' OR applies_to LIKE '%file:/root/projects/trading-model/docs/05_layer_04_event_failure_risk.md%' OR note LIKE '%file:/root/projects/trading-model/docs/05_layer_04_event_failure_risk.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-model/docs/06_layer_05_alpha_confidence.md', 'trading-model/docs/14_layer_05_alpha_confidence.md'),
  payload = replace(payload, 'trading-model/docs/06_layer_05_alpha_confidence.md', 'trading-model/docs/14_layer_05_alpha_confidence.md'),
  applies_to = replace(applies_to, 'trading-model/docs/06_layer_05_alpha_confidence.md', 'trading-model/docs/14_layer_05_alpha_confidence.md'),
  note = replace(note, 'trading-model/docs/06_layer_05_alpha_confidence.md', 'trading-model/docs/14_layer_05_alpha_confidence.md')
WHERE path LIKE '%trading-model/docs/06_layer_05_alpha_confidence.md%' OR payload LIKE '%trading-model/docs/06_layer_05_alpha_confidence.md%' OR applies_to LIKE '%trading-model/docs/06_layer_05_alpha_confidence.md%' OR note LIKE '%trading-model/docs/06_layer_05_alpha_confidence.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-model/docs/06_layer_05_alpha_confidence.md', '/root/projects/trading-model/docs/14_layer_05_alpha_confidence.md'),
  payload = replace(payload, '/root/projects/trading-model/docs/06_layer_05_alpha_confidence.md', '/root/projects/trading-model/docs/14_layer_05_alpha_confidence.md'),
  applies_to = replace(applies_to, '/root/projects/trading-model/docs/06_layer_05_alpha_confidence.md', '/root/projects/trading-model/docs/14_layer_05_alpha_confidence.md'),
  note = replace(note, '/root/projects/trading-model/docs/06_layer_05_alpha_confidence.md', '/root/projects/trading-model/docs/14_layer_05_alpha_confidence.md')
WHERE path LIKE '%/root/projects/trading-model/docs/06_layer_05_alpha_confidence.md%' OR payload LIKE '%/root/projects/trading-model/docs/06_layer_05_alpha_confidence.md%' OR applies_to LIKE '%/root/projects/trading-model/docs/06_layer_05_alpha_confidence.md%' OR note LIKE '%/root/projects/trading-model/docs/06_layer_05_alpha_confidence.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-model/docs/06_layer_05_alpha_confidence.md', 'file:/root/projects/trading-model/docs/14_layer_05_alpha_confidence.md'),
  payload = replace(payload, 'file:/root/projects/trading-model/docs/06_layer_05_alpha_confidence.md', 'file:/root/projects/trading-model/docs/14_layer_05_alpha_confidence.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-model/docs/06_layer_05_alpha_confidence.md', 'file:/root/projects/trading-model/docs/14_layer_05_alpha_confidence.md'),
  note = replace(note, 'file:/root/projects/trading-model/docs/06_layer_05_alpha_confidence.md', 'file:/root/projects/trading-model/docs/14_layer_05_alpha_confidence.md')
WHERE path LIKE '%file:/root/projects/trading-model/docs/06_layer_05_alpha_confidence.md%' OR payload LIKE '%file:/root/projects/trading-model/docs/06_layer_05_alpha_confidence.md%' OR applies_to LIKE '%file:/root/projects/trading-model/docs/06_layer_05_alpha_confidence.md%' OR note LIKE '%file:/root/projects/trading-model/docs/06_layer_05_alpha_confidence.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-model/docs/07_layer_06_position_projection.md', 'trading-model/docs/15_layer_06_position_projection.md'),
  payload = replace(payload, 'trading-model/docs/07_layer_06_position_projection.md', 'trading-model/docs/15_layer_06_position_projection.md'),
  applies_to = replace(applies_to, 'trading-model/docs/07_layer_06_position_projection.md', 'trading-model/docs/15_layer_06_position_projection.md'),
  note = replace(note, 'trading-model/docs/07_layer_06_position_projection.md', 'trading-model/docs/15_layer_06_position_projection.md')
WHERE path LIKE '%trading-model/docs/07_layer_06_position_projection.md%' OR payload LIKE '%trading-model/docs/07_layer_06_position_projection.md%' OR applies_to LIKE '%trading-model/docs/07_layer_06_position_projection.md%' OR note LIKE '%trading-model/docs/07_layer_06_position_projection.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-model/docs/07_layer_06_position_projection.md', '/root/projects/trading-model/docs/15_layer_06_position_projection.md'),
  payload = replace(payload, '/root/projects/trading-model/docs/07_layer_06_position_projection.md', '/root/projects/trading-model/docs/15_layer_06_position_projection.md'),
  applies_to = replace(applies_to, '/root/projects/trading-model/docs/07_layer_06_position_projection.md', '/root/projects/trading-model/docs/15_layer_06_position_projection.md'),
  note = replace(note, '/root/projects/trading-model/docs/07_layer_06_position_projection.md', '/root/projects/trading-model/docs/15_layer_06_position_projection.md')
WHERE path LIKE '%/root/projects/trading-model/docs/07_layer_06_position_projection.md%' OR payload LIKE '%/root/projects/trading-model/docs/07_layer_06_position_projection.md%' OR applies_to LIKE '%/root/projects/trading-model/docs/07_layer_06_position_projection.md%' OR note LIKE '%/root/projects/trading-model/docs/07_layer_06_position_projection.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-model/docs/07_layer_06_position_projection.md', 'file:/root/projects/trading-model/docs/15_layer_06_position_projection.md'),
  payload = replace(payload, 'file:/root/projects/trading-model/docs/07_layer_06_position_projection.md', 'file:/root/projects/trading-model/docs/15_layer_06_position_projection.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-model/docs/07_layer_06_position_projection.md', 'file:/root/projects/trading-model/docs/15_layer_06_position_projection.md'),
  note = replace(note, 'file:/root/projects/trading-model/docs/07_layer_06_position_projection.md', 'file:/root/projects/trading-model/docs/15_layer_06_position_projection.md')
WHERE path LIKE '%file:/root/projects/trading-model/docs/07_layer_06_position_projection.md%' OR payload LIKE '%file:/root/projects/trading-model/docs/07_layer_06_position_projection.md%' OR applies_to LIKE '%file:/root/projects/trading-model/docs/07_layer_06_position_projection.md%' OR note LIKE '%file:/root/projects/trading-model/docs/07_layer_06_position_projection.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-model/docs/08_layer_07_underlying_action.md', 'trading-model/docs/16_layer_07_underlying_action.md'),
  payload = replace(payload, 'trading-model/docs/08_layer_07_underlying_action.md', 'trading-model/docs/16_layer_07_underlying_action.md'),
  applies_to = replace(applies_to, 'trading-model/docs/08_layer_07_underlying_action.md', 'trading-model/docs/16_layer_07_underlying_action.md'),
  note = replace(note, 'trading-model/docs/08_layer_07_underlying_action.md', 'trading-model/docs/16_layer_07_underlying_action.md')
WHERE path LIKE '%trading-model/docs/08_layer_07_underlying_action.md%' OR payload LIKE '%trading-model/docs/08_layer_07_underlying_action.md%' OR applies_to LIKE '%trading-model/docs/08_layer_07_underlying_action.md%' OR note LIKE '%trading-model/docs/08_layer_07_underlying_action.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-model/docs/08_layer_07_underlying_action.md', '/root/projects/trading-model/docs/16_layer_07_underlying_action.md'),
  payload = replace(payload, '/root/projects/trading-model/docs/08_layer_07_underlying_action.md', '/root/projects/trading-model/docs/16_layer_07_underlying_action.md'),
  applies_to = replace(applies_to, '/root/projects/trading-model/docs/08_layer_07_underlying_action.md', '/root/projects/trading-model/docs/16_layer_07_underlying_action.md'),
  note = replace(note, '/root/projects/trading-model/docs/08_layer_07_underlying_action.md', '/root/projects/trading-model/docs/16_layer_07_underlying_action.md')
WHERE path LIKE '%/root/projects/trading-model/docs/08_layer_07_underlying_action.md%' OR payload LIKE '%/root/projects/trading-model/docs/08_layer_07_underlying_action.md%' OR applies_to LIKE '%/root/projects/trading-model/docs/08_layer_07_underlying_action.md%' OR note LIKE '%/root/projects/trading-model/docs/08_layer_07_underlying_action.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-model/docs/08_layer_07_underlying_action.md', 'file:/root/projects/trading-model/docs/16_layer_07_underlying_action.md'),
  payload = replace(payload, 'file:/root/projects/trading-model/docs/08_layer_07_underlying_action.md', 'file:/root/projects/trading-model/docs/16_layer_07_underlying_action.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-model/docs/08_layer_07_underlying_action.md', 'file:/root/projects/trading-model/docs/16_layer_07_underlying_action.md'),
  note = replace(note, 'file:/root/projects/trading-model/docs/08_layer_07_underlying_action.md', 'file:/root/projects/trading-model/docs/16_layer_07_underlying_action.md')
WHERE path LIKE '%file:/root/projects/trading-model/docs/08_layer_07_underlying_action.md%' OR payload LIKE '%file:/root/projects/trading-model/docs/08_layer_07_underlying_action.md%' OR applies_to LIKE '%file:/root/projects/trading-model/docs/08_layer_07_underlying_action.md%' OR note LIKE '%file:/root/projects/trading-model/docs/08_layer_07_underlying_action.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-model/docs/09_layer_08_trading_guidance.md', 'trading-model/docs/17_layer_08_trading_guidance.md'),
  payload = replace(payload, 'trading-model/docs/09_layer_08_trading_guidance.md', 'trading-model/docs/17_layer_08_trading_guidance.md'),
  applies_to = replace(applies_to, 'trading-model/docs/09_layer_08_trading_guidance.md', 'trading-model/docs/17_layer_08_trading_guidance.md'),
  note = replace(note, 'trading-model/docs/09_layer_08_trading_guidance.md', 'trading-model/docs/17_layer_08_trading_guidance.md')
WHERE path LIKE '%trading-model/docs/09_layer_08_trading_guidance.md%' OR payload LIKE '%trading-model/docs/09_layer_08_trading_guidance.md%' OR applies_to LIKE '%trading-model/docs/09_layer_08_trading_guidance.md%' OR note LIKE '%trading-model/docs/09_layer_08_trading_guidance.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-model/docs/09_layer_08_trading_guidance.md', '/root/projects/trading-model/docs/17_layer_08_trading_guidance.md'),
  payload = replace(payload, '/root/projects/trading-model/docs/09_layer_08_trading_guidance.md', '/root/projects/trading-model/docs/17_layer_08_trading_guidance.md'),
  applies_to = replace(applies_to, '/root/projects/trading-model/docs/09_layer_08_trading_guidance.md', '/root/projects/trading-model/docs/17_layer_08_trading_guidance.md'),
  note = replace(note, '/root/projects/trading-model/docs/09_layer_08_trading_guidance.md', '/root/projects/trading-model/docs/17_layer_08_trading_guidance.md')
WHERE path LIKE '%/root/projects/trading-model/docs/09_layer_08_trading_guidance.md%' OR payload LIKE '%/root/projects/trading-model/docs/09_layer_08_trading_guidance.md%' OR applies_to LIKE '%/root/projects/trading-model/docs/09_layer_08_trading_guidance.md%' OR note LIKE '%/root/projects/trading-model/docs/09_layer_08_trading_guidance.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-model/docs/09_layer_08_trading_guidance.md', 'file:/root/projects/trading-model/docs/17_layer_08_trading_guidance.md'),
  payload = replace(payload, 'file:/root/projects/trading-model/docs/09_layer_08_trading_guidance.md', 'file:/root/projects/trading-model/docs/17_layer_08_trading_guidance.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-model/docs/09_layer_08_trading_guidance.md', 'file:/root/projects/trading-model/docs/17_layer_08_trading_guidance.md'),
  note = replace(note, 'file:/root/projects/trading-model/docs/09_layer_08_trading_guidance.md', 'file:/root/projects/trading-model/docs/17_layer_08_trading_guidance.md')
WHERE path LIKE '%file:/root/projects/trading-model/docs/09_layer_08_trading_guidance.md%' OR payload LIKE '%file:/root/projects/trading-model/docs/09_layer_08_trading_guidance.md%' OR applies_to LIKE '%file:/root/projects/trading-model/docs/09_layer_08_trading_guidance.md%' OR note LIKE '%file:/root/projects/trading-model/docs/09_layer_08_trading_guidance.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-model/docs/10_layer_09_event_risk_governor.md', 'trading-model/docs/18_layer_09_event_risk_governor.md'),
  payload = replace(payload, 'trading-model/docs/10_layer_09_event_risk_governor.md', 'trading-model/docs/18_layer_09_event_risk_governor.md'),
  applies_to = replace(applies_to, 'trading-model/docs/10_layer_09_event_risk_governor.md', 'trading-model/docs/18_layer_09_event_risk_governor.md'),
  note = replace(note, 'trading-model/docs/10_layer_09_event_risk_governor.md', 'trading-model/docs/18_layer_09_event_risk_governor.md')
WHERE path LIKE '%trading-model/docs/10_layer_09_event_risk_governor.md%' OR payload LIKE '%trading-model/docs/10_layer_09_event_risk_governor.md%' OR applies_to LIKE '%trading-model/docs/10_layer_09_event_risk_governor.md%' OR note LIKE '%trading-model/docs/10_layer_09_event_risk_governor.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-model/docs/10_layer_09_event_risk_governor.md', '/root/projects/trading-model/docs/18_layer_09_event_risk_governor.md'),
  payload = replace(payload, '/root/projects/trading-model/docs/10_layer_09_event_risk_governor.md', '/root/projects/trading-model/docs/18_layer_09_event_risk_governor.md'),
  applies_to = replace(applies_to, '/root/projects/trading-model/docs/10_layer_09_event_risk_governor.md', '/root/projects/trading-model/docs/18_layer_09_event_risk_governor.md'),
  note = replace(note, '/root/projects/trading-model/docs/10_layer_09_event_risk_governor.md', '/root/projects/trading-model/docs/18_layer_09_event_risk_governor.md')
WHERE path LIKE '%/root/projects/trading-model/docs/10_layer_09_event_risk_governor.md%' OR payload LIKE '%/root/projects/trading-model/docs/10_layer_09_event_risk_governor.md%' OR applies_to LIKE '%/root/projects/trading-model/docs/10_layer_09_event_risk_governor.md%' OR note LIKE '%/root/projects/trading-model/docs/10_layer_09_event_risk_governor.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-model/docs/10_layer_09_event_risk_governor.md', 'file:/root/projects/trading-model/docs/18_layer_09_event_risk_governor.md'),
  payload = replace(payload, 'file:/root/projects/trading-model/docs/10_layer_09_event_risk_governor.md', 'file:/root/projects/trading-model/docs/18_layer_09_event_risk_governor.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-model/docs/10_layer_09_event_risk_governor.md', 'file:/root/projects/trading-model/docs/18_layer_09_event_risk_governor.md'),
  note = replace(note, 'file:/root/projects/trading-model/docs/10_layer_09_event_risk_governor.md', 'file:/root/projects/trading-model/docs/18_layer_09_event_risk_governor.md')
WHERE path LIKE '%file:/root/projects/trading-model/docs/10_layer_09_event_risk_governor.md%' OR payload LIKE '%file:/root/projects/trading-model/docs/10_layer_09_event_risk_governor.md%' OR applies_to LIKE '%file:/root/projects/trading-model/docs/10_layer_09_event_risk_governor.md%' OR note LIKE '%file:/root/projects/trading-model/docs/10_layer_09_event_risk_governor.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-model/docs/12_model_decomposition.md', 'trading-model/docs/20_model_decomposition.md'),
  payload = replace(payload, 'trading-model/docs/12_model_decomposition.md', 'trading-model/docs/20_model_decomposition.md'),
  applies_to = replace(applies_to, 'trading-model/docs/12_model_decomposition.md', 'trading-model/docs/20_model_decomposition.md'),
  note = replace(note, 'trading-model/docs/12_model_decomposition.md', 'trading-model/docs/20_model_decomposition.md')
WHERE path LIKE '%trading-model/docs/12_model_decomposition.md%' OR payload LIKE '%trading-model/docs/12_model_decomposition.md%' OR applies_to LIKE '%trading-model/docs/12_model_decomposition.md%' OR note LIKE '%trading-model/docs/12_model_decomposition.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-model/docs/12_model_decomposition.md', '/root/projects/trading-model/docs/20_model_decomposition.md'),
  payload = replace(payload, '/root/projects/trading-model/docs/12_model_decomposition.md', '/root/projects/trading-model/docs/20_model_decomposition.md'),
  applies_to = replace(applies_to, '/root/projects/trading-model/docs/12_model_decomposition.md', '/root/projects/trading-model/docs/20_model_decomposition.md'),
  note = replace(note, '/root/projects/trading-model/docs/12_model_decomposition.md', '/root/projects/trading-model/docs/20_model_decomposition.md')
WHERE path LIKE '%/root/projects/trading-model/docs/12_model_decomposition.md%' OR payload LIKE '%/root/projects/trading-model/docs/12_model_decomposition.md%' OR applies_to LIKE '%/root/projects/trading-model/docs/12_model_decomposition.md%' OR note LIKE '%/root/projects/trading-model/docs/12_model_decomposition.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-model/docs/12_model_decomposition.md', 'file:/root/projects/trading-model/docs/20_model_decomposition.md'),
  payload = replace(payload, 'file:/root/projects/trading-model/docs/12_model_decomposition.md', 'file:/root/projects/trading-model/docs/20_model_decomposition.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-model/docs/12_model_decomposition.md', 'file:/root/projects/trading-model/docs/20_model_decomposition.md'),
  note = replace(note, 'file:/root/projects/trading-model/docs/12_model_decomposition.md', 'file:/root/projects/trading-model/docs/20_model_decomposition.md')
WHERE path LIKE '%file:/root/projects/trading-model/docs/12_model_decomposition.md%' OR payload LIKE '%file:/root/projects/trading-model/docs/12_model_decomposition.md%' OR applies_to LIKE '%file:/root/projects/trading-model/docs/12_model_decomposition.md%' OR note LIKE '%file:/root/projects/trading-model/docs/12_model_decomposition.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-model/docs/13_vector_taxonomy.md', 'trading-model/docs/21_vector_taxonomy.md'),
  payload = replace(payload, 'trading-model/docs/13_vector_taxonomy.md', 'trading-model/docs/21_vector_taxonomy.md'),
  applies_to = replace(applies_to, 'trading-model/docs/13_vector_taxonomy.md', 'trading-model/docs/21_vector_taxonomy.md'),
  note = replace(note, 'trading-model/docs/13_vector_taxonomy.md', 'trading-model/docs/21_vector_taxonomy.md')
WHERE path LIKE '%trading-model/docs/13_vector_taxonomy.md%' OR payload LIKE '%trading-model/docs/13_vector_taxonomy.md%' OR applies_to LIKE '%trading-model/docs/13_vector_taxonomy.md%' OR note LIKE '%trading-model/docs/13_vector_taxonomy.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-model/docs/13_vector_taxonomy.md', '/root/projects/trading-model/docs/21_vector_taxonomy.md'),
  payload = replace(payload, '/root/projects/trading-model/docs/13_vector_taxonomy.md', '/root/projects/trading-model/docs/21_vector_taxonomy.md'),
  applies_to = replace(applies_to, '/root/projects/trading-model/docs/13_vector_taxonomy.md', '/root/projects/trading-model/docs/21_vector_taxonomy.md'),
  note = replace(note, '/root/projects/trading-model/docs/13_vector_taxonomy.md', '/root/projects/trading-model/docs/21_vector_taxonomy.md')
WHERE path LIKE '%/root/projects/trading-model/docs/13_vector_taxonomy.md%' OR payload LIKE '%/root/projects/trading-model/docs/13_vector_taxonomy.md%' OR applies_to LIKE '%/root/projects/trading-model/docs/13_vector_taxonomy.md%' OR note LIKE '%/root/projects/trading-model/docs/13_vector_taxonomy.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-model/docs/13_vector_taxonomy.md', 'file:/root/projects/trading-model/docs/21_vector_taxonomy.md'),
  payload = replace(payload, 'file:/root/projects/trading-model/docs/13_vector_taxonomy.md', 'file:/root/projects/trading-model/docs/21_vector_taxonomy.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-model/docs/13_vector_taxonomy.md', 'file:/root/projects/trading-model/docs/21_vector_taxonomy.md'),
  note = replace(note, 'file:/root/projects/trading-model/docs/13_vector_taxonomy.md', 'file:/root/projects/trading-model/docs/21_vector_taxonomy.md')
WHERE path LIKE '%file:/root/projects/trading-model/docs/13_vector_taxonomy.md%' OR payload LIKE '%file:/root/projects/trading-model/docs/13_vector_taxonomy.md%' OR applies_to LIKE '%file:/root/projects/trading-model/docs/13_vector_taxonomy.md%' OR note LIKE '%file:/root/projects/trading-model/docs/13_vector_taxonomy.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-model/docs/14_state_vector_feature_registry.md', 'trading-model/docs/22_state_vector_feature_registry.md'),
  payload = replace(payload, 'trading-model/docs/14_state_vector_feature_registry.md', 'trading-model/docs/22_state_vector_feature_registry.md'),
  applies_to = replace(applies_to, 'trading-model/docs/14_state_vector_feature_registry.md', 'trading-model/docs/22_state_vector_feature_registry.md'),
  note = replace(note, 'trading-model/docs/14_state_vector_feature_registry.md', 'trading-model/docs/22_state_vector_feature_registry.md')
WHERE path LIKE '%trading-model/docs/14_state_vector_feature_registry.md%' OR payload LIKE '%trading-model/docs/14_state_vector_feature_registry.md%' OR applies_to LIKE '%trading-model/docs/14_state_vector_feature_registry.md%' OR note LIKE '%trading-model/docs/14_state_vector_feature_registry.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-model/docs/14_state_vector_feature_registry.md', '/root/projects/trading-model/docs/22_state_vector_feature_registry.md'),
  payload = replace(payload, '/root/projects/trading-model/docs/14_state_vector_feature_registry.md', '/root/projects/trading-model/docs/22_state_vector_feature_registry.md'),
  applies_to = replace(applies_to, '/root/projects/trading-model/docs/14_state_vector_feature_registry.md', '/root/projects/trading-model/docs/22_state_vector_feature_registry.md'),
  note = replace(note, '/root/projects/trading-model/docs/14_state_vector_feature_registry.md', '/root/projects/trading-model/docs/22_state_vector_feature_registry.md')
WHERE path LIKE '%/root/projects/trading-model/docs/14_state_vector_feature_registry.md%' OR payload LIKE '%/root/projects/trading-model/docs/14_state_vector_feature_registry.md%' OR applies_to LIKE '%/root/projects/trading-model/docs/14_state_vector_feature_registry.md%' OR note LIKE '%/root/projects/trading-model/docs/14_state_vector_feature_registry.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-model/docs/14_state_vector_feature_registry.md', 'file:/root/projects/trading-model/docs/22_state_vector_feature_registry.md'),
  payload = replace(payload, 'file:/root/projects/trading-model/docs/14_state_vector_feature_registry.md', 'file:/root/projects/trading-model/docs/22_state_vector_feature_registry.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-model/docs/14_state_vector_feature_registry.md', 'file:/root/projects/trading-model/docs/22_state_vector_feature_registry.md'),
  note = replace(note, 'file:/root/projects/trading-model/docs/14_state_vector_feature_registry.md', 'file:/root/projects/trading-model/docs/22_state_vector_feature_registry.md')
WHERE path LIKE '%file:/root/projects/trading-model/docs/14_state_vector_feature_registry.md%' OR payload LIKE '%file:/root/projects/trading-model/docs/14_state_vector_feature_registry.md%' OR applies_to LIKE '%file:/root/projects/trading-model/docs/14_state_vector_feature_registry.md%' OR note LIKE '%file:/root/projects/trading-model/docs/14_state_vector_feature_registry.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-model/docs/16_promotion_readiness.md', 'trading-model/docs/30_promotion_readiness.md'),
  payload = replace(payload, 'trading-model/docs/16_promotion_readiness.md', 'trading-model/docs/30_promotion_readiness.md'),
  applies_to = replace(applies_to, 'trading-model/docs/16_promotion_readiness.md', 'trading-model/docs/30_promotion_readiness.md'),
  note = replace(note, 'trading-model/docs/16_promotion_readiness.md', 'trading-model/docs/30_promotion_readiness.md')
WHERE path LIKE '%trading-model/docs/16_promotion_readiness.md%' OR payload LIKE '%trading-model/docs/16_promotion_readiness.md%' OR applies_to LIKE '%trading-model/docs/16_promotion_readiness.md%' OR note LIKE '%trading-model/docs/16_promotion_readiness.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-model/docs/16_promotion_readiness.md', '/root/projects/trading-model/docs/30_promotion_readiness.md'),
  payload = replace(payload, '/root/projects/trading-model/docs/16_promotion_readiness.md', '/root/projects/trading-model/docs/30_promotion_readiness.md'),
  applies_to = replace(applies_to, '/root/projects/trading-model/docs/16_promotion_readiness.md', '/root/projects/trading-model/docs/30_promotion_readiness.md'),
  note = replace(note, '/root/projects/trading-model/docs/16_promotion_readiness.md', '/root/projects/trading-model/docs/30_promotion_readiness.md')
WHERE path LIKE '%/root/projects/trading-model/docs/16_promotion_readiness.md%' OR payload LIKE '%/root/projects/trading-model/docs/16_promotion_readiness.md%' OR applies_to LIKE '%/root/projects/trading-model/docs/16_promotion_readiness.md%' OR note LIKE '%/root/projects/trading-model/docs/16_promotion_readiness.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-model/docs/16_promotion_readiness.md', 'file:/root/projects/trading-model/docs/30_promotion_readiness.md'),
  payload = replace(payload, 'file:/root/projects/trading-model/docs/16_promotion_readiness.md', 'file:/root/projects/trading-model/docs/30_promotion_readiness.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-model/docs/16_promotion_readiness.md', 'file:/root/projects/trading-model/docs/30_promotion_readiness.md'),
  note = replace(note, 'file:/root/projects/trading-model/docs/16_promotion_readiness.md', 'file:/root/projects/trading-model/docs/30_promotion_readiness.md')
WHERE path LIKE '%file:/root/projects/trading-model/docs/16_promotion_readiness.md%' OR payload LIKE '%file:/root/projects/trading-model/docs/16_promotion_readiness.md%' OR applies_to LIKE '%file:/root/projects/trading-model/docs/16_promotion_readiness.md%' OR note LIKE '%file:/root/projects/trading-model/docs/16_promotion_readiness.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-model/docs/17_promotion_acceptance.md', 'trading-model/docs/31_promotion_acceptance.md'),
  payload = replace(payload, 'trading-model/docs/17_promotion_acceptance.md', 'trading-model/docs/31_promotion_acceptance.md'),
  applies_to = replace(applies_to, 'trading-model/docs/17_promotion_acceptance.md', 'trading-model/docs/31_promotion_acceptance.md'),
  note = replace(note, 'trading-model/docs/17_promotion_acceptance.md', 'trading-model/docs/31_promotion_acceptance.md')
WHERE path LIKE '%trading-model/docs/17_promotion_acceptance.md%' OR payload LIKE '%trading-model/docs/17_promotion_acceptance.md%' OR applies_to LIKE '%trading-model/docs/17_promotion_acceptance.md%' OR note LIKE '%trading-model/docs/17_promotion_acceptance.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-model/docs/17_promotion_acceptance.md', '/root/projects/trading-model/docs/31_promotion_acceptance.md'),
  payload = replace(payload, '/root/projects/trading-model/docs/17_promotion_acceptance.md', '/root/projects/trading-model/docs/31_promotion_acceptance.md'),
  applies_to = replace(applies_to, '/root/projects/trading-model/docs/17_promotion_acceptance.md', '/root/projects/trading-model/docs/31_promotion_acceptance.md'),
  note = replace(note, '/root/projects/trading-model/docs/17_promotion_acceptance.md', '/root/projects/trading-model/docs/31_promotion_acceptance.md')
WHERE path LIKE '%/root/projects/trading-model/docs/17_promotion_acceptance.md%' OR payload LIKE '%/root/projects/trading-model/docs/17_promotion_acceptance.md%' OR applies_to LIKE '%/root/projects/trading-model/docs/17_promotion_acceptance.md%' OR note LIKE '%/root/projects/trading-model/docs/17_promotion_acceptance.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-model/docs/17_promotion_acceptance.md', 'file:/root/projects/trading-model/docs/31_promotion_acceptance.md'),
  payload = replace(payload, 'file:/root/projects/trading-model/docs/17_promotion_acceptance.md', 'file:/root/projects/trading-model/docs/31_promotion_acceptance.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-model/docs/17_promotion_acceptance.md', 'file:/root/projects/trading-model/docs/31_promotion_acceptance.md'),
  note = replace(note, 'file:/root/projects/trading-model/docs/17_promotion_acceptance.md', 'file:/root/projects/trading-model/docs/31_promotion_acceptance.md')
WHERE path LIKE '%file:/root/projects/trading-model/docs/17_promotion_acceptance.md%' OR payload LIKE '%file:/root/projects/trading-model/docs/17_promotion_acceptance.md%' OR applies_to LIKE '%file:/root/projects/trading-model/docs/17_promotion_acceptance.md%' OR note LIKE '%file:/root/projects/trading-model/docs/17_promotion_acceptance.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-model/docs/18_historical_dataset_scope.md', 'trading-model/docs/40_historical_dataset_scope.md'),
  payload = replace(payload, 'trading-model/docs/18_historical_dataset_scope.md', 'trading-model/docs/40_historical_dataset_scope.md'),
  applies_to = replace(applies_to, 'trading-model/docs/18_historical_dataset_scope.md', 'trading-model/docs/40_historical_dataset_scope.md'),
  note = replace(note, 'trading-model/docs/18_historical_dataset_scope.md', 'trading-model/docs/40_historical_dataset_scope.md')
WHERE path LIKE '%trading-model/docs/18_historical_dataset_scope.md%' OR payload LIKE '%trading-model/docs/18_historical_dataset_scope.md%' OR applies_to LIKE '%trading-model/docs/18_historical_dataset_scope.md%' OR note LIKE '%trading-model/docs/18_historical_dataset_scope.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-model/docs/18_historical_dataset_scope.md', '/root/projects/trading-model/docs/40_historical_dataset_scope.md'),
  payload = replace(payload, '/root/projects/trading-model/docs/18_historical_dataset_scope.md', '/root/projects/trading-model/docs/40_historical_dataset_scope.md'),
  applies_to = replace(applies_to, '/root/projects/trading-model/docs/18_historical_dataset_scope.md', '/root/projects/trading-model/docs/40_historical_dataset_scope.md'),
  note = replace(note, '/root/projects/trading-model/docs/18_historical_dataset_scope.md', '/root/projects/trading-model/docs/40_historical_dataset_scope.md')
WHERE path LIKE '%/root/projects/trading-model/docs/18_historical_dataset_scope.md%' OR payload LIKE '%/root/projects/trading-model/docs/18_historical_dataset_scope.md%' OR applies_to LIKE '%/root/projects/trading-model/docs/18_historical_dataset_scope.md%' OR note LIKE '%/root/projects/trading-model/docs/18_historical_dataset_scope.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-model/docs/18_historical_dataset_scope.md', 'file:/root/projects/trading-model/docs/40_historical_dataset_scope.md'),
  payload = replace(payload, 'file:/root/projects/trading-model/docs/18_historical_dataset_scope.md', 'file:/root/projects/trading-model/docs/40_historical_dataset_scope.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-model/docs/18_historical_dataset_scope.md', 'file:/root/projects/trading-model/docs/40_historical_dataset_scope.md'),
  note = replace(note, 'file:/root/projects/trading-model/docs/18_historical_dataset_scope.md', 'file:/root/projects/trading-model/docs/40_historical_dataset_scope.md')
WHERE path LIKE '%file:/root/projects/trading-model/docs/18_historical_dataset_scope.md%' OR payload LIKE '%file:/root/projects/trading-model/docs/18_historical_dataset_scope.md%' OR applies_to LIKE '%file:/root/projects/trading-model/docs/18_historical_dataset_scope.md%' OR note LIKE '%file:/root/projects/trading-model/docs/18_historical_dataset_scope.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-model/docs/19_realtime_decision_handoff.md', 'trading-model/docs/41_realtime_decision_handoff.md'),
  payload = replace(payload, 'trading-model/docs/19_realtime_decision_handoff.md', 'trading-model/docs/41_realtime_decision_handoff.md'),
  applies_to = replace(applies_to, 'trading-model/docs/19_realtime_decision_handoff.md', 'trading-model/docs/41_realtime_decision_handoff.md'),
  note = replace(note, 'trading-model/docs/19_realtime_decision_handoff.md', 'trading-model/docs/41_realtime_decision_handoff.md')
WHERE path LIKE '%trading-model/docs/19_realtime_decision_handoff.md%' OR payload LIKE '%trading-model/docs/19_realtime_decision_handoff.md%' OR applies_to LIKE '%trading-model/docs/19_realtime_decision_handoff.md%' OR note LIKE '%trading-model/docs/19_realtime_decision_handoff.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-model/docs/19_realtime_decision_handoff.md', '/root/projects/trading-model/docs/41_realtime_decision_handoff.md'),
  payload = replace(payload, '/root/projects/trading-model/docs/19_realtime_decision_handoff.md', '/root/projects/trading-model/docs/41_realtime_decision_handoff.md'),
  applies_to = replace(applies_to, '/root/projects/trading-model/docs/19_realtime_decision_handoff.md', '/root/projects/trading-model/docs/41_realtime_decision_handoff.md'),
  note = replace(note, '/root/projects/trading-model/docs/19_realtime_decision_handoff.md', '/root/projects/trading-model/docs/41_realtime_decision_handoff.md')
WHERE path LIKE '%/root/projects/trading-model/docs/19_realtime_decision_handoff.md%' OR payload LIKE '%/root/projects/trading-model/docs/19_realtime_decision_handoff.md%' OR applies_to LIKE '%/root/projects/trading-model/docs/19_realtime_decision_handoff.md%' OR note LIKE '%/root/projects/trading-model/docs/19_realtime_decision_handoff.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-model/docs/19_realtime_decision_handoff.md', 'file:/root/projects/trading-model/docs/41_realtime_decision_handoff.md'),
  payload = replace(payload, 'file:/root/projects/trading-model/docs/19_realtime_decision_handoff.md', 'file:/root/projects/trading-model/docs/41_realtime_decision_handoff.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-model/docs/19_realtime_decision_handoff.md', 'file:/root/projects/trading-model/docs/41_realtime_decision_handoff.md'),
  note = replace(note, 'file:/root/projects/trading-model/docs/19_realtime_decision_handoff.md', 'file:/root/projects/trading-model/docs/41_realtime_decision_handoff.md')
WHERE path LIKE '%file:/root/projects/trading-model/docs/19_realtime_decision_handoff.md%' OR payload LIKE '%file:/root/projects/trading-model/docs/19_realtime_decision_handoff.md%' OR applies_to LIKE '%file:/root/projects/trading-model/docs/19_realtime_decision_handoff.md%' OR note LIKE '%file:/root/projects/trading-model/docs/19_realtime_decision_handoff.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-model/docs/20_activity_price_relationship_study.md', 'trading-model/docs/50_activity_price_relationship_study.md'),
  payload = replace(payload, 'trading-model/docs/20_activity_price_relationship_study.md', 'trading-model/docs/50_activity_price_relationship_study.md'),
  applies_to = replace(applies_to, 'trading-model/docs/20_activity_price_relationship_study.md', 'trading-model/docs/50_activity_price_relationship_study.md'),
  note = replace(note, 'trading-model/docs/20_activity_price_relationship_study.md', 'trading-model/docs/50_activity_price_relationship_study.md')
WHERE path LIKE '%trading-model/docs/20_activity_price_relationship_study.md%' OR payload LIKE '%trading-model/docs/20_activity_price_relationship_study.md%' OR applies_to LIKE '%trading-model/docs/20_activity_price_relationship_study.md%' OR note LIKE '%trading-model/docs/20_activity_price_relationship_study.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-model/docs/20_activity_price_relationship_study.md', '/root/projects/trading-model/docs/50_activity_price_relationship_study.md'),
  payload = replace(payload, '/root/projects/trading-model/docs/20_activity_price_relationship_study.md', '/root/projects/trading-model/docs/50_activity_price_relationship_study.md'),
  applies_to = replace(applies_to, '/root/projects/trading-model/docs/20_activity_price_relationship_study.md', '/root/projects/trading-model/docs/50_activity_price_relationship_study.md'),
  note = replace(note, '/root/projects/trading-model/docs/20_activity_price_relationship_study.md', '/root/projects/trading-model/docs/50_activity_price_relationship_study.md')
WHERE path LIKE '%/root/projects/trading-model/docs/20_activity_price_relationship_study.md%' OR payload LIKE '%/root/projects/trading-model/docs/20_activity_price_relationship_study.md%' OR applies_to LIKE '%/root/projects/trading-model/docs/20_activity_price_relationship_study.md%' OR note LIKE '%/root/projects/trading-model/docs/20_activity_price_relationship_study.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-model/docs/20_activity_price_relationship_study.md', 'file:/root/projects/trading-model/docs/50_activity_price_relationship_study.md'),
  payload = replace(payload, 'file:/root/projects/trading-model/docs/20_activity_price_relationship_study.md', 'file:/root/projects/trading-model/docs/50_activity_price_relationship_study.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-model/docs/20_activity_price_relationship_study.md', 'file:/root/projects/trading-model/docs/50_activity_price_relationship_study.md'),
  note = replace(note, 'file:/root/projects/trading-model/docs/20_activity_price_relationship_study.md', 'file:/root/projects/trading-model/docs/50_activity_price_relationship_study.md')
WHERE path LIKE '%file:/root/projects/trading-model/docs/20_activity_price_relationship_study.md%' OR payload LIKE '%file:/root/projects/trading-model/docs/20_activity_price_relationship_study.md%' OR applies_to LIKE '%file:/root/projects/trading-model/docs/20_activity_price_relationship_study.md%' OR note LIKE '%file:/root/projects/trading-model/docs/20_activity_price_relationship_study.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-model/docs/21_event_family_scouting.md', 'trading-model/docs/51_event_family_scouting.md'),
  payload = replace(payload, 'trading-model/docs/21_event_family_scouting.md', 'trading-model/docs/51_event_family_scouting.md'),
  applies_to = replace(applies_to, 'trading-model/docs/21_event_family_scouting.md', 'trading-model/docs/51_event_family_scouting.md'),
  note = replace(note, 'trading-model/docs/21_event_family_scouting.md', 'trading-model/docs/51_event_family_scouting.md')
WHERE path LIKE '%trading-model/docs/21_event_family_scouting.md%' OR payload LIKE '%trading-model/docs/21_event_family_scouting.md%' OR applies_to LIKE '%trading-model/docs/21_event_family_scouting.md%' OR note LIKE '%trading-model/docs/21_event_family_scouting.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-model/docs/21_event_family_scouting.md', '/root/projects/trading-model/docs/51_event_family_scouting.md'),
  payload = replace(payload, '/root/projects/trading-model/docs/21_event_family_scouting.md', '/root/projects/trading-model/docs/51_event_family_scouting.md'),
  applies_to = replace(applies_to, '/root/projects/trading-model/docs/21_event_family_scouting.md', '/root/projects/trading-model/docs/51_event_family_scouting.md'),
  note = replace(note, '/root/projects/trading-model/docs/21_event_family_scouting.md', '/root/projects/trading-model/docs/51_event_family_scouting.md')
WHERE path LIKE '%/root/projects/trading-model/docs/21_event_family_scouting.md%' OR payload LIKE '%/root/projects/trading-model/docs/21_event_family_scouting.md%' OR applies_to LIKE '%/root/projects/trading-model/docs/21_event_family_scouting.md%' OR note LIKE '%/root/projects/trading-model/docs/21_event_family_scouting.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-model/docs/21_event_family_scouting.md', 'file:/root/projects/trading-model/docs/51_event_family_scouting.md'),
  payload = replace(payload, 'file:/root/projects/trading-model/docs/21_event_family_scouting.md', 'file:/root/projects/trading-model/docs/51_event_family_scouting.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-model/docs/21_event_family_scouting.md', 'file:/root/projects/trading-model/docs/51_event_family_scouting.md'),
  note = replace(note, 'file:/root/projects/trading-model/docs/21_event_family_scouting.md', 'file:/root/projects/trading-model/docs/51_event_family_scouting.md')
WHERE path LIKE '%file:/root/projects/trading-model/docs/21_event_family_scouting.md%' OR payload LIKE '%file:/root/projects/trading-model/docs/21_event_family_scouting.md%' OR applies_to LIKE '%file:/root/projects/trading-model/docs/21_event_family_scouting.md%' OR note LIKE '%file:/root/projects/trading-model/docs/21_event_family_scouting.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-model/docs/22_earnings_guidance_event_family_packet.md', 'trading-model/docs/52_earnings_guidance_event_family_packet.md'),
  payload = replace(payload, 'trading-model/docs/22_earnings_guidance_event_family_packet.md', 'trading-model/docs/52_earnings_guidance_event_family_packet.md'),
  applies_to = replace(applies_to, 'trading-model/docs/22_earnings_guidance_event_family_packet.md', 'trading-model/docs/52_earnings_guidance_event_family_packet.md'),
  note = replace(note, 'trading-model/docs/22_earnings_guidance_event_family_packet.md', 'trading-model/docs/52_earnings_guidance_event_family_packet.md')
WHERE path LIKE '%trading-model/docs/22_earnings_guidance_event_family_packet.md%' OR payload LIKE '%trading-model/docs/22_earnings_guidance_event_family_packet.md%' OR applies_to LIKE '%trading-model/docs/22_earnings_guidance_event_family_packet.md%' OR note LIKE '%trading-model/docs/22_earnings_guidance_event_family_packet.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-model/docs/22_earnings_guidance_event_family_packet.md', '/root/projects/trading-model/docs/52_earnings_guidance_event_family_packet.md'),
  payload = replace(payload, '/root/projects/trading-model/docs/22_earnings_guidance_event_family_packet.md', '/root/projects/trading-model/docs/52_earnings_guidance_event_family_packet.md'),
  applies_to = replace(applies_to, '/root/projects/trading-model/docs/22_earnings_guidance_event_family_packet.md', '/root/projects/trading-model/docs/52_earnings_guidance_event_family_packet.md'),
  note = replace(note, '/root/projects/trading-model/docs/22_earnings_guidance_event_family_packet.md', '/root/projects/trading-model/docs/52_earnings_guidance_event_family_packet.md')
WHERE path LIKE '%/root/projects/trading-model/docs/22_earnings_guidance_event_family_packet.md%' OR payload LIKE '%/root/projects/trading-model/docs/22_earnings_guidance_event_family_packet.md%' OR applies_to LIKE '%/root/projects/trading-model/docs/22_earnings_guidance_event_family_packet.md%' OR note LIKE '%/root/projects/trading-model/docs/22_earnings_guidance_event_family_packet.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-model/docs/22_earnings_guidance_event_family_packet.md', 'file:/root/projects/trading-model/docs/52_earnings_guidance_event_family_packet.md'),
  payload = replace(payload, 'file:/root/projects/trading-model/docs/22_earnings_guidance_event_family_packet.md', 'file:/root/projects/trading-model/docs/52_earnings_guidance_event_family_packet.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-model/docs/22_earnings_guidance_event_family_packet.md', 'file:/root/projects/trading-model/docs/52_earnings_guidance_event_family_packet.md'),
  note = replace(note, 'file:/root/projects/trading-model/docs/22_earnings_guidance_event_family_packet.md', 'file:/root/projects/trading-model/docs/52_earnings_guidance_event_family_packet.md')
WHERE path LIKE '%file:/root/projects/trading-model/docs/22_earnings_guidance_event_family_packet.md%' OR payload LIKE '%file:/root/projects/trading-model/docs/22_earnings_guidance_event_family_packet.md%' OR applies_to LIKE '%file:/root/projects/trading-model/docs/22_earnings_guidance_event_family_packet.md%' OR note LIKE '%file:/root/projects/trading-model/docs/22_earnings_guidance_event_family_packet.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-model/docs/23_event_layer_final_judgment.md', 'trading-model/docs/53_event_layer_final_judgment.md'),
  payload = replace(payload, 'trading-model/docs/23_event_layer_final_judgment.md', 'trading-model/docs/53_event_layer_final_judgment.md'),
  applies_to = replace(applies_to, 'trading-model/docs/23_event_layer_final_judgment.md', 'trading-model/docs/53_event_layer_final_judgment.md'),
  note = replace(note, 'trading-model/docs/23_event_layer_final_judgment.md', 'trading-model/docs/53_event_layer_final_judgment.md')
WHERE path LIKE '%trading-model/docs/23_event_layer_final_judgment.md%' OR payload LIKE '%trading-model/docs/23_event_layer_final_judgment.md%' OR applies_to LIKE '%trading-model/docs/23_event_layer_final_judgment.md%' OR note LIKE '%trading-model/docs/23_event_layer_final_judgment.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-model/docs/23_event_layer_final_judgment.md', '/root/projects/trading-model/docs/53_event_layer_final_judgment.md'),
  payload = replace(payload, '/root/projects/trading-model/docs/23_event_layer_final_judgment.md', '/root/projects/trading-model/docs/53_event_layer_final_judgment.md'),
  applies_to = replace(applies_to, '/root/projects/trading-model/docs/23_event_layer_final_judgment.md', '/root/projects/trading-model/docs/53_event_layer_final_judgment.md'),
  note = replace(note, '/root/projects/trading-model/docs/23_event_layer_final_judgment.md', '/root/projects/trading-model/docs/53_event_layer_final_judgment.md')
WHERE path LIKE '%/root/projects/trading-model/docs/23_event_layer_final_judgment.md%' OR payload LIKE '%/root/projects/trading-model/docs/23_event_layer_final_judgment.md%' OR applies_to LIKE '%/root/projects/trading-model/docs/23_event_layer_final_judgment.md%' OR note LIKE '%/root/projects/trading-model/docs/23_event_layer_final_judgment.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-model/docs/23_event_layer_final_judgment.md', 'file:/root/projects/trading-model/docs/53_event_layer_final_judgment.md'),
  payload = replace(payload, 'file:/root/projects/trading-model/docs/23_event_layer_final_judgment.md', 'file:/root/projects/trading-model/docs/53_event_layer_final_judgment.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-model/docs/23_event_layer_final_judgment.md', 'file:/root/projects/trading-model/docs/53_event_layer_final_judgment.md'),
  note = replace(note, 'file:/root/projects/trading-model/docs/23_event_layer_final_judgment.md', 'file:/root/projects/trading-model/docs/53_event_layer_final_judgment.md')
WHERE path LIKE '%file:/root/projects/trading-model/docs/23_event_layer_final_judgment.md%' OR payload LIKE '%file:/root/projects/trading-model/docs/23_event_layer_final_judgment.md%' OR applies_to LIKE '%file:/root/projects/trading-model/docs/23_event_layer_final_judgment.md%' OR note LIKE '%file:/root/projects/trading-model/docs/23_event_layer_final_judgment.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-storage/docs/04_storage_lifecycle.md', 'trading-storage/docs/02_architecture.md'),
  payload = replace(payload, 'trading-storage/docs/04_storage_lifecycle.md', 'trading-storage/docs/02_architecture.md'),
  applies_to = replace(applies_to, 'trading-storage/docs/04_storage_lifecycle.md', 'trading-storage/docs/02_architecture.md'),
  note = replace(note, 'trading-storage/docs/04_storage_lifecycle.md', 'trading-storage/docs/02_architecture.md')
WHERE path LIKE '%trading-storage/docs/04_storage_lifecycle.md%' OR payload LIKE '%trading-storage/docs/04_storage_lifecycle.md%' OR applies_to LIKE '%trading-storage/docs/04_storage_lifecycle.md%' OR note LIKE '%trading-storage/docs/04_storage_lifecycle.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-storage/docs/04_storage_lifecycle.md', '/root/projects/trading-storage/docs/02_architecture.md'),
  payload = replace(payload, '/root/projects/trading-storage/docs/04_storage_lifecycle.md', '/root/projects/trading-storage/docs/02_architecture.md'),
  applies_to = replace(applies_to, '/root/projects/trading-storage/docs/04_storage_lifecycle.md', '/root/projects/trading-storage/docs/02_architecture.md'),
  note = replace(note, '/root/projects/trading-storage/docs/04_storage_lifecycle.md', '/root/projects/trading-storage/docs/02_architecture.md')
WHERE path LIKE '%/root/projects/trading-storage/docs/04_storage_lifecycle.md%' OR payload LIKE '%/root/projects/trading-storage/docs/04_storage_lifecycle.md%' OR applies_to LIKE '%/root/projects/trading-storage/docs/04_storage_lifecycle.md%' OR note LIKE '%/root/projects/trading-storage/docs/04_storage_lifecycle.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-storage/docs/04_storage_lifecycle.md', 'file:/root/projects/trading-storage/docs/02_architecture.md'),
  payload = replace(payload, 'file:/root/projects/trading-storage/docs/04_storage_lifecycle.md', 'file:/root/projects/trading-storage/docs/02_architecture.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-storage/docs/04_storage_lifecycle.md', 'file:/root/projects/trading-storage/docs/02_architecture.md'),
  note = replace(note, 'file:/root/projects/trading-storage/docs/04_storage_lifecycle.md', 'file:/root/projects/trading-storage/docs/02_architecture.md')
WHERE path LIKE '%file:/root/projects/trading-storage/docs/04_storage_lifecycle.md%' OR payload LIKE '%file:/root/projects/trading-storage/docs/04_storage_lifecycle.md%' OR applies_to LIKE '%file:/root/projects/trading-storage/docs/04_storage_lifecycle.md%' OR note LIKE '%file:/root/projects/trading-storage/docs/04_storage_lifecycle.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-storage/docs/05_storage_acceptance.md', 'trading-storage/docs/03_contracts.md'),
  payload = replace(payload, 'trading-storage/docs/05_storage_acceptance.md', 'trading-storage/docs/03_contracts.md'),
  applies_to = replace(applies_to, 'trading-storage/docs/05_storage_acceptance.md', 'trading-storage/docs/03_contracts.md'),
  note = replace(note, 'trading-storage/docs/05_storage_acceptance.md', 'trading-storage/docs/03_contracts.md')
WHERE path LIKE '%trading-storage/docs/05_storage_acceptance.md%' OR payload LIKE '%trading-storage/docs/05_storage_acceptance.md%' OR applies_to LIKE '%trading-storage/docs/05_storage_acceptance.md%' OR note LIKE '%trading-storage/docs/05_storage_acceptance.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-storage/docs/05_storage_acceptance.md', '/root/projects/trading-storage/docs/03_contracts.md'),
  payload = replace(payload, '/root/projects/trading-storage/docs/05_storage_acceptance.md', '/root/projects/trading-storage/docs/03_contracts.md'),
  applies_to = replace(applies_to, '/root/projects/trading-storage/docs/05_storage_acceptance.md', '/root/projects/trading-storage/docs/03_contracts.md'),
  note = replace(note, '/root/projects/trading-storage/docs/05_storage_acceptance.md', '/root/projects/trading-storage/docs/03_contracts.md')
WHERE path LIKE '%/root/projects/trading-storage/docs/05_storage_acceptance.md%' OR payload LIKE '%/root/projects/trading-storage/docs/05_storage_acceptance.md%' OR applies_to LIKE '%/root/projects/trading-storage/docs/05_storage_acceptance.md%' OR note LIKE '%/root/projects/trading-storage/docs/05_storage_acceptance.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-storage/docs/05_storage_acceptance.md', 'file:/root/projects/trading-storage/docs/03_contracts.md'),
  payload = replace(payload, 'file:/root/projects/trading-storage/docs/05_storage_acceptance.md', 'file:/root/projects/trading-storage/docs/03_contracts.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-storage/docs/05_storage_acceptance.md', 'file:/root/projects/trading-storage/docs/03_contracts.md'),
  note = replace(note, 'file:/root/projects/trading-storage/docs/05_storage_acceptance.md', 'file:/root/projects/trading-storage/docs/03_contracts.md')
WHERE path LIKE '%file:/root/projects/trading-storage/docs/05_storage_acceptance.md%' OR payload LIKE '%file:/root/projects/trading-storage/docs/05_storage_acceptance.md%' OR applies_to LIKE '%file:/root/projects/trading-storage/docs/05_storage_acceptance.md%' OR note LIKE '%file:/root/projects/trading-storage/docs/05_storage_acceptance.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-storage/docs/80_task.md', 'trading-storage/docs/04_task.md'),
  payload = replace(payload, 'trading-storage/docs/80_task.md', 'trading-storage/docs/04_task.md'),
  applies_to = replace(applies_to, 'trading-storage/docs/80_task.md', 'trading-storage/docs/04_task.md'),
  note = replace(note, 'trading-storage/docs/80_task.md', 'trading-storage/docs/04_task.md')
WHERE path LIKE '%trading-storage/docs/80_task.md%' OR payload LIKE '%trading-storage/docs/80_task.md%' OR applies_to LIKE '%trading-storage/docs/80_task.md%' OR note LIKE '%trading-storage/docs/80_task.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-storage/docs/80_task.md', '/root/projects/trading-storage/docs/04_task.md'),
  payload = replace(payload, '/root/projects/trading-storage/docs/80_task.md', '/root/projects/trading-storage/docs/04_task.md'),
  applies_to = replace(applies_to, '/root/projects/trading-storage/docs/80_task.md', '/root/projects/trading-storage/docs/04_task.md'),
  note = replace(note, '/root/projects/trading-storage/docs/80_task.md', '/root/projects/trading-storage/docs/04_task.md')
WHERE path LIKE '%/root/projects/trading-storage/docs/80_task.md%' OR payload LIKE '%/root/projects/trading-storage/docs/80_task.md%' OR applies_to LIKE '%/root/projects/trading-storage/docs/80_task.md%' OR note LIKE '%/root/projects/trading-storage/docs/80_task.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-storage/docs/80_task.md', 'file:/root/projects/trading-storage/docs/04_task.md'),
  payload = replace(payload, 'file:/root/projects/trading-storage/docs/80_task.md', 'file:/root/projects/trading-storage/docs/04_task.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-storage/docs/80_task.md', 'file:/root/projects/trading-storage/docs/04_task.md'),
  note = replace(note, 'file:/root/projects/trading-storage/docs/80_task.md', 'file:/root/projects/trading-storage/docs/04_task.md')
WHERE path LIKE '%file:/root/projects/trading-storage/docs/80_task.md%' OR payload LIKE '%file:/root/projects/trading-storage/docs/80_task.md%' OR applies_to LIKE '%file:/root/projects/trading-storage/docs/80_task.md%' OR note LIKE '%file:/root/projects/trading-storage/docs/80_task.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-storage/docs/81_decision.md', 'trading-storage/docs/05_decision.md'),
  payload = replace(payload, 'trading-storage/docs/81_decision.md', 'trading-storage/docs/05_decision.md'),
  applies_to = replace(applies_to, 'trading-storage/docs/81_decision.md', 'trading-storage/docs/05_decision.md'),
  note = replace(note, 'trading-storage/docs/81_decision.md', 'trading-storage/docs/05_decision.md')
WHERE path LIKE '%trading-storage/docs/81_decision.md%' OR payload LIKE '%trading-storage/docs/81_decision.md%' OR applies_to LIKE '%trading-storage/docs/81_decision.md%' OR note LIKE '%trading-storage/docs/81_decision.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-storage/docs/81_decision.md', '/root/projects/trading-storage/docs/05_decision.md'),
  payload = replace(payload, '/root/projects/trading-storage/docs/81_decision.md', '/root/projects/trading-storage/docs/05_decision.md'),
  applies_to = replace(applies_to, '/root/projects/trading-storage/docs/81_decision.md', '/root/projects/trading-storage/docs/05_decision.md'),
  note = replace(note, '/root/projects/trading-storage/docs/81_decision.md', '/root/projects/trading-storage/docs/05_decision.md')
WHERE path LIKE '%/root/projects/trading-storage/docs/81_decision.md%' OR payload LIKE '%/root/projects/trading-storage/docs/81_decision.md%' OR applies_to LIKE '%/root/projects/trading-storage/docs/81_decision.md%' OR note LIKE '%/root/projects/trading-storage/docs/81_decision.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-storage/docs/81_decision.md', 'file:/root/projects/trading-storage/docs/05_decision.md'),
  payload = replace(payload, 'file:/root/projects/trading-storage/docs/81_decision.md', 'file:/root/projects/trading-storage/docs/05_decision.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-storage/docs/81_decision.md', 'file:/root/projects/trading-storage/docs/05_decision.md'),
  note = replace(note, 'file:/root/projects/trading-storage/docs/81_decision.md', 'file:/root/projects/trading-storage/docs/05_decision.md')
WHERE path LIKE '%file:/root/projects/trading-storage/docs/81_decision.md%' OR payload LIKE '%file:/root/projects/trading-storage/docs/81_decision.md%' OR applies_to LIKE '%file:/root/projects/trading-storage/docs/81_decision.md%' OR note LIKE '%file:/root/projects/trading-storage/docs/81_decision.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-storage/docs/82_memory.md', 'trading-storage/docs/06_memory.md'),
  payload = replace(payload, 'trading-storage/docs/82_memory.md', 'trading-storage/docs/06_memory.md'),
  applies_to = replace(applies_to, 'trading-storage/docs/82_memory.md', 'trading-storage/docs/06_memory.md'),
  note = replace(note, 'trading-storage/docs/82_memory.md', 'trading-storage/docs/06_memory.md')
WHERE path LIKE '%trading-storage/docs/82_memory.md%' OR payload LIKE '%trading-storage/docs/82_memory.md%' OR applies_to LIKE '%trading-storage/docs/82_memory.md%' OR note LIKE '%trading-storage/docs/82_memory.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-storage/docs/82_memory.md', '/root/projects/trading-storage/docs/06_memory.md'),
  payload = replace(payload, '/root/projects/trading-storage/docs/82_memory.md', '/root/projects/trading-storage/docs/06_memory.md'),
  applies_to = replace(applies_to, '/root/projects/trading-storage/docs/82_memory.md', '/root/projects/trading-storage/docs/06_memory.md'),
  note = replace(note, '/root/projects/trading-storage/docs/82_memory.md', '/root/projects/trading-storage/docs/06_memory.md')
WHERE path LIKE '%/root/projects/trading-storage/docs/82_memory.md%' OR payload LIKE '%/root/projects/trading-storage/docs/82_memory.md%' OR applies_to LIKE '%/root/projects/trading-storage/docs/82_memory.md%' OR note LIKE '%/root/projects/trading-storage/docs/82_memory.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-storage/docs/82_memory.md', 'file:/root/projects/trading-storage/docs/06_memory.md'),
  payload = replace(payload, 'file:/root/projects/trading-storage/docs/82_memory.md', 'file:/root/projects/trading-storage/docs/06_memory.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-storage/docs/82_memory.md', 'file:/root/projects/trading-storage/docs/06_memory.md'),
  note = replace(note, 'file:/root/projects/trading-storage/docs/82_memory.md', 'file:/root/projects/trading-storage/docs/06_memory.md')
WHERE path LIKE '%file:/root/projects/trading-storage/docs/82_memory.md%' OR payload LIKE '%file:/root/projects/trading-storage/docs/82_memory.md%' OR applies_to LIKE '%file:/root/projects/trading-storage/docs/82_memory.md%' OR note LIKE '%file:/root/projects/trading-storage/docs/82_memory.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-storage/docs/02_layer_01_market_regime.md', 'trading-storage/docs/10_layer_01_market_regime.md'),
  payload = replace(payload, 'trading-storage/docs/02_layer_01_market_regime.md', 'trading-storage/docs/10_layer_01_market_regime.md'),
  applies_to = replace(applies_to, 'trading-storage/docs/02_layer_01_market_regime.md', 'trading-storage/docs/10_layer_01_market_regime.md'),
  note = replace(note, 'trading-storage/docs/02_layer_01_market_regime.md', 'trading-storage/docs/10_layer_01_market_regime.md')
WHERE path LIKE '%trading-storage/docs/02_layer_01_market_regime.md%' OR payload LIKE '%trading-storage/docs/02_layer_01_market_regime.md%' OR applies_to LIKE '%trading-storage/docs/02_layer_01_market_regime.md%' OR note LIKE '%trading-storage/docs/02_layer_01_market_regime.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-storage/docs/02_layer_01_market_regime.md', '/root/projects/trading-storage/docs/10_layer_01_market_regime.md'),
  payload = replace(payload, '/root/projects/trading-storage/docs/02_layer_01_market_regime.md', '/root/projects/trading-storage/docs/10_layer_01_market_regime.md'),
  applies_to = replace(applies_to, '/root/projects/trading-storage/docs/02_layer_01_market_regime.md', '/root/projects/trading-storage/docs/10_layer_01_market_regime.md'),
  note = replace(note, '/root/projects/trading-storage/docs/02_layer_01_market_regime.md', '/root/projects/trading-storage/docs/10_layer_01_market_regime.md')
WHERE path LIKE '%/root/projects/trading-storage/docs/02_layer_01_market_regime.md%' OR payload LIKE '%/root/projects/trading-storage/docs/02_layer_01_market_regime.md%' OR applies_to LIKE '%/root/projects/trading-storage/docs/02_layer_01_market_regime.md%' OR note LIKE '%/root/projects/trading-storage/docs/02_layer_01_market_regime.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-storage/docs/02_layer_01_market_regime.md', 'file:/root/projects/trading-storage/docs/10_layer_01_market_regime.md'),
  payload = replace(payload, 'file:/root/projects/trading-storage/docs/02_layer_01_market_regime.md', 'file:/root/projects/trading-storage/docs/10_layer_01_market_regime.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-storage/docs/02_layer_01_market_regime.md', 'file:/root/projects/trading-storage/docs/10_layer_01_market_regime.md'),
  note = replace(note, 'file:/root/projects/trading-storage/docs/02_layer_01_market_regime.md', 'file:/root/projects/trading-storage/docs/10_layer_01_market_regime.md')
WHERE path LIKE '%file:/root/projects/trading-storage/docs/02_layer_01_market_regime.md%' OR payload LIKE '%file:/root/projects/trading-storage/docs/02_layer_01_market_regime.md%' OR applies_to LIKE '%file:/root/projects/trading-storage/docs/02_layer_01_market_regime.md%' OR note LIKE '%file:/root/projects/trading-storage/docs/02_layer_01_market_regime.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-storage/docs/03_layer_02_sector_context.md', 'trading-storage/docs/11_layer_02_sector_context.md'),
  payload = replace(payload, 'trading-storage/docs/03_layer_02_sector_context.md', 'trading-storage/docs/11_layer_02_sector_context.md'),
  applies_to = replace(applies_to, 'trading-storage/docs/03_layer_02_sector_context.md', 'trading-storage/docs/11_layer_02_sector_context.md'),
  note = replace(note, 'trading-storage/docs/03_layer_02_sector_context.md', 'trading-storage/docs/11_layer_02_sector_context.md')
WHERE path LIKE '%trading-storage/docs/03_layer_02_sector_context.md%' OR payload LIKE '%trading-storage/docs/03_layer_02_sector_context.md%' OR applies_to LIKE '%trading-storage/docs/03_layer_02_sector_context.md%' OR note LIKE '%trading-storage/docs/03_layer_02_sector_context.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-storage/docs/03_layer_02_sector_context.md', '/root/projects/trading-storage/docs/11_layer_02_sector_context.md'),
  payload = replace(payload, '/root/projects/trading-storage/docs/03_layer_02_sector_context.md', '/root/projects/trading-storage/docs/11_layer_02_sector_context.md'),
  applies_to = replace(applies_to, '/root/projects/trading-storage/docs/03_layer_02_sector_context.md', '/root/projects/trading-storage/docs/11_layer_02_sector_context.md'),
  note = replace(note, '/root/projects/trading-storage/docs/03_layer_02_sector_context.md', '/root/projects/trading-storage/docs/11_layer_02_sector_context.md')
WHERE path LIKE '%/root/projects/trading-storage/docs/03_layer_02_sector_context.md%' OR payload LIKE '%/root/projects/trading-storage/docs/03_layer_02_sector_context.md%' OR applies_to LIKE '%/root/projects/trading-storage/docs/03_layer_02_sector_context.md%' OR note LIKE '%/root/projects/trading-storage/docs/03_layer_02_sector_context.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-storage/docs/03_layer_02_sector_context.md', 'file:/root/projects/trading-storage/docs/11_layer_02_sector_context.md'),
  payload = replace(payload, 'file:/root/projects/trading-storage/docs/03_layer_02_sector_context.md', 'file:/root/projects/trading-storage/docs/11_layer_02_sector_context.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-storage/docs/03_layer_02_sector_context.md', 'file:/root/projects/trading-storage/docs/11_layer_02_sector_context.md'),
  note = replace(note, 'file:/root/projects/trading-storage/docs/03_layer_02_sector_context.md', 'file:/root/projects/trading-storage/docs/11_layer_02_sector_context.md')
WHERE path LIKE '%file:/root/projects/trading-storage/docs/03_layer_02_sector_context.md%' OR payload LIKE '%file:/root/projects/trading-storage/docs/03_layer_02_sector_context.md%' OR applies_to LIKE '%file:/root/projects/trading-storage/docs/03_layer_02_sector_context.md%' OR note LIKE '%file:/root/projects/trading-storage/docs/03_layer_02_sector_context.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-storage/docs/06_storage_lifecycle_policy.md', 'trading-storage/docs/20_storage_lifecycle_policy.md'),
  payload = replace(payload, 'trading-storage/docs/06_storage_lifecycle_policy.md', 'trading-storage/docs/20_storage_lifecycle_policy.md'),
  applies_to = replace(applies_to, 'trading-storage/docs/06_storage_lifecycle_policy.md', 'trading-storage/docs/20_storage_lifecycle_policy.md'),
  note = replace(note, 'trading-storage/docs/06_storage_lifecycle_policy.md', 'trading-storage/docs/20_storage_lifecycle_policy.md')
WHERE path LIKE '%trading-storage/docs/06_storage_lifecycle_policy.md%' OR payload LIKE '%trading-storage/docs/06_storage_lifecycle_policy.md%' OR applies_to LIKE '%trading-storage/docs/06_storage_lifecycle_policy.md%' OR note LIKE '%trading-storage/docs/06_storage_lifecycle_policy.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-storage/docs/06_storage_lifecycle_policy.md', '/root/projects/trading-storage/docs/20_storage_lifecycle_policy.md'),
  payload = replace(payload, '/root/projects/trading-storage/docs/06_storage_lifecycle_policy.md', '/root/projects/trading-storage/docs/20_storage_lifecycle_policy.md'),
  applies_to = replace(applies_to, '/root/projects/trading-storage/docs/06_storage_lifecycle_policy.md', '/root/projects/trading-storage/docs/20_storage_lifecycle_policy.md'),
  note = replace(note, '/root/projects/trading-storage/docs/06_storage_lifecycle_policy.md', '/root/projects/trading-storage/docs/20_storage_lifecycle_policy.md')
WHERE path LIKE '%/root/projects/trading-storage/docs/06_storage_lifecycle_policy.md%' OR payload LIKE '%/root/projects/trading-storage/docs/06_storage_lifecycle_policy.md%' OR applies_to LIKE '%/root/projects/trading-storage/docs/06_storage_lifecycle_policy.md%' OR note LIKE '%/root/projects/trading-storage/docs/06_storage_lifecycle_policy.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-storage/docs/06_storage_lifecycle_policy.md', 'file:/root/projects/trading-storage/docs/20_storage_lifecycle_policy.md'),
  payload = replace(payload, 'file:/root/projects/trading-storage/docs/06_storage_lifecycle_policy.md', 'file:/root/projects/trading-storage/docs/20_storage_lifecycle_policy.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-storage/docs/06_storage_lifecycle_policy.md', 'file:/root/projects/trading-storage/docs/20_storage_lifecycle_policy.md'),
  note = replace(note, 'file:/root/projects/trading-storage/docs/06_storage_lifecycle_policy.md', 'file:/root/projects/trading-storage/docs/20_storage_lifecycle_policy.md')
WHERE path LIKE '%file:/root/projects/trading-storage/docs/06_storage_lifecycle_policy.md%' OR payload LIKE '%file:/root/projects/trading-storage/docs/06_storage_lifecycle_policy.md%' OR applies_to LIKE '%file:/root/projects/trading-storage/docs/06_storage_lifecycle_policy.md%' OR note LIKE '%file:/root/projects/trading-storage/docs/06_storage_lifecycle_policy.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-storage/docs/10_lifecycle_receipts.md', 'trading-storage/docs/21_lifecycle_receipts.md'),
  payload = replace(payload, 'trading-storage/docs/10_lifecycle_receipts.md', 'trading-storage/docs/21_lifecycle_receipts.md'),
  applies_to = replace(applies_to, 'trading-storage/docs/10_lifecycle_receipts.md', 'trading-storage/docs/21_lifecycle_receipts.md'),
  note = replace(note, 'trading-storage/docs/10_lifecycle_receipts.md', 'trading-storage/docs/21_lifecycle_receipts.md')
WHERE path LIKE '%trading-storage/docs/10_lifecycle_receipts.md%' OR payload LIKE '%trading-storage/docs/10_lifecycle_receipts.md%' OR applies_to LIKE '%trading-storage/docs/10_lifecycle_receipts.md%' OR note LIKE '%trading-storage/docs/10_lifecycle_receipts.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-storage/docs/10_lifecycle_receipts.md', '/root/projects/trading-storage/docs/21_lifecycle_receipts.md'),
  payload = replace(payload, '/root/projects/trading-storage/docs/10_lifecycle_receipts.md', '/root/projects/trading-storage/docs/21_lifecycle_receipts.md'),
  applies_to = replace(applies_to, '/root/projects/trading-storage/docs/10_lifecycle_receipts.md', '/root/projects/trading-storage/docs/21_lifecycle_receipts.md'),
  note = replace(note, '/root/projects/trading-storage/docs/10_lifecycle_receipts.md', '/root/projects/trading-storage/docs/21_lifecycle_receipts.md')
WHERE path LIKE '%/root/projects/trading-storage/docs/10_lifecycle_receipts.md%' OR payload LIKE '%/root/projects/trading-storage/docs/10_lifecycle_receipts.md%' OR applies_to LIKE '%/root/projects/trading-storage/docs/10_lifecycle_receipts.md%' OR note LIKE '%/root/projects/trading-storage/docs/10_lifecycle_receipts.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-storage/docs/10_lifecycle_receipts.md', 'file:/root/projects/trading-storage/docs/21_lifecycle_receipts.md'),
  payload = replace(payload, 'file:/root/projects/trading-storage/docs/10_lifecycle_receipts.md', 'file:/root/projects/trading-storage/docs/21_lifecycle_receipts.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-storage/docs/10_lifecycle_receipts.md', 'file:/root/projects/trading-storage/docs/21_lifecycle_receipts.md'),
  note = replace(note, 'file:/root/projects/trading-storage/docs/10_lifecycle_receipts.md', 'file:/root/projects/trading-storage/docs/21_lifecycle_receipts.md')
WHERE path LIKE '%file:/root/projects/trading-storage/docs/10_lifecycle_receipts.md%' OR payload LIKE '%file:/root/projects/trading-storage/docs/10_lifecycle_receipts.md%' OR applies_to LIKE '%file:/root/projects/trading-storage/docs/10_lifecycle_receipts.md%' OR note LIKE '%file:/root/projects/trading-storage/docs/10_lifecycle_receipts.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-storage/docs/07_artifact_index.md', 'trading-storage/docs/30_artifact_index.md'),
  payload = replace(payload, 'trading-storage/docs/07_artifact_index.md', 'trading-storage/docs/30_artifact_index.md'),
  applies_to = replace(applies_to, 'trading-storage/docs/07_artifact_index.md', 'trading-storage/docs/30_artifact_index.md'),
  note = replace(note, 'trading-storage/docs/07_artifact_index.md', 'trading-storage/docs/30_artifact_index.md')
WHERE path LIKE '%trading-storage/docs/07_artifact_index.md%' OR payload LIKE '%trading-storage/docs/07_artifact_index.md%' OR applies_to LIKE '%trading-storage/docs/07_artifact_index.md%' OR note LIKE '%trading-storage/docs/07_artifact_index.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-storage/docs/07_artifact_index.md', '/root/projects/trading-storage/docs/30_artifact_index.md'),
  payload = replace(payload, '/root/projects/trading-storage/docs/07_artifact_index.md', '/root/projects/trading-storage/docs/30_artifact_index.md'),
  applies_to = replace(applies_to, '/root/projects/trading-storage/docs/07_artifact_index.md', '/root/projects/trading-storage/docs/30_artifact_index.md'),
  note = replace(note, '/root/projects/trading-storage/docs/07_artifact_index.md', '/root/projects/trading-storage/docs/30_artifact_index.md')
WHERE path LIKE '%/root/projects/trading-storage/docs/07_artifact_index.md%' OR payload LIKE '%/root/projects/trading-storage/docs/07_artifact_index.md%' OR applies_to LIKE '%/root/projects/trading-storage/docs/07_artifact_index.md%' OR note LIKE '%/root/projects/trading-storage/docs/07_artifact_index.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-storage/docs/07_artifact_index.md', 'file:/root/projects/trading-storage/docs/30_artifact_index.md'),
  payload = replace(payload, 'file:/root/projects/trading-storage/docs/07_artifact_index.md', 'file:/root/projects/trading-storage/docs/30_artifact_index.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-storage/docs/07_artifact_index.md', 'file:/root/projects/trading-storage/docs/30_artifact_index.md'),
  note = replace(note, 'file:/root/projects/trading-storage/docs/07_artifact_index.md', 'file:/root/projects/trading-storage/docs/30_artifact_index.md')
WHERE path LIKE '%file:/root/projects/trading-storage/docs/07_artifact_index.md%' OR payload LIKE '%file:/root/projects/trading-storage/docs/07_artifact_index.md%' OR applies_to LIKE '%file:/root/projects/trading-storage/docs/07_artifact_index.md%' OR note LIKE '%file:/root/projects/trading-storage/docs/07_artifact_index.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-storage/docs/08_protected_set.md', 'trading-storage/docs/31_protected_set.md'),
  payload = replace(payload, 'trading-storage/docs/08_protected_set.md', 'trading-storage/docs/31_protected_set.md'),
  applies_to = replace(applies_to, 'trading-storage/docs/08_protected_set.md', 'trading-storage/docs/31_protected_set.md'),
  note = replace(note, 'trading-storage/docs/08_protected_set.md', 'trading-storage/docs/31_protected_set.md')
WHERE path LIKE '%trading-storage/docs/08_protected_set.md%' OR payload LIKE '%trading-storage/docs/08_protected_set.md%' OR applies_to LIKE '%trading-storage/docs/08_protected_set.md%' OR note LIKE '%trading-storage/docs/08_protected_set.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-storage/docs/08_protected_set.md', '/root/projects/trading-storage/docs/31_protected_set.md'),
  payload = replace(payload, '/root/projects/trading-storage/docs/08_protected_set.md', '/root/projects/trading-storage/docs/31_protected_set.md'),
  applies_to = replace(applies_to, '/root/projects/trading-storage/docs/08_protected_set.md', '/root/projects/trading-storage/docs/31_protected_set.md'),
  note = replace(note, '/root/projects/trading-storage/docs/08_protected_set.md', '/root/projects/trading-storage/docs/31_protected_set.md')
WHERE path LIKE '%/root/projects/trading-storage/docs/08_protected_set.md%' OR payload LIKE '%/root/projects/trading-storage/docs/08_protected_set.md%' OR applies_to LIKE '%/root/projects/trading-storage/docs/08_protected_set.md%' OR note LIKE '%/root/projects/trading-storage/docs/08_protected_set.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-storage/docs/08_protected_set.md', 'file:/root/projects/trading-storage/docs/31_protected_set.md'),
  payload = replace(payload, 'file:/root/projects/trading-storage/docs/08_protected_set.md', 'file:/root/projects/trading-storage/docs/31_protected_set.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-storage/docs/08_protected_set.md', 'file:/root/projects/trading-storage/docs/31_protected_set.md'),
  note = replace(note, 'file:/root/projects/trading-storage/docs/08_protected_set.md', 'file:/root/projects/trading-storage/docs/31_protected_set.md')
WHERE path LIKE '%file:/root/projects/trading-storage/docs/08_protected_set.md%' OR payload LIKE '%file:/root/projects/trading-storage/docs/08_protected_set.md%' OR applies_to LIKE '%file:/root/projects/trading-storage/docs/08_protected_set.md%' OR note LIKE '%file:/root/projects/trading-storage/docs/08_protected_set.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-storage/docs/09_compression_archive.md', 'trading-storage/docs/32_compression_archive.md'),
  payload = replace(payload, 'trading-storage/docs/09_compression_archive.md', 'trading-storage/docs/32_compression_archive.md'),
  applies_to = replace(applies_to, 'trading-storage/docs/09_compression_archive.md', 'trading-storage/docs/32_compression_archive.md'),
  note = replace(note, 'trading-storage/docs/09_compression_archive.md', 'trading-storage/docs/32_compression_archive.md')
WHERE path LIKE '%trading-storage/docs/09_compression_archive.md%' OR payload LIKE '%trading-storage/docs/09_compression_archive.md%' OR applies_to LIKE '%trading-storage/docs/09_compression_archive.md%' OR note LIKE '%trading-storage/docs/09_compression_archive.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-storage/docs/09_compression_archive.md', '/root/projects/trading-storage/docs/32_compression_archive.md'),
  payload = replace(payload, '/root/projects/trading-storage/docs/09_compression_archive.md', '/root/projects/trading-storage/docs/32_compression_archive.md'),
  applies_to = replace(applies_to, '/root/projects/trading-storage/docs/09_compression_archive.md', '/root/projects/trading-storage/docs/32_compression_archive.md'),
  note = replace(note, '/root/projects/trading-storage/docs/09_compression_archive.md', '/root/projects/trading-storage/docs/32_compression_archive.md')
WHERE path LIKE '%/root/projects/trading-storage/docs/09_compression_archive.md%' OR payload LIKE '%/root/projects/trading-storage/docs/09_compression_archive.md%' OR applies_to LIKE '%/root/projects/trading-storage/docs/09_compression_archive.md%' OR note LIKE '%/root/projects/trading-storage/docs/09_compression_archive.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-storage/docs/09_compression_archive.md', 'file:/root/projects/trading-storage/docs/32_compression_archive.md'),
  payload = replace(payload, 'file:/root/projects/trading-storage/docs/09_compression_archive.md', 'file:/root/projects/trading-storage/docs/32_compression_archive.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-storage/docs/09_compression_archive.md', 'file:/root/projects/trading-storage/docs/32_compression_archive.md'),
  note = replace(note, 'file:/root/projects/trading-storage/docs/09_compression_archive.md', 'file:/root/projects/trading-storage/docs/32_compression_archive.md')
WHERE path LIKE '%file:/root/projects/trading-storage/docs/09_compression_archive.md%' OR payload LIKE '%file:/root/projects/trading-storage/docs/09_compression_archive.md%' OR applies_to LIKE '%file:/root/projects/trading-storage/docs/09_compression_archive.md%' OR note LIKE '%file:/root/projects/trading-storage/docs/09_compression_archive.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-storage/docs/11_dashboard_read_models.md', 'trading-storage/docs/40_dashboard_read_models.md'),
  payload = replace(payload, 'trading-storage/docs/11_dashboard_read_models.md', 'trading-storage/docs/40_dashboard_read_models.md'),
  applies_to = replace(applies_to, 'trading-storage/docs/11_dashboard_read_models.md', 'trading-storage/docs/40_dashboard_read_models.md'),
  note = replace(note, 'trading-storage/docs/11_dashboard_read_models.md', 'trading-storage/docs/40_dashboard_read_models.md')
WHERE path LIKE '%trading-storage/docs/11_dashboard_read_models.md%' OR payload LIKE '%trading-storage/docs/11_dashboard_read_models.md%' OR applies_to LIKE '%trading-storage/docs/11_dashboard_read_models.md%' OR note LIKE '%trading-storage/docs/11_dashboard_read_models.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-storage/docs/11_dashboard_read_models.md', '/root/projects/trading-storage/docs/40_dashboard_read_models.md'),
  payload = replace(payload, '/root/projects/trading-storage/docs/11_dashboard_read_models.md', '/root/projects/trading-storage/docs/40_dashboard_read_models.md'),
  applies_to = replace(applies_to, '/root/projects/trading-storage/docs/11_dashboard_read_models.md', '/root/projects/trading-storage/docs/40_dashboard_read_models.md'),
  note = replace(note, '/root/projects/trading-storage/docs/11_dashboard_read_models.md', '/root/projects/trading-storage/docs/40_dashboard_read_models.md')
WHERE path LIKE '%/root/projects/trading-storage/docs/11_dashboard_read_models.md%' OR payload LIKE '%/root/projects/trading-storage/docs/11_dashboard_read_models.md%' OR applies_to LIKE '%/root/projects/trading-storage/docs/11_dashboard_read_models.md%' OR note LIKE '%/root/projects/trading-storage/docs/11_dashboard_read_models.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-storage/docs/11_dashboard_read_models.md', 'file:/root/projects/trading-storage/docs/40_dashboard_read_models.md'),
  payload = replace(payload, 'file:/root/projects/trading-storage/docs/11_dashboard_read_models.md', 'file:/root/projects/trading-storage/docs/40_dashboard_read_models.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-storage/docs/11_dashboard_read_models.md', 'file:/root/projects/trading-storage/docs/40_dashboard_read_models.md'),
  note = replace(note, 'file:/root/projects/trading-storage/docs/11_dashboard_read_models.md', 'file:/root/projects/trading-storage/docs/40_dashboard_read_models.md')
WHERE path LIKE '%file:/root/projects/trading-storage/docs/11_dashboard_read_models.md%' OR payload LIKE '%file:/root/projects/trading-storage/docs/11_dashboard_read_models.md%' OR applies_to LIKE '%file:/root/projects/trading-storage/docs/11_dashboard_read_models.md%' OR note LIKE '%file:/root/projects/trading-storage/docs/11_dashboard_read_models.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-storage/docs/12_dashboard_summary_layout.md', 'trading-storage/docs/41_dashboard_summary_layout.md'),
  payload = replace(payload, 'trading-storage/docs/12_dashboard_summary_layout.md', 'trading-storage/docs/41_dashboard_summary_layout.md'),
  applies_to = replace(applies_to, 'trading-storage/docs/12_dashboard_summary_layout.md', 'trading-storage/docs/41_dashboard_summary_layout.md'),
  note = replace(note, 'trading-storage/docs/12_dashboard_summary_layout.md', 'trading-storage/docs/41_dashboard_summary_layout.md')
WHERE path LIKE '%trading-storage/docs/12_dashboard_summary_layout.md%' OR payload LIKE '%trading-storage/docs/12_dashboard_summary_layout.md%' OR applies_to LIKE '%trading-storage/docs/12_dashboard_summary_layout.md%' OR note LIKE '%trading-storage/docs/12_dashboard_summary_layout.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-storage/docs/12_dashboard_summary_layout.md', '/root/projects/trading-storage/docs/41_dashboard_summary_layout.md'),
  payload = replace(payload, '/root/projects/trading-storage/docs/12_dashboard_summary_layout.md', '/root/projects/trading-storage/docs/41_dashboard_summary_layout.md'),
  applies_to = replace(applies_to, '/root/projects/trading-storage/docs/12_dashboard_summary_layout.md', '/root/projects/trading-storage/docs/41_dashboard_summary_layout.md'),
  note = replace(note, '/root/projects/trading-storage/docs/12_dashboard_summary_layout.md', '/root/projects/trading-storage/docs/41_dashboard_summary_layout.md')
WHERE path LIKE '%/root/projects/trading-storage/docs/12_dashboard_summary_layout.md%' OR payload LIKE '%/root/projects/trading-storage/docs/12_dashboard_summary_layout.md%' OR applies_to LIKE '%/root/projects/trading-storage/docs/12_dashboard_summary_layout.md%' OR note LIKE '%/root/projects/trading-storage/docs/12_dashboard_summary_layout.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-storage/docs/12_dashboard_summary_layout.md', 'file:/root/projects/trading-storage/docs/41_dashboard_summary_layout.md'),
  payload = replace(payload, 'file:/root/projects/trading-storage/docs/12_dashboard_summary_layout.md', 'file:/root/projects/trading-storage/docs/41_dashboard_summary_layout.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-storage/docs/12_dashboard_summary_layout.md', 'file:/root/projects/trading-storage/docs/41_dashboard_summary_layout.md'),
  note = replace(note, 'file:/root/projects/trading-storage/docs/12_dashboard_summary_layout.md', 'file:/root/projects/trading-storage/docs/41_dashboard_summary_layout.md')
WHERE path LIKE '%file:/root/projects/trading-storage/docs/12_dashboard_summary_layout.md%' OR payload LIKE '%file:/root/projects/trading-storage/docs/12_dashboard_summary_layout.md%' OR applies_to LIKE '%file:/root/projects/trading-storage/docs/12_dashboard_summary_layout.md%' OR note LIKE '%file:/root/projects/trading-storage/docs/12_dashboard_summary_layout.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-manager/docs/02_model_stack_control_plane.md', 'trading-manager/docs/02_architecture.md'),
  payload = replace(payload, 'trading-manager/docs/02_model_stack_control_plane.md', 'trading-manager/docs/02_architecture.md'),
  applies_to = replace(applies_to, 'trading-manager/docs/02_model_stack_control_plane.md', 'trading-manager/docs/02_architecture.md'),
  note = replace(note, 'trading-manager/docs/02_model_stack_control_plane.md', 'trading-manager/docs/02_architecture.md')
WHERE path LIKE '%trading-manager/docs/02_model_stack_control_plane.md%' OR payload LIKE '%trading-manager/docs/02_model_stack_control_plane.md%' OR applies_to LIKE '%trading-manager/docs/02_model_stack_control_plane.md%' OR note LIKE '%trading-manager/docs/02_model_stack_control_plane.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-manager/docs/02_model_stack_control_plane.md', '/root/projects/trading-manager/docs/02_architecture.md'),
  payload = replace(payload, '/root/projects/trading-manager/docs/02_model_stack_control_plane.md', '/root/projects/trading-manager/docs/02_architecture.md'),
  applies_to = replace(applies_to, '/root/projects/trading-manager/docs/02_model_stack_control_plane.md', '/root/projects/trading-manager/docs/02_architecture.md'),
  note = replace(note, '/root/projects/trading-manager/docs/02_model_stack_control_plane.md', '/root/projects/trading-manager/docs/02_architecture.md')
WHERE path LIKE '%/root/projects/trading-manager/docs/02_model_stack_control_plane.md%' OR payload LIKE '%/root/projects/trading-manager/docs/02_model_stack_control_plane.md%' OR applies_to LIKE '%/root/projects/trading-manager/docs/02_model_stack_control_plane.md%' OR note LIKE '%/root/projects/trading-manager/docs/02_model_stack_control_plane.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-manager/docs/02_model_stack_control_plane.md', 'file:/root/projects/trading-manager/docs/02_architecture.md'),
  payload = replace(payload, 'file:/root/projects/trading-manager/docs/02_model_stack_control_plane.md', 'file:/root/projects/trading-manager/docs/02_architecture.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-manager/docs/02_model_stack_control_plane.md', 'file:/root/projects/trading-manager/docs/02_architecture.md'),
  note = replace(note, 'file:/root/projects/trading-manager/docs/02_model_stack_control_plane.md', 'file:/root/projects/trading-manager/docs/02_architecture.md')
WHERE path LIKE '%file:/root/projects/trading-manager/docs/02_model_stack_control_plane.md%' OR payload LIKE '%file:/root/projects/trading-manager/docs/02_model_stack_control_plane.md%' OR applies_to LIKE '%file:/root/projects/trading-manager/docs/02_model_stack_control_plane.md%' OR note LIKE '%file:/root/projects/trading-manager/docs/02_model_stack_control_plane.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-manager/docs/80_task.md', 'trading-manager/docs/04_task.md'),
  payload = replace(payload, 'trading-manager/docs/80_task.md', 'trading-manager/docs/04_task.md'),
  applies_to = replace(applies_to, 'trading-manager/docs/80_task.md', 'trading-manager/docs/04_task.md'),
  note = replace(note, 'trading-manager/docs/80_task.md', 'trading-manager/docs/04_task.md')
WHERE path LIKE '%trading-manager/docs/80_task.md%' OR payload LIKE '%trading-manager/docs/80_task.md%' OR applies_to LIKE '%trading-manager/docs/80_task.md%' OR note LIKE '%trading-manager/docs/80_task.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-manager/docs/80_task.md', '/root/projects/trading-manager/docs/04_task.md'),
  payload = replace(payload, '/root/projects/trading-manager/docs/80_task.md', '/root/projects/trading-manager/docs/04_task.md'),
  applies_to = replace(applies_to, '/root/projects/trading-manager/docs/80_task.md', '/root/projects/trading-manager/docs/04_task.md'),
  note = replace(note, '/root/projects/trading-manager/docs/80_task.md', '/root/projects/trading-manager/docs/04_task.md')
WHERE path LIKE '%/root/projects/trading-manager/docs/80_task.md%' OR payload LIKE '%/root/projects/trading-manager/docs/80_task.md%' OR applies_to LIKE '%/root/projects/trading-manager/docs/80_task.md%' OR note LIKE '%/root/projects/trading-manager/docs/80_task.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-manager/docs/80_task.md', 'file:/root/projects/trading-manager/docs/04_task.md'),
  payload = replace(payload, 'file:/root/projects/trading-manager/docs/80_task.md', 'file:/root/projects/trading-manager/docs/04_task.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-manager/docs/80_task.md', 'file:/root/projects/trading-manager/docs/04_task.md'),
  note = replace(note, 'file:/root/projects/trading-manager/docs/80_task.md', 'file:/root/projects/trading-manager/docs/04_task.md')
WHERE path LIKE '%file:/root/projects/trading-manager/docs/80_task.md%' OR payload LIKE '%file:/root/projects/trading-manager/docs/80_task.md%' OR applies_to LIKE '%file:/root/projects/trading-manager/docs/80_task.md%' OR note LIKE '%file:/root/projects/trading-manager/docs/80_task.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-manager/docs/81_decision.md', 'trading-manager/docs/05_decision.md'),
  payload = replace(payload, 'trading-manager/docs/81_decision.md', 'trading-manager/docs/05_decision.md'),
  applies_to = replace(applies_to, 'trading-manager/docs/81_decision.md', 'trading-manager/docs/05_decision.md'),
  note = replace(note, 'trading-manager/docs/81_decision.md', 'trading-manager/docs/05_decision.md')
WHERE path LIKE '%trading-manager/docs/81_decision.md%' OR payload LIKE '%trading-manager/docs/81_decision.md%' OR applies_to LIKE '%trading-manager/docs/81_decision.md%' OR note LIKE '%trading-manager/docs/81_decision.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-manager/docs/81_decision.md', '/root/projects/trading-manager/docs/05_decision.md'),
  payload = replace(payload, '/root/projects/trading-manager/docs/81_decision.md', '/root/projects/trading-manager/docs/05_decision.md'),
  applies_to = replace(applies_to, '/root/projects/trading-manager/docs/81_decision.md', '/root/projects/trading-manager/docs/05_decision.md'),
  note = replace(note, '/root/projects/trading-manager/docs/81_decision.md', '/root/projects/trading-manager/docs/05_decision.md')
WHERE path LIKE '%/root/projects/trading-manager/docs/81_decision.md%' OR payload LIKE '%/root/projects/trading-manager/docs/81_decision.md%' OR applies_to LIKE '%/root/projects/trading-manager/docs/81_decision.md%' OR note LIKE '%/root/projects/trading-manager/docs/81_decision.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-manager/docs/81_decision.md', 'file:/root/projects/trading-manager/docs/05_decision.md'),
  payload = replace(payload, 'file:/root/projects/trading-manager/docs/81_decision.md', 'file:/root/projects/trading-manager/docs/05_decision.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-manager/docs/81_decision.md', 'file:/root/projects/trading-manager/docs/05_decision.md'),
  note = replace(note, 'file:/root/projects/trading-manager/docs/81_decision.md', 'file:/root/projects/trading-manager/docs/05_decision.md')
WHERE path LIKE '%file:/root/projects/trading-manager/docs/81_decision.md%' OR payload LIKE '%file:/root/projects/trading-manager/docs/81_decision.md%' OR applies_to LIKE '%file:/root/projects/trading-manager/docs/81_decision.md%' OR note LIKE '%file:/root/projects/trading-manager/docs/81_decision.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-manager/docs/82_memory.md', 'trading-manager/docs/06_memory.md'),
  payload = replace(payload, 'trading-manager/docs/82_memory.md', 'trading-manager/docs/06_memory.md'),
  applies_to = replace(applies_to, 'trading-manager/docs/82_memory.md', 'trading-manager/docs/06_memory.md'),
  note = replace(note, 'trading-manager/docs/82_memory.md', 'trading-manager/docs/06_memory.md')
WHERE path LIKE '%trading-manager/docs/82_memory.md%' OR payload LIKE '%trading-manager/docs/82_memory.md%' OR applies_to LIKE '%trading-manager/docs/82_memory.md%' OR note LIKE '%trading-manager/docs/82_memory.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-manager/docs/82_memory.md', '/root/projects/trading-manager/docs/06_memory.md'),
  payload = replace(payload, '/root/projects/trading-manager/docs/82_memory.md', '/root/projects/trading-manager/docs/06_memory.md'),
  applies_to = replace(applies_to, '/root/projects/trading-manager/docs/82_memory.md', '/root/projects/trading-manager/docs/06_memory.md'),
  note = replace(note, '/root/projects/trading-manager/docs/82_memory.md', '/root/projects/trading-manager/docs/06_memory.md')
WHERE path LIKE '%/root/projects/trading-manager/docs/82_memory.md%' OR payload LIKE '%/root/projects/trading-manager/docs/82_memory.md%' OR applies_to LIKE '%/root/projects/trading-manager/docs/82_memory.md%' OR note LIKE '%/root/projects/trading-manager/docs/82_memory.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-manager/docs/82_memory.md', 'file:/root/projects/trading-manager/docs/06_memory.md'),
  payload = replace(payload, 'file:/root/projects/trading-manager/docs/82_memory.md', 'file:/root/projects/trading-manager/docs/06_memory.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-manager/docs/82_memory.md', 'file:/root/projects/trading-manager/docs/06_memory.md'),
  note = replace(note, 'file:/root/projects/trading-manager/docs/82_memory.md', 'file:/root/projects/trading-manager/docs/06_memory.md')
WHERE path LIKE '%file:/root/projects/trading-manager/docs/82_memory.md%' OR payload LIKE '%file:/root/projects/trading-manager/docs/82_memory.md%' OR applies_to LIKE '%file:/root/projects/trading-manager/docs/82_memory.md%' OR note LIKE '%file:/root/projects/trading-manager/docs/82_memory.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-manager/docs/12_registry.md', 'trading-manager/docs/10_registry.md'),
  payload = replace(payload, 'trading-manager/docs/12_registry.md', 'trading-manager/docs/10_registry.md'),
  applies_to = replace(applies_to, 'trading-manager/docs/12_registry.md', 'trading-manager/docs/10_registry.md'),
  note = replace(note, 'trading-manager/docs/12_registry.md', 'trading-manager/docs/10_registry.md')
WHERE path LIKE '%trading-manager/docs/12_registry.md%' OR payload LIKE '%trading-manager/docs/12_registry.md%' OR applies_to LIKE '%trading-manager/docs/12_registry.md%' OR note LIKE '%trading-manager/docs/12_registry.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-manager/docs/12_registry.md', '/root/projects/trading-manager/docs/10_registry.md'),
  payload = replace(payload, '/root/projects/trading-manager/docs/12_registry.md', '/root/projects/trading-manager/docs/10_registry.md'),
  applies_to = replace(applies_to, '/root/projects/trading-manager/docs/12_registry.md', '/root/projects/trading-manager/docs/10_registry.md'),
  note = replace(note, '/root/projects/trading-manager/docs/12_registry.md', '/root/projects/trading-manager/docs/10_registry.md')
WHERE path LIKE '%/root/projects/trading-manager/docs/12_registry.md%' OR payload LIKE '%/root/projects/trading-manager/docs/12_registry.md%' OR applies_to LIKE '%/root/projects/trading-manager/docs/12_registry.md%' OR note LIKE '%/root/projects/trading-manager/docs/12_registry.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-manager/docs/12_registry.md', 'file:/root/projects/trading-manager/docs/10_registry.md'),
  payload = replace(payload, 'file:/root/projects/trading-manager/docs/12_registry.md', 'file:/root/projects/trading-manager/docs/10_registry.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-manager/docs/12_registry.md', 'file:/root/projects/trading-manager/docs/10_registry.md'),
  note = replace(note, 'file:/root/projects/trading-manager/docs/12_registry.md', 'file:/root/projects/trading-manager/docs/10_registry.md')
WHERE path LIKE '%file:/root/projects/trading-manager/docs/12_registry.md%' OR payload LIKE '%file:/root/projects/trading-manager/docs/12_registry.md%' OR applies_to LIKE '%file:/root/projects/trading-manager/docs/12_registry.md%' OR note LIKE '%file:/root/projects/trading-manager/docs/12_registry.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-manager/docs/13_templates.md', 'trading-manager/docs/11_templates.md'),
  payload = replace(payload, 'trading-manager/docs/13_templates.md', 'trading-manager/docs/11_templates.md'),
  applies_to = replace(applies_to, 'trading-manager/docs/13_templates.md', 'trading-manager/docs/11_templates.md'),
  note = replace(note, 'trading-manager/docs/13_templates.md', 'trading-manager/docs/11_templates.md')
WHERE path LIKE '%trading-manager/docs/13_templates.md%' OR payload LIKE '%trading-manager/docs/13_templates.md%' OR applies_to LIKE '%trading-manager/docs/13_templates.md%' OR note LIKE '%trading-manager/docs/13_templates.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-manager/docs/13_templates.md', '/root/projects/trading-manager/docs/11_templates.md'),
  payload = replace(payload, '/root/projects/trading-manager/docs/13_templates.md', '/root/projects/trading-manager/docs/11_templates.md'),
  applies_to = replace(applies_to, '/root/projects/trading-manager/docs/13_templates.md', '/root/projects/trading-manager/docs/11_templates.md'),
  note = replace(note, '/root/projects/trading-manager/docs/13_templates.md', '/root/projects/trading-manager/docs/11_templates.md')
WHERE path LIKE '%/root/projects/trading-manager/docs/13_templates.md%' OR payload LIKE '%/root/projects/trading-manager/docs/13_templates.md%' OR applies_to LIKE '%/root/projects/trading-manager/docs/13_templates.md%' OR note LIKE '%/root/projects/trading-manager/docs/13_templates.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-manager/docs/13_templates.md', 'file:/root/projects/trading-manager/docs/11_templates.md'),
  payload = replace(payload, 'file:/root/projects/trading-manager/docs/13_templates.md', 'file:/root/projects/trading-manager/docs/11_templates.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-manager/docs/13_templates.md', 'file:/root/projects/trading-manager/docs/11_templates.md'),
  note = replace(note, 'file:/root/projects/trading-manager/docs/13_templates.md', 'file:/root/projects/trading-manager/docs/11_templates.md')
WHERE path LIKE '%file:/root/projects/trading-manager/docs/13_templates.md%' OR payload LIKE '%file:/root/projects/trading-manager/docs/13_templates.md%' OR applies_to LIKE '%file:/root/projects/trading-manager/docs/13_templates.md%' OR note LIKE '%file:/root/projects/trading-manager/docs/13_templates.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-manager/docs/04_task_system.md', 'trading-manager/docs/20_task_system.md'),
  payload = replace(payload, 'trading-manager/docs/04_task_system.md', 'trading-manager/docs/20_task_system.md'),
  applies_to = replace(applies_to, 'trading-manager/docs/04_task_system.md', 'trading-manager/docs/20_task_system.md'),
  note = replace(note, 'trading-manager/docs/04_task_system.md', 'trading-manager/docs/20_task_system.md')
WHERE path LIKE '%trading-manager/docs/04_task_system.md%' OR payload LIKE '%trading-manager/docs/04_task_system.md%' OR applies_to LIKE '%trading-manager/docs/04_task_system.md%' OR note LIKE '%trading-manager/docs/04_task_system.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-manager/docs/04_task_system.md', '/root/projects/trading-manager/docs/20_task_system.md'),
  payload = replace(payload, '/root/projects/trading-manager/docs/04_task_system.md', '/root/projects/trading-manager/docs/20_task_system.md'),
  applies_to = replace(applies_to, '/root/projects/trading-manager/docs/04_task_system.md', '/root/projects/trading-manager/docs/20_task_system.md'),
  note = replace(note, '/root/projects/trading-manager/docs/04_task_system.md', '/root/projects/trading-manager/docs/20_task_system.md')
WHERE path LIKE '%/root/projects/trading-manager/docs/04_task_system.md%' OR payload LIKE '%/root/projects/trading-manager/docs/04_task_system.md%' OR applies_to LIKE '%/root/projects/trading-manager/docs/04_task_system.md%' OR note LIKE '%/root/projects/trading-manager/docs/04_task_system.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-manager/docs/04_task_system.md', 'file:/root/projects/trading-manager/docs/20_task_system.md'),
  payload = replace(payload, 'file:/root/projects/trading-manager/docs/04_task_system.md', 'file:/root/projects/trading-manager/docs/20_task_system.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-manager/docs/04_task_system.md', 'file:/root/projects/trading-manager/docs/20_task_system.md'),
  note = replace(note, 'file:/root/projects/trading-manager/docs/04_task_system.md', 'file:/root/projects/trading-manager/docs/20_task_system.md')
WHERE path LIKE '%file:/root/projects/trading-manager/docs/04_task_system.md%' OR payload LIKE '%file:/root/projects/trading-manager/docs/04_task_system.md%' OR applies_to LIKE '%file:/root/projects/trading-manager/docs/04_task_system.md%' OR note LIKE '%file:/root/projects/trading-manager/docs/04_task_system.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-manager/docs/05_monthly_backfill.md', 'trading-manager/docs/21_monthly_backfill.md'),
  payload = replace(payload, 'trading-manager/docs/05_monthly_backfill.md', 'trading-manager/docs/21_monthly_backfill.md'),
  applies_to = replace(applies_to, 'trading-manager/docs/05_monthly_backfill.md', 'trading-manager/docs/21_monthly_backfill.md'),
  note = replace(note, 'trading-manager/docs/05_monthly_backfill.md', 'trading-manager/docs/21_monthly_backfill.md')
WHERE path LIKE '%trading-manager/docs/05_monthly_backfill.md%' OR payload LIKE '%trading-manager/docs/05_monthly_backfill.md%' OR applies_to LIKE '%trading-manager/docs/05_monthly_backfill.md%' OR note LIKE '%trading-manager/docs/05_monthly_backfill.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-manager/docs/05_monthly_backfill.md', '/root/projects/trading-manager/docs/21_monthly_backfill.md'),
  payload = replace(payload, '/root/projects/trading-manager/docs/05_monthly_backfill.md', '/root/projects/trading-manager/docs/21_monthly_backfill.md'),
  applies_to = replace(applies_to, '/root/projects/trading-manager/docs/05_monthly_backfill.md', '/root/projects/trading-manager/docs/21_monthly_backfill.md'),
  note = replace(note, '/root/projects/trading-manager/docs/05_monthly_backfill.md', '/root/projects/trading-manager/docs/21_monthly_backfill.md')
WHERE path LIKE '%/root/projects/trading-manager/docs/05_monthly_backfill.md%' OR payload LIKE '%/root/projects/trading-manager/docs/05_monthly_backfill.md%' OR applies_to LIKE '%/root/projects/trading-manager/docs/05_monthly_backfill.md%' OR note LIKE '%/root/projects/trading-manager/docs/05_monthly_backfill.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-manager/docs/05_monthly_backfill.md', 'file:/root/projects/trading-manager/docs/21_monthly_backfill.md'),
  payload = replace(payload, 'file:/root/projects/trading-manager/docs/05_monthly_backfill.md', 'file:/root/projects/trading-manager/docs/21_monthly_backfill.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-manager/docs/05_monthly_backfill.md', 'file:/root/projects/trading-manager/docs/21_monthly_backfill.md'),
  note = replace(note, 'file:/root/projects/trading-manager/docs/05_monthly_backfill.md', 'file:/root/projects/trading-manager/docs/21_monthly_backfill.md')
WHERE path LIKE '%file:/root/projects/trading-manager/docs/05_monthly_backfill.md%' OR payload LIKE '%file:/root/projects/trading-manager/docs/05_monthly_backfill.md%' OR applies_to LIKE '%file:/root/projects/trading-manager/docs/05_monthly_backfill.md%' OR note LIKE '%file:/root/projects/trading-manager/docs/05_monthly_backfill.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-manager/docs/06_dataset_expansion.md', 'trading-manager/docs/22_dataset_expansion.md'),
  payload = replace(payload, 'trading-manager/docs/06_dataset_expansion.md', 'trading-manager/docs/22_dataset_expansion.md'),
  applies_to = replace(applies_to, 'trading-manager/docs/06_dataset_expansion.md', 'trading-manager/docs/22_dataset_expansion.md'),
  note = replace(note, 'trading-manager/docs/06_dataset_expansion.md', 'trading-manager/docs/22_dataset_expansion.md')
WHERE path LIKE '%trading-manager/docs/06_dataset_expansion.md%' OR payload LIKE '%trading-manager/docs/06_dataset_expansion.md%' OR applies_to LIKE '%trading-manager/docs/06_dataset_expansion.md%' OR note LIKE '%trading-manager/docs/06_dataset_expansion.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-manager/docs/06_dataset_expansion.md', '/root/projects/trading-manager/docs/22_dataset_expansion.md'),
  payload = replace(payload, '/root/projects/trading-manager/docs/06_dataset_expansion.md', '/root/projects/trading-manager/docs/22_dataset_expansion.md'),
  applies_to = replace(applies_to, '/root/projects/trading-manager/docs/06_dataset_expansion.md', '/root/projects/trading-manager/docs/22_dataset_expansion.md'),
  note = replace(note, '/root/projects/trading-manager/docs/06_dataset_expansion.md', '/root/projects/trading-manager/docs/22_dataset_expansion.md')
WHERE path LIKE '%/root/projects/trading-manager/docs/06_dataset_expansion.md%' OR payload LIKE '%/root/projects/trading-manager/docs/06_dataset_expansion.md%' OR applies_to LIKE '%/root/projects/trading-manager/docs/06_dataset_expansion.md%' OR note LIKE '%/root/projects/trading-manager/docs/06_dataset_expansion.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-manager/docs/06_dataset_expansion.md', 'file:/root/projects/trading-manager/docs/22_dataset_expansion.md'),
  payload = replace(payload, 'file:/root/projects/trading-manager/docs/06_dataset_expansion.md', 'file:/root/projects/trading-manager/docs/22_dataset_expansion.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-manager/docs/06_dataset_expansion.md', 'file:/root/projects/trading-manager/docs/22_dataset_expansion.md'),
  note = replace(note, 'file:/root/projects/trading-manager/docs/06_dataset_expansion.md', 'file:/root/projects/trading-manager/docs/22_dataset_expansion.md')
WHERE path LIKE '%file:/root/projects/trading-manager/docs/06_dataset_expansion.md%' OR payload LIKE '%file:/root/projects/trading-manager/docs/06_dataset_expansion.md%' OR applies_to LIKE '%file:/root/projects/trading-manager/docs/06_dataset_expansion.md%' OR note LIKE '%file:/root/projects/trading-manager/docs/06_dataset_expansion.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-manager/docs/07_controlled_information_pass.md', 'trading-manager/docs/23_controlled_information_pass.md'),
  payload = replace(payload, 'trading-manager/docs/07_controlled_information_pass.md', 'trading-manager/docs/23_controlled_information_pass.md'),
  applies_to = replace(applies_to, 'trading-manager/docs/07_controlled_information_pass.md', 'trading-manager/docs/23_controlled_information_pass.md'),
  note = replace(note, 'trading-manager/docs/07_controlled_information_pass.md', 'trading-manager/docs/23_controlled_information_pass.md')
WHERE path LIKE '%trading-manager/docs/07_controlled_information_pass.md%' OR payload LIKE '%trading-manager/docs/07_controlled_information_pass.md%' OR applies_to LIKE '%trading-manager/docs/07_controlled_information_pass.md%' OR note LIKE '%trading-manager/docs/07_controlled_information_pass.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-manager/docs/07_controlled_information_pass.md', '/root/projects/trading-manager/docs/23_controlled_information_pass.md'),
  payload = replace(payload, '/root/projects/trading-manager/docs/07_controlled_information_pass.md', '/root/projects/trading-manager/docs/23_controlled_information_pass.md'),
  applies_to = replace(applies_to, '/root/projects/trading-manager/docs/07_controlled_information_pass.md', '/root/projects/trading-manager/docs/23_controlled_information_pass.md'),
  note = replace(note, '/root/projects/trading-manager/docs/07_controlled_information_pass.md', '/root/projects/trading-manager/docs/23_controlled_information_pass.md')
WHERE path LIKE '%/root/projects/trading-manager/docs/07_controlled_information_pass.md%' OR payload LIKE '%/root/projects/trading-manager/docs/07_controlled_information_pass.md%' OR applies_to LIKE '%/root/projects/trading-manager/docs/07_controlled_information_pass.md%' OR note LIKE '%/root/projects/trading-manager/docs/07_controlled_information_pass.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-manager/docs/07_controlled_information_pass.md', 'file:/root/projects/trading-manager/docs/23_controlled_information_pass.md'),
  payload = replace(payload, 'file:/root/projects/trading-manager/docs/07_controlled_information_pass.md', 'file:/root/projects/trading-manager/docs/23_controlled_information_pass.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-manager/docs/07_controlled_information_pass.md', 'file:/root/projects/trading-manager/docs/23_controlled_information_pass.md'),
  note = replace(note, 'file:/root/projects/trading-manager/docs/07_controlled_information_pass.md', 'file:/root/projects/trading-manager/docs/23_controlled_information_pass.md')
WHERE path LIKE '%file:/root/projects/trading-manager/docs/07_controlled_information_pass.md%' OR payload LIKE '%file:/root/projects/trading-manager/docs/07_controlled_information_pass.md%' OR applies_to LIKE '%file:/root/projects/trading-manager/docs/07_controlled_information_pass.md%' OR note LIKE '%file:/root/projects/trading-manager/docs/07_controlled_information_pass.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-manager/docs/08_model_promotion.md', 'trading-manager/docs/24_model_promotion.md'),
  payload = replace(payload, 'trading-manager/docs/08_model_promotion.md', 'trading-manager/docs/24_model_promotion.md'),
  applies_to = replace(applies_to, 'trading-manager/docs/08_model_promotion.md', 'trading-manager/docs/24_model_promotion.md'),
  note = replace(note, 'trading-manager/docs/08_model_promotion.md', 'trading-manager/docs/24_model_promotion.md')
WHERE path LIKE '%trading-manager/docs/08_model_promotion.md%' OR payload LIKE '%trading-manager/docs/08_model_promotion.md%' OR applies_to LIKE '%trading-manager/docs/08_model_promotion.md%' OR note LIKE '%trading-manager/docs/08_model_promotion.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-manager/docs/08_model_promotion.md', '/root/projects/trading-manager/docs/24_model_promotion.md'),
  payload = replace(payload, '/root/projects/trading-manager/docs/08_model_promotion.md', '/root/projects/trading-manager/docs/24_model_promotion.md'),
  applies_to = replace(applies_to, '/root/projects/trading-manager/docs/08_model_promotion.md', '/root/projects/trading-manager/docs/24_model_promotion.md'),
  note = replace(note, '/root/projects/trading-manager/docs/08_model_promotion.md', '/root/projects/trading-manager/docs/24_model_promotion.md')
WHERE path LIKE '%/root/projects/trading-manager/docs/08_model_promotion.md%' OR payload LIKE '%/root/projects/trading-manager/docs/08_model_promotion.md%' OR applies_to LIKE '%/root/projects/trading-manager/docs/08_model_promotion.md%' OR note LIKE '%/root/projects/trading-manager/docs/08_model_promotion.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-manager/docs/08_model_promotion.md', 'file:/root/projects/trading-manager/docs/24_model_promotion.md'),
  payload = replace(payload, 'file:/root/projects/trading-manager/docs/08_model_promotion.md', 'file:/root/projects/trading-manager/docs/24_model_promotion.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-manager/docs/08_model_promotion.md', 'file:/root/projects/trading-manager/docs/24_model_promotion.md'),
  note = replace(note, 'file:/root/projects/trading-manager/docs/08_model_promotion.md', 'file:/root/projects/trading-manager/docs/24_model_promotion.md')
WHERE path LIKE '%file:/root/projects/trading-manager/docs/08_model_promotion.md%' OR payload LIKE '%file:/root/projects/trading-manager/docs/08_model_promotion.md%' OR applies_to LIKE '%file:/root/projects/trading-manager/docs/08_model_promotion.md%' OR note LIKE '%file:/root/projects/trading-manager/docs/08_model_promotion.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-manager/docs/09_automation_scheduler.md', 'trading-manager/docs/25_automation_scheduler.md'),
  payload = replace(payload, 'trading-manager/docs/09_automation_scheduler.md', 'trading-manager/docs/25_automation_scheduler.md'),
  applies_to = replace(applies_to, 'trading-manager/docs/09_automation_scheduler.md', 'trading-manager/docs/25_automation_scheduler.md'),
  note = replace(note, 'trading-manager/docs/09_automation_scheduler.md', 'trading-manager/docs/25_automation_scheduler.md')
WHERE path LIKE '%trading-manager/docs/09_automation_scheduler.md%' OR payload LIKE '%trading-manager/docs/09_automation_scheduler.md%' OR applies_to LIKE '%trading-manager/docs/09_automation_scheduler.md%' OR note LIKE '%trading-manager/docs/09_automation_scheduler.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-manager/docs/09_automation_scheduler.md', '/root/projects/trading-manager/docs/25_automation_scheduler.md'),
  payload = replace(payload, '/root/projects/trading-manager/docs/09_automation_scheduler.md', '/root/projects/trading-manager/docs/25_automation_scheduler.md'),
  applies_to = replace(applies_to, '/root/projects/trading-manager/docs/09_automation_scheduler.md', '/root/projects/trading-manager/docs/25_automation_scheduler.md'),
  note = replace(note, '/root/projects/trading-manager/docs/09_automation_scheduler.md', '/root/projects/trading-manager/docs/25_automation_scheduler.md')
WHERE path LIKE '%/root/projects/trading-manager/docs/09_automation_scheduler.md%' OR payload LIKE '%/root/projects/trading-manager/docs/09_automation_scheduler.md%' OR applies_to LIKE '%/root/projects/trading-manager/docs/09_automation_scheduler.md%' OR note LIKE '%/root/projects/trading-manager/docs/09_automation_scheduler.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-manager/docs/09_automation_scheduler.md', 'file:/root/projects/trading-manager/docs/25_automation_scheduler.md'),
  payload = replace(payload, 'file:/root/projects/trading-manager/docs/09_automation_scheduler.md', 'file:/root/projects/trading-manager/docs/25_automation_scheduler.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-manager/docs/09_automation_scheduler.md', 'file:/root/projects/trading-manager/docs/25_automation_scheduler.md'),
  note = replace(note, 'file:/root/projects/trading-manager/docs/09_automation_scheduler.md', 'file:/root/projects/trading-manager/docs/25_automation_scheduler.md')
WHERE path LIKE '%file:/root/projects/trading-manager/docs/09_automation_scheduler.md%' OR payload LIKE '%file:/root/projects/trading-manager/docs/09_automation_scheduler.md%' OR applies_to LIKE '%file:/root/projects/trading-manager/docs/09_automation_scheduler.md%' OR note LIKE '%file:/root/projects/trading-manager/docs/09_automation_scheduler.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-manager/docs/10_historical_scheduler_runtime.md', 'trading-manager/docs/26_historical_scheduler_runtime.md'),
  payload = replace(payload, 'trading-manager/docs/10_historical_scheduler_runtime.md', 'trading-manager/docs/26_historical_scheduler_runtime.md'),
  applies_to = replace(applies_to, 'trading-manager/docs/10_historical_scheduler_runtime.md', 'trading-manager/docs/26_historical_scheduler_runtime.md'),
  note = replace(note, 'trading-manager/docs/10_historical_scheduler_runtime.md', 'trading-manager/docs/26_historical_scheduler_runtime.md')
WHERE path LIKE '%trading-manager/docs/10_historical_scheduler_runtime.md%' OR payload LIKE '%trading-manager/docs/10_historical_scheduler_runtime.md%' OR applies_to LIKE '%trading-manager/docs/10_historical_scheduler_runtime.md%' OR note LIKE '%trading-manager/docs/10_historical_scheduler_runtime.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-manager/docs/10_historical_scheduler_runtime.md', '/root/projects/trading-manager/docs/26_historical_scheduler_runtime.md'),
  payload = replace(payload, '/root/projects/trading-manager/docs/10_historical_scheduler_runtime.md', '/root/projects/trading-manager/docs/26_historical_scheduler_runtime.md'),
  applies_to = replace(applies_to, '/root/projects/trading-manager/docs/10_historical_scheduler_runtime.md', '/root/projects/trading-manager/docs/26_historical_scheduler_runtime.md'),
  note = replace(note, '/root/projects/trading-manager/docs/10_historical_scheduler_runtime.md', '/root/projects/trading-manager/docs/26_historical_scheduler_runtime.md')
WHERE path LIKE '%/root/projects/trading-manager/docs/10_historical_scheduler_runtime.md%' OR payload LIKE '%/root/projects/trading-manager/docs/10_historical_scheduler_runtime.md%' OR applies_to LIKE '%/root/projects/trading-manager/docs/10_historical_scheduler_runtime.md%' OR note LIKE '%/root/projects/trading-manager/docs/10_historical_scheduler_runtime.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-manager/docs/10_historical_scheduler_runtime.md', 'file:/root/projects/trading-manager/docs/26_historical_scheduler_runtime.md'),
  payload = replace(payload, 'file:/root/projects/trading-manager/docs/10_historical_scheduler_runtime.md', 'file:/root/projects/trading-manager/docs/26_historical_scheduler_runtime.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-manager/docs/10_historical_scheduler_runtime.md', 'file:/root/projects/trading-manager/docs/26_historical_scheduler_runtime.md'),
  note = replace(note, 'file:/root/projects/trading-manager/docs/10_historical_scheduler_runtime.md', 'file:/root/projects/trading-manager/docs/26_historical_scheduler_runtime.md')
WHERE path LIKE '%file:/root/projects/trading-manager/docs/10_historical_scheduler_runtime.md%' OR payload LIKE '%file:/root/projects/trading-manager/docs/10_historical_scheduler_runtime.md%' OR applies_to LIKE '%file:/root/projects/trading-manager/docs/10_historical_scheduler_runtime.md%' OR note LIKE '%file:/root/projects/trading-manager/docs/10_historical_scheduler_runtime.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-manager/docs/14_control_plane_acceptance.md', 'trading-manager/docs/27_control_plane_acceptance.md'),
  payload = replace(payload, 'trading-manager/docs/14_control_plane_acceptance.md', 'trading-manager/docs/27_control_plane_acceptance.md'),
  applies_to = replace(applies_to, 'trading-manager/docs/14_control_plane_acceptance.md', 'trading-manager/docs/27_control_plane_acceptance.md'),
  note = replace(note, 'trading-manager/docs/14_control_plane_acceptance.md', 'trading-manager/docs/27_control_plane_acceptance.md')
WHERE path LIKE '%trading-manager/docs/14_control_plane_acceptance.md%' OR payload LIKE '%trading-manager/docs/14_control_plane_acceptance.md%' OR applies_to LIKE '%trading-manager/docs/14_control_plane_acceptance.md%' OR note LIKE '%trading-manager/docs/14_control_plane_acceptance.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-manager/docs/14_control_plane_acceptance.md', '/root/projects/trading-manager/docs/27_control_plane_acceptance.md'),
  payload = replace(payload, '/root/projects/trading-manager/docs/14_control_plane_acceptance.md', '/root/projects/trading-manager/docs/27_control_plane_acceptance.md'),
  applies_to = replace(applies_to, '/root/projects/trading-manager/docs/14_control_plane_acceptance.md', '/root/projects/trading-manager/docs/27_control_plane_acceptance.md'),
  note = replace(note, '/root/projects/trading-manager/docs/14_control_plane_acceptance.md', '/root/projects/trading-manager/docs/27_control_plane_acceptance.md')
WHERE path LIKE '%/root/projects/trading-manager/docs/14_control_plane_acceptance.md%' OR payload LIKE '%/root/projects/trading-manager/docs/14_control_plane_acceptance.md%' OR applies_to LIKE '%/root/projects/trading-manager/docs/14_control_plane_acceptance.md%' OR note LIKE '%/root/projects/trading-manager/docs/14_control_plane_acceptance.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-manager/docs/14_control_plane_acceptance.md', 'file:/root/projects/trading-manager/docs/27_control_plane_acceptance.md'),
  payload = replace(payload, 'file:/root/projects/trading-manager/docs/14_control_plane_acceptance.md', 'file:/root/projects/trading-manager/docs/27_control_plane_acceptance.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-manager/docs/14_control_plane_acceptance.md', 'file:/root/projects/trading-manager/docs/27_control_plane_acceptance.md'),
  note = replace(note, 'file:/root/projects/trading-manager/docs/14_control_plane_acceptance.md', 'file:/root/projects/trading-manager/docs/27_control_plane_acceptance.md')
WHERE path LIKE '%file:/root/projects/trading-manager/docs/14_control_plane_acceptance.md%' OR payload LIKE '%file:/root/projects/trading-manager/docs/14_control_plane_acceptance.md%' OR applies_to LIKE '%file:/root/projects/trading-manager/docs/14_control_plane_acceptance.md%' OR note LIKE '%file:/root/projects/trading-manager/docs/14_control_plane_acceptance.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-manager/docs/15_numbering_physical_contract.md', 'trading-manager/docs/28_numbering_physical_contract.md'),
  payload = replace(payload, 'trading-manager/docs/15_numbering_physical_contract.md', 'trading-manager/docs/28_numbering_physical_contract.md'),
  applies_to = replace(applies_to, 'trading-manager/docs/15_numbering_physical_contract.md', 'trading-manager/docs/28_numbering_physical_contract.md'),
  note = replace(note, 'trading-manager/docs/15_numbering_physical_contract.md', 'trading-manager/docs/28_numbering_physical_contract.md')
WHERE path LIKE '%trading-manager/docs/15_numbering_physical_contract.md%' OR payload LIKE '%trading-manager/docs/15_numbering_physical_contract.md%' OR applies_to LIKE '%trading-manager/docs/15_numbering_physical_contract.md%' OR note LIKE '%trading-manager/docs/15_numbering_physical_contract.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-manager/docs/15_numbering_physical_contract.md', '/root/projects/trading-manager/docs/28_numbering_physical_contract.md'),
  payload = replace(payload, '/root/projects/trading-manager/docs/15_numbering_physical_contract.md', '/root/projects/trading-manager/docs/28_numbering_physical_contract.md'),
  applies_to = replace(applies_to, '/root/projects/trading-manager/docs/15_numbering_physical_contract.md', '/root/projects/trading-manager/docs/28_numbering_physical_contract.md'),
  note = replace(note, '/root/projects/trading-manager/docs/15_numbering_physical_contract.md', '/root/projects/trading-manager/docs/28_numbering_physical_contract.md')
WHERE path LIKE '%/root/projects/trading-manager/docs/15_numbering_physical_contract.md%' OR payload LIKE '%/root/projects/trading-manager/docs/15_numbering_physical_contract.md%' OR applies_to LIKE '%/root/projects/trading-manager/docs/15_numbering_physical_contract.md%' OR note LIKE '%/root/projects/trading-manager/docs/15_numbering_physical_contract.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-manager/docs/15_numbering_physical_contract.md', 'file:/root/projects/trading-manager/docs/28_numbering_physical_contract.md'),
  payload = replace(payload, 'file:/root/projects/trading-manager/docs/15_numbering_physical_contract.md', 'file:/root/projects/trading-manager/docs/28_numbering_physical_contract.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-manager/docs/15_numbering_physical_contract.md', 'file:/root/projects/trading-manager/docs/28_numbering_physical_contract.md'),
  note = replace(note, 'file:/root/projects/trading-manager/docs/15_numbering_physical_contract.md', 'file:/root/projects/trading-manager/docs/28_numbering_physical_contract.md')
WHERE path LIKE '%file:/root/projects/trading-manager/docs/15_numbering_physical_contract.md%' OR payload LIKE '%file:/root/projects/trading-manager/docs/15_numbering_physical_contract.md%' OR applies_to LIKE '%file:/root/projects/trading-manager/docs/15_numbering_physical_contract.md%' OR note LIKE '%file:/root/projects/trading-manager/docs/15_numbering_physical_contract.md%';

UPDATE trading_registry
SET
  path = replace(path, 'trading-manager/docs/11_helpers.md', 'trading-manager/docs/30_helpers.md'),
  payload = replace(payload, 'trading-manager/docs/11_helpers.md', 'trading-manager/docs/30_helpers.md'),
  applies_to = replace(applies_to, 'trading-manager/docs/11_helpers.md', 'trading-manager/docs/30_helpers.md'),
  note = replace(note, 'trading-manager/docs/11_helpers.md', 'trading-manager/docs/30_helpers.md')
WHERE path LIKE '%trading-manager/docs/11_helpers.md%' OR payload LIKE '%trading-manager/docs/11_helpers.md%' OR applies_to LIKE '%trading-manager/docs/11_helpers.md%' OR note LIKE '%trading-manager/docs/11_helpers.md%';

UPDATE trading_registry
SET
  path = replace(path, '/root/projects/trading-manager/docs/11_helpers.md', '/root/projects/trading-manager/docs/30_helpers.md'),
  payload = replace(payload, '/root/projects/trading-manager/docs/11_helpers.md', '/root/projects/trading-manager/docs/30_helpers.md'),
  applies_to = replace(applies_to, '/root/projects/trading-manager/docs/11_helpers.md', '/root/projects/trading-manager/docs/30_helpers.md'),
  note = replace(note, '/root/projects/trading-manager/docs/11_helpers.md', '/root/projects/trading-manager/docs/30_helpers.md')
WHERE path LIKE '%/root/projects/trading-manager/docs/11_helpers.md%' OR payload LIKE '%/root/projects/trading-manager/docs/11_helpers.md%' OR applies_to LIKE '%/root/projects/trading-manager/docs/11_helpers.md%' OR note LIKE '%/root/projects/trading-manager/docs/11_helpers.md%';

UPDATE trading_registry
SET
  path = replace(path, 'file:/root/projects/trading-manager/docs/11_helpers.md', 'file:/root/projects/trading-manager/docs/30_helpers.md'),
  payload = replace(payload, 'file:/root/projects/trading-manager/docs/11_helpers.md', 'file:/root/projects/trading-manager/docs/30_helpers.md'),
  applies_to = replace(applies_to, 'file:/root/projects/trading-manager/docs/11_helpers.md', 'file:/root/projects/trading-manager/docs/30_helpers.md'),
  note = replace(note, 'file:/root/projects/trading-manager/docs/11_helpers.md', 'file:/root/projects/trading-manager/docs/30_helpers.md')
WHERE path LIKE '%file:/root/projects/trading-manager/docs/11_helpers.md%' OR payload LIKE '%file:/root/projects/trading-manager/docs/11_helpers.md%' OR applies_to LIKE '%file:/root/projects/trading-manager/docs/11_helpers.md%' OR note LIKE '%file:/root/projects/trading-manager/docs/11_helpers.md%';
