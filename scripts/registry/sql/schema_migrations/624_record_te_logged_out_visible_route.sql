-- Record the current Trading Economics route: logged-out visible calendar pages
-- for recent/future maintenance and completed one-time replay seed coverage.

UPDATE trading_registry
SET note = '07 data feed for conservative Trading Economics visible-page U.S. high-impact macro calendar rows. Current accepted operation uses logged-out visible-page recent/custom calendar requests with no authenticated cookies by default; historical replay seed coverage is complete and ongoing maintenance fetches recent/future rows.',
    updated_at = NOW()
WHERE key = 'TRADING_ECONOMICS_CALENDAR_WEB';

UPDATE trading_registry
SET note = 'Trading Economics visible calendar web-page capability; intentionally excludes API/download endpoints, uses logged-out recent/custom pages by default, and is not itself a final data_kind.',
    updated_at = NOW()
WHERE key = 'TRADING_ECONOMICS_CALENDAR_PAGE';

UPDATE trading_registry
SET note = 'Provider/feed-owner identity for Trading Economics. The accepted runtime calendar route is logged-out visible-page recent/custom fetches without API/download/export use or authenticated cookies by default.',
    updated_at = NOW()
WHERE key = 'TRADING_ECONOMICS';
