-- Register bid-side option activity trigger fields.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'fld_OPD069',
    'field',
    'OPTION_EVENT_TRIGGER_TRADE_AT_BID',
    'field_name',
    'trade_at_bid',
    'trading-data/src/data_feed/11_feed_thetadata_option_event_timeline/pipeline.py',
    'option_activity_event_detail;option_abnormality_coverage;directional_activity_evidence',
    'sync_artifact',
    'Bid-side trade trigger for option activity events; complements trade_at_ask so bid-side flow can be sampled explicitly.'
  ),
  (
    'fld_OPD070',
    'field',
    'OPTION_EVENT_STANDARD_MAX_PRICE_VS_BID',
    'field_name',
    'max_price_vs_bid',
    'trading-data/src/data_feed/11_feed_thetadata_option_event_timeline/pipeline.py',
    'option_activity_event_standard;option_abnormality_coverage;directional_activity_evidence',
    'sync_artifact',
    'Current-standard threshold for maximum bid-minus-trade-price distance when classifying bid-side option trades.'
  ),
  (
    'fld_OPD071',
    'field',
    'OPTION_EVENT_STANDARD_MIN_BID_TOUCH_RATIO',
    'field_name',
    'min_bid_touch_ratio',
    'trading-data/src/data_feed/11_feed_thetadata_option_event_timeline/pipeline.py',
    'option_activity_event_standard;option_abnormality_coverage;directional_activity_evidence',
    'sync_artifact',
    'Current-standard threshold for bid-touch ratio when classifying bid-side option trades.'
  )
ON CONFLICT (id) DO UPDATE
SET kind = EXCLUDED.kind,
    key = EXCLUDED.key,
    payload_format = EXCLUDED.payload_format,
    payload = EXCLUDED.payload,
    path = EXCLUDED.path,
    applies_to = EXCLUDED.applies_to,
    artifact_sync_policy = EXCLUDED.artifact_sync_policy,
    note = EXCLUDED.note,
    updated_at = NOW();
