-- Limit provider rows to current source-interface providers. Historical,
-- fallback, secret-only, or non-data-source platforms remain terms/configs until an
-- active source interface needs provider semantics again.

UPDATE trading_registry
SET kind = 'term',
    payload = 'BEA API reference',
    applies_to = 'historical_macro_provider_reference',
    note = 'historical/available official macro API reference retained for documentation and secret-alias context only; not a current provider row because no active source interface routes through BEA'
WHERE key = 'BEA';

UPDATE trading_registry
SET kind = 'term',
    payload = 'BLS API reference',
    applies_to = 'historical_macro_provider_reference',
    note = 'historical/available official macro API reference retained for documentation and secret-alias context only; not a current provider row because no active source interface routes through BLS'
WHERE key = 'BLS';

UPDATE trading_registry
SET kind = 'term',
    payload = 'Census API reference',
    applies_to = 'historical_macro_provider_reference',
    note = 'historical/available official macro API reference retained for documentation and secret-alias context only; not a current provider row because no active source interface routes through Census'
WHERE key = 'CENSUS';

UPDATE trading_registry
SET kind = 'term',
    payload = 'FRED/St. Louis Fed/ALFRED reference',
    applies_to = 'historical_macro_provider_reference',
    note = 'historical/available FRED/St. Louis Fed/ALFRED-native reference retained for explicitly reviewed research exceptions; not a current provider row and must not duplicate official-agency source routes'
WHERE key = 'FRED';

UPDATE trading_registry
SET kind = 'term',
    payload = 'GitHub code hosting reference',
    applies_to = 'git_operations',
    note = 'code-hosting platform reference for repository operations; not a trading-data/source-interface provider row'
WHERE key = 'GITHUB';

UPDATE trading_registry
SET kind = 'term',
    payload = 'U.S. Treasury Fiscal Data API reference',
    applies_to = 'historical_macro_provider_reference',
    note = 'historical/available official Treasury Fiscal Data API reference retained for documentation only; not a current provider row because no active source interface routes through it'
WHERE key = 'US_TREASURY_FISCAL_DATA';
