-- Clarify that data task JSON templates should stay minimal and operational.
-- Target engine: PostgreSQL.

UPDATE trading_registry
SET note = 'minimal draft manager-issued historical data task key template; include only fields used by manager handoff and bundle execution; not an accepted schema until contract review'
WHERE id = 'out_SGC6SHTM';

UPDATE trading_registry
SET note = 'minimal draft completion receipt template for development receipts; include only fields used for task status, output references, row counts, and error evidence; durable receipt contract remains future work'
WHERE id = 'out_ERYNXVJ3';
