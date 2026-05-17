-- Align registry doc locators with the first-principles trading-manager docs spine.

UPDATE trading_registry
SET path = replace(path, 'trading-manager/docs/93_contracts.md', 'trading-manager/docs/03_contracts.md')
WHERE path LIKE '%trading-manager/docs/93_contracts.md%';

UPDATE trading_registry
SET path = replace(path, '/root/projects/trading-manager/docs/93_contracts.md', '/root/projects/trading-manager/docs/03_contracts.md')
WHERE path LIKE '%/root/projects/trading-manager/docs/93_contracts.md%';

UPDATE trading_registry
SET path = replace(path, 'trading-manager/docs/95_task_system.md', 'trading-manager/docs/04_task_system.md')
WHERE path LIKE '%trading-manager/docs/95_task_system.md%';

UPDATE trading_registry
SET path = replace(path, 'trading-manager/docs/94_monthly_backfill.md', 'trading-manager/docs/05_monthly_backfill.md')
WHERE path LIKE '%trading-manager/docs/94_monthly_backfill.md%';

UPDATE trading_registry
SET path = replace(path, 'trading-manager/docs/100_dataset_expansion.md', 'trading-manager/docs/06_dataset_expansion.md')
WHERE path LIKE '%trading-manager/docs/100_dataset_expansion.md%';

UPDATE trading_registry
SET path = replace(path, 'trading-manager/docs/101_controlled_information_pass.md', 'trading-manager/docs/07_controlled_information_pass.md')
WHERE path LIKE '%trading-manager/docs/101_controlled_information_pass.md%';

UPDATE trading_registry
SET path = replace(path, 'trading-manager/docs/96_model_promotion.md', 'trading-manager/docs/08_model_promotion.md')
WHERE path LIKE '%trading-manager/docs/96_model_promotion.md%';

UPDATE trading_registry
SET path = replace(path, 'trading-manager/docs/98_automation_scheduler.md', 'trading-manager/docs/09_automation_scheduler.md')
WHERE path LIKE '%trading-manager/docs/98_automation_scheduler.md%';

UPDATE trading_registry
SET path = replace(path, 'trading-manager/docs/99_historical_scheduler_runtime.md', 'trading-manager/docs/10_historical_scheduler_runtime.md')
WHERE path LIKE '%trading-manager/docs/99_historical_scheduler_runtime.md%';

UPDATE trading_registry
SET path = replace(path, 'trading-manager/docs/90_helpers.md', 'trading-manager/docs/11_helpers.md')
WHERE path LIKE '%trading-manager/docs/90_helpers.md%';

UPDATE trading_registry
SET path = replace(path, 'trading-manager/docs/91_registry.md', 'trading-manager/docs/12_registry.md')
WHERE path LIKE '%trading-manager/docs/91_registry.md%';

UPDATE trading_registry
SET path = replace(path, 'trading-manager/docs/92_templates.md', 'trading-manager/docs/13_templates.md')
WHERE path LIKE '%trading-manager/docs/92_templates.md%';

UPDATE trading_registry
SET path = replace(path, 'trading-manager/docs/97_manager_control_plane_closeout.md', 'trading-manager/docs/14_control_plane_acceptance.md')
WHERE path LIKE '%trading-manager/docs/97_manager_control_plane_closeout.md%';

UPDATE trading_registry
SET path = replace(path, 'trading-manager/docs/103_numbering_physical_audit.md', 'trading-manager/docs/15_numbering_physical_contract.md')
WHERE path LIKE '%trading-manager/docs/103_numbering_physical_audit.md%';
