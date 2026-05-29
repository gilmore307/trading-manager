-- Drop empty pre-renumbering model/feature relations after the 10-layer contract became canonical.
-- This script intentionally refuses to drop any table or materialized view that still contains rows.

DO $$
DECLARE
  target_table text;
  qualified_table text;
  relation_kind "char";
  row_count bigint;
  target_tables text[] := ARRAY[
    'trading_model.model_06_position_projection',
    'trading_model.model_06_position_projection_explainability',
    'trading_model.model_06_position_projection_diagnostics',
    'trading_model.model_07_underlying_action',
    'trading_model.model_07_underlying_action_explainability',
    'trading_model.model_07_underlying_action_diagnostics',
    'trading_model.model_08_option_expression',
    'trading_model.model_08_option_expression_explainability',
    'trading_model.model_08_option_expression_diagnostics',
    'trading_model.model_09_event_risk_governor',
    'trading_model.model_09_event_risk_governor_explainability',
    'trading_model.model_09_event_risk_governor_diagnostics',
    'trading_data.feature_09_event_risk_governor'
  ];
BEGIN
  FOREACH target_table IN ARRAY target_tables LOOP
    SELECT c.oid::regclass::text, c.relkind
    INTO qualified_table, relation_kind
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE c.oid = to_regclass(target_table);

    IF qualified_table IS NULL THEN
      CONTINUE;
    END IF;

    IF relation_kind IN ('r', 'p', 'm') THEN
      EXECUTE format('SELECT count(*) FROM %s', qualified_table) INTO row_count;
      IF row_count <> 0 THEN
        RAISE EXCEPTION 'Refusing to drop %, row_count=%', target_table, row_count;
      END IF;
    END IF;

    IF relation_kind IN ('r', 'p') THEN
      EXECUTE format('DROP TABLE %s', qualified_table);
    ELSIF relation_kind = 'm' THEN
      EXECUTE format('DROP MATERIALIZED VIEW %s', qualified_table);
    ELSIF relation_kind = 'v' THEN
      EXECUTE format('DROP VIEW %s', qualified_table);
    ELSE
      RAISE EXCEPTION 'Refusing to drop %, unsupported relkind=%', target_table, relation_kind;
    END IF;
  END LOOP;
END $$;
