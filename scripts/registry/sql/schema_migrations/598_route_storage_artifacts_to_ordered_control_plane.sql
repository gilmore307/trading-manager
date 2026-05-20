UPDATE trading_registry
SET note = replace(note, 'storage/artifacts', 'storage/02_control_plane/artifacts'),
    updated_at = now()
WHERE note LIKE '%storage/artifacts%';

UPDATE trading_registry
SET payload = replace(payload, 'storage/artifacts', 'storage/02_control_plane/artifacts'),
    updated_at = now()
WHERE payload LIKE '%storage/artifacts%';

UPDATE trading_registry
SET applies_to = replace(applies_to, 'storage/artifacts', 'storage/02_control_plane/artifacts'),
    updated_at = now()
WHERE applies_to LIKE '%storage/artifacts%';
