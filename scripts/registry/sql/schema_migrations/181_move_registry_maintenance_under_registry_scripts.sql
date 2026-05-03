-- Move the registered registry export helper to the nested scripts/registry boundary.
UPDATE trading_registry
SET payload = 'scripts/registry/apply_registry_migrations.py --export-only',
    path = '/root/projects/trading-manager/scripts/registry/apply_registry_migrations.py',
    applies_to = 'scripts/registry/current.csv',
    note = 'Exports the SQL-backed registry table to scripts/registry/current.csv for GitHub-visible review.',
    updated_at = NOW()
WHERE id = 'scr_CV8R2M5J';
