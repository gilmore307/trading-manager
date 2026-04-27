-- Register GDELT news acquisition bundle and article source-evidence data kind.
-- Target engine: PostgreSQL.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  ('dbu_GDELTN1', 'data_bundle', 'GDELT_NEWS', 'text', 'gdelt_news', 'trading-data/src/trading_data/data_sources/gdelt_news', 'trading-data;event_database', 'sync_artifact', 'Implemented GDELT BigQuery-backed global news source-evidence bundle for political, economic, technology, geopolitical, sector, and broad-market event discovery'),
  ('dki_GDELTART', 'data_kind', 'GDELT_ARTICLE', 'text', 'gdelt_article', 'trading-data/storage/templates/data_kinds/gdelt/gdelt_article.preview.csv', 'gdelt_news', 'sync_artifact', 'Final saved GDELT article/source-evidence row; later event extraction/clustering projects rows into trading_event/event_factor without duplicating SEC/company official disclosures'),
  ('fld_GDLT001', 'field', 'GDELT_ARTICLE_ID', 'text', 'article_id', 'trading-data/storage/templates/data_kinds/gdelt/gdelt_article.preview.csv', 'gdelt_article_template', 'sync_artifact', 'GDELT GKG record id or stable source article identifier'),
  ('fld_GDLT002', 'field', 'GDELT_ARTICLE_SEEN_AT_UTC', 'text', 'seen_at_utc', 'trading-data/storage/templates/data_kinds/gdelt/gdelt_article.preview.csv', 'gdelt_article_template', 'sync_artifact', 'GDELT article observation timestamp normalized to UTC'),
  ('fld_GDLT003', 'field', 'GDELT_SOURCE_DOMAIN', 'text', 'source_domain', 'trading-data/storage/templates/data_kinds/gdelt/gdelt_article.preview.csv', 'gdelt_article_template', 'sync_artifact', 'GDELT source common name/domain for the article'),
  ('fld_GDLT004', 'field', 'GDELT_ARTICLE_URL', 'text', 'url', 'trading-data/storage/templates/data_kinds/gdelt/gdelt_article.preview.csv', 'gdelt_article_template', 'sync_artifact', 'canonical article/document URL from GDELT'),
  ('fld_GDLT005', 'field', 'GDELT_ARTICLE_LANGUAGE', 'text', 'language', 'trading-data/storage/templates/data_kinds/gdelt/gdelt_article.preview.csv', 'gdelt_article_template', 'sync_artifact', 'article language when available from the selected GDELT surface'),
  ('fld_GDLT006', 'field', 'GDELT_SOURCE_COUNTRY', 'text', 'source_country', 'trading-data/storage/templates/data_kinds/gdelt/gdelt_article.preview.csv', 'gdelt_article_template', 'sync_artifact', 'source country when available from the selected GDELT surface'),
  ('fld_GDLT007', 'field', 'GDELT_ARTICLE_TITLE', 'text', 'title', 'trading-data/storage/templates/data_kinds/gdelt/gdelt_article.preview.csv', 'gdelt_article_template', 'sync_artifact', 'article title when available from the selected GDELT surface'),
  ('fld_GDLT008', 'field', 'GDELT_THEMES', 'text', 'themes', 'trading-data/storage/templates/data_kinds/gdelt/gdelt_article.preview.csv', 'gdelt_article_template', 'sync_artifact', 'GDELT theme string used as source evidence for downstream event extraction'),
  ('fld_GDLT009', 'field', 'GDELT_PERSONS', 'text', 'persons', 'trading-data/storage/templates/data_kinds/gdelt/gdelt_article.preview.csv', 'gdelt_article_template', 'sync_artifact', 'GDELT person entities string'),
  ('fld_GDLT010', 'field', 'GDELT_ORGANIZATIONS', 'text', 'organizations', 'trading-data/storage/templates/data_kinds/gdelt/gdelt_article.preview.csv', 'gdelt_article_template', 'sync_artifact', 'GDELT organization entities string'),
  ('fld_GDLT011', 'field', 'GDELT_LOCATIONS', 'text', 'locations', 'trading-data/storage/templates/data_kinds/gdelt/gdelt_article.preview.csv', 'gdelt_article_template', 'sync_artifact', 'GDELT location entities string'),
  ('fld_GDLT012', 'field', 'GDELT_TONE', 'text', 'tone', 'trading-data/storage/templates/data_kinds/gdelt/gdelt_article.preview.csv', 'gdelt_article_template', 'sync_artifact', 'GDELT tone score or selected tone component'),
  ('fld_GDLT013', 'field', 'GDELT_SHARING_IMAGE', 'text', 'sharing_image', 'trading-data/storage/templates/data_kinds/gdelt/gdelt_article.preview.csv', 'gdelt_article_template', 'sync_artifact', 'GDELT sharing/social image URL when available'),
  ('fld_GDLT014', 'field', 'GDELT_IMPACT_SCOPE_HINT', 'text', 'impact_scope_hint', 'trading-data/storage/templates/data_kinds/gdelt/gdelt_article.preview.csv', 'gdelt_article_template', 'sync_artifact', 'initial broad impact-scope hint for downstream event extraction'),
  ('fld_GDLT015', 'field', 'GDELT_SOURCE_TYPE', 'text', 'source_type', 'trading-data/storage/templates/data_kinds/gdelt/gdelt_article.preview.csv', 'gdelt_article_template', 'sync_artifact', 'source type for GDELT article evidence, usually gdelt_gkg_article')
ON CONFLICT (id) DO UPDATE
SET kind = EXCLUDED.kind,
    key = EXCLUDED.key,
    payload_format = EXCLUDED.payload_format,
    payload = EXCLUDED.payload,
    path = EXCLUDED.path,
    applies_to = EXCLUDED.applies_to,
    artifact_sync_policy = EXCLUDED.artifact_sync_policy,
    note = EXCLUDED.note;
