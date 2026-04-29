-- Unify normalized ticker/symbol vocabulary and remove ambiguous event security id.
-- In normalized project-facing fields, use symbol for tradable identifiers.
-- Keep ticker only in provider/source prose where it is the external term.

UPDATE trading_registry
SET key = 'ETF_SYMBOL',
    payload = 'etf_symbol',
    note = 'ETF symbol whose issuer-published holdings are represented. Identity value identifies or names an entity/artifact rather than measuring or locating it.'
WHERE id = 'fld_ETFH001';

UPDATE trading_registry
SET key = 'ETF_HOLDING_SYMBOL',
    payload = 'holding_symbol',
    note = 'Constituent security symbol from issuer-published holdings. Identity value identifies or names an entity/artifact rather than measuring or locating it.'
WHERE id = 'fld_ETFH004';

DELETE FROM trading_registry
WHERE id = 'fld_EVT011';
