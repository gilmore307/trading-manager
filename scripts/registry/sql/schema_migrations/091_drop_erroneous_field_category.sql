-- Remove the erroneous field_category registry column added in migration 089.
-- The field grouping attempt was reverted because field categories must be redesigned
-- as a stricter registry model instead of bolted onto field rows.

DROP INDEX IF EXISTS idx_trading_registry_field_category;

ALTER TABLE trading_registry
DROP CONSTRAINT IF EXISTS trading_registry_field_category_required_check;

ALTER TABLE trading_registry
DROP CONSTRAINT IF EXISTS trading_registry_field_category_value_check;

ALTER TABLE trading_registry
DROP COLUMN IF EXISTS field_category;

CREATE OR REPLACE FUNCTION set_trading_registry_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  IF ROW(NEW.kind, NEW.key, NEW.payload_format, NEW.payload, NEW.path, NEW.applies_to, NEW.artifact_sync_policy, NEW.note)
     IS DISTINCT FROM
     ROW(OLD.kind, OLD.key, OLD.payload_format, OLD.payload, OLD.path, OLD.applies_to, OLD.artifact_sync_policy, OLD.note) THEN
    NEW.updated_at = NOW();
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
