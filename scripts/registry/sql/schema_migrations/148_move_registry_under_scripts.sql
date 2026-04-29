-- Move the registry maintenance surface under scripts/registry/ while leaving
-- runtime helper package code in src/trading_scripts/registry/.

UPDATE trading_registry
SET payload = 'scripts/registry/apply_registry_migrations.py --export-only',
    path = '/root/projects/trading-main/scripts/registry/apply_registry_migrations.py',
    applies_to = 'scripts/registry/current.csv',
    note = 'maintenance helper command that exports the active trading_registry table to scripts/registry/current.csv'
WHERE key = 'HELPER_REGISTRY_EXPORT_CURRENT_CSV';
