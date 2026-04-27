-- Merge reusable option quote fields while keeping event-detail-only fields scoped to option events.
-- Target engine: PostgreSQL.

-- Reusable option quote primitives: option chain quote contexts and option event quote contexts
-- now share the same leaf names where the meaning is the same.
UPDATE trading_registry
SET
  applies_to = 'option_template;option_chain_snapshot_template;option_activity_event_detail_template',
  note = 'option bid price in quote contexts'
WHERE kind = 'field'
  AND key = 'OPTION_TEMPLATE_BID';

UPDATE trading_registry
SET
  applies_to = 'option_template;option_chain_snapshot_template;option_activity_event_detail_template',
  note = 'option ask price in quote contexts'
WHERE kind = 'field'
  AND key = 'OPTION_TEMPLATE_ASK';

UPDATE trading_registry
SET
  applies_to = 'option_template;option_chain_snapshot_template;option_activity_event_detail_template',
  note = 'option quote midpoint price in quote contexts'
WHERE kind = 'field'
  AND key = 'OPTION_TEMPLATE_MID';

UPDATE trading_registry
SET
  applies_to = 'option_template;option_chain_snapshot_template;option_activity_event_detail_template',
  note = 'option ask minus bid spread in quote contexts'
WHERE kind = 'field'
  AND key = 'OPTION_TEMPLATE_SPREAD';

UPDATE trading_registry
SET
  applies_to = 'market_data_template;option_bar_template;option_chain_snapshot_template;option_activity_event_detail_template',
  note = 'timestamp in America/New_York shared by final bar outputs and nested option quote/snapshot contexts'
WHERE kind = 'field'
  AND key = 'DATA_TIMESTAMP_ET';

-- Remove event-only quote leaf rows that were made redundant by the reusable option quote fields.
DELETE FROM trading_registry
WHERE kind = 'field'
  AND key IN (
    'QUOTE_ASK',
    'QUOTE_BID',
    'QUOTE_MID',
    'QUOTE_SPREAD',
    'QUOTE_TIMESTAMP_ET'
  );

-- Restore option-event-detail key scope for fields that are still specific to the event detail artifact.
UPDATE trading_registry
SET
  key = 'OPTION_EVENT_DETAIL_QUOTE_CONTEXT',
  note = 'nested quote context near the triggering option activity event'
WHERE kind = 'field'
  AND key = 'QUOTE_CONTEXT';

UPDATE trading_registry
SET
  key = 'OPTION_EVENT_DETAIL_ASK_TOUCH_RATIO',
  note = 'observed ratio/indicator showing how closely the triggering trade touched the contemporaneous ask'
WHERE kind = 'field'
  AND key = 'QUOTE_ASK_TOUCH_RATIO';

UPDATE trading_registry
SET
  key = 'OPTION_EVENT_DETAIL_TRADE_PRICE',
  note = 'triggering trade price in the emitted option activity event detail'
WHERE kind = 'field'
  AND key = 'TRADE_PRICE';

UPDATE trading_registry
SET
  key = 'OPTION_EVENT_DETAIL_TRADE_SIZE',
  note = 'triggering trade size in the emitted option activity event detail'
WHERE kind = 'field'
  AND key = 'TRADE_SIZE';

UPDATE trading_registry
SET
  key = 'OPTION_EVENT_DETAIL_TRADE_TIMESTAMP_ET',
  note = 'triggering trade timestamp in America/New_York for the emitted option activity event detail'
WHERE kind = 'field'
  AND key = 'TRADE_TIMESTAMP_ET';

UPDATE trading_registry
SET
  key = 'OPTION_EVENT_DETAIL_PRICE_VS_ASK',
  note = 'triggering trade price minus contemporaneous ask metric used to identify ask-side option activity'
WHERE kind = 'field'
  AND key = 'TRADE_PRICE_VS_ASK';
