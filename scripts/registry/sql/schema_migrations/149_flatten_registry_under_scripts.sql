UPDATE trading_registry
SET payload = 'scripts/apply_registry_migrations.py --export-only',
    path = '/root/projects/trading-main/scripts/apply_registry_migrations.py',
    applies_to = 'scripts/current.csv',
    note = 'Exports the SQL-backed registry table to scripts/current.csv for GitHub-visible review.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'helper-registry-export-current-csv';
