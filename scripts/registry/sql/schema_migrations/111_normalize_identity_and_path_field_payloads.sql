-- Normalize identity/path field payloads: single-name payloads are reserved for
-- genuinely generic shared semantics; scoped fields use prefix + semantic suffix.

UPDATE trading_registry
SET key = 'DATA_TASK_CREDENTIAL_CONFIG_ID',
    payload = 'data_task_credential_config_id',
    note = 'data task credential registry config identifier for provider/source credentials. Identity value identifies or names an entity/artifact rather than measuring or locating it.'
WHERE id = 'fld_FJF5ZAJ5';

UPDATE trading_registry
SET key = 'DATA_TASK_RUN_ID',
    payload = 'data_task_run_id',
    note = 'identifier for one invocation of a stable data task key. Identity value identifies or names an entity/artifact rather than measuring or locating it.'
WHERE id = 'fld_F3FORVEW';

UPDATE trading_registry
SET key = 'ISSUER_NAME',
    payload = 'issuer_name',
    note = 'issuer/source/sponsor display name shared by ETF holdings and curated instrument universes. Identity value identifies or names an entity/artifact rather than measuring or locating it.'
WHERE id = 'fld_ETFH002';

UPDATE trading_registry
SET key = 'OPTION_EVENT_DETAIL_SOURCE_PROVIDER_NAME',
    payload = 'source_provider_name',
    note = 'source provider display name for option event detail source context. Identity value identifies or names an entity/artifact rather than measuring or locating it.'
WHERE id = 'fld_OPD014';

UPDATE trading_registry
SET key = 'OPTION_EVENT_DETAIL_STANDARD_ID',
    payload = 'option_event_detail_standard_id',
    note = 'stable random identifier for the model-produced option event detail standard snapshot. Identity value identifies or names an entity/artifact rather than measuring or locating it.'
WHERE id = 'fld_OPD046';

UPDATE trading_registry
SET key = 'OPTION_EVENT_DETAIL_STANDARD_SOURCE_NAME',
    payload = 'option_event_detail_standard_source_name',
    note = 'source/model name that produced the option event detail event-time current standard. Identity value identifies or names an entity/artifact rather than measuring or locating it.'
WHERE id = 'fld_OPD045';

UPDATE trading_registry
SET key = 'SOURCE_NAME',
    payload = 'source_name',
    note = 'provider/source display name for documentation or shared mixed-source payloads. Identity value identifies or names an entity/artifact rather than measuring or locating it.'
WHERE id = 'fld_EKIND002';

UPDATE trading_registry
SET key = 'TIMELINE_HEADLINE',
    payload = 'timeline_headline',
    note = 'human-readable event timeline headline; for option_activity_event it should read like a news headline and mention only triggered abnormal indicators. Identity value identifies or names an entity/artifact rather than measuring or locating it.'
WHERE id = 'fld_EVT001';

UPDATE trading_registry
SET key = 'EVENT_LINK_URL',
    payload = 'event_link_url',
    note = 'URL or local artifact link for article, news, and event timeline rows. Path value locates or references an artifact, file, URL, source reference, output reference, or repository path.'
WHERE id = 'fld_EVT007';

UPDATE trading_registry
SET key = 'EVENT_SOURCE_REFERENCE',
    payload = 'source_reference',
    note = 'compact source reference such as SEC accession number, article id/url, option event detail id, or release-calendar id. Path value locates or references an artifact, file, URL, source reference, output reference, or repository path.'
WHERE id = 'fld_EVT017';

UPDATE trading_registry
SET key = 'SOURCE_REFERENCES',
    payload = 'source_references',
    note = 'canonical compact source-reference field for event evidence templates. Path value locates or references an artifact, file, URL, source reference, output reference, or repository path.'
WHERE id = 'fld_ABN008';

UPDATE trading_registry
SET key = 'STOCK_ETF_SOURCE_SNAPSHOT_REFERENCES',
    payload = 'source_snapshot_references',
    note = 'source ETF holdings snapshot references used to build this exposure row. Path value locates or references an artifact, file, URL, source reference, output reference, or repository path.'
WHERE id = 'fld_STKEX010';

UPDATE trading_registry
SET key = 'REGISTRY_ITEM_PATH',
    payload = 'registry_item_path',
    note = 'canonical path/locator field for trading_registry.path. Path value locates or references an artifact, file, URL, source reference, output reference, or repository path.'
WHERE id = 'fld_M7Q2P8TZ';

UPDATE trading_registry
SET key = 'DATA_KIND_TEMPLATE_PREVIEW_FILE_PATH',
    payload = 'data_kind_template_preview_file_path',
    note = 'small CSV preview/template file path in the source-specific folder for the final saved data-kind schema. Path value locates or references an artifact, file, URL, source reference, output reference, or repository path.'
WHERE id = 'fld_EKIND011';

UPDATE trading_registry
SET key = 'DATA_TASK_RUN_OUTPUT_DIRECTORY',
    payload = 'data_task_run_output_directory',
    note = 'development output directory for one data task run. Path value locates or references an artifact, file, URL, source reference, output reference, or repository path.'
WHERE id = 'fld_U3G3BLPO';

UPDATE trading_registry
SET key = 'DATA_TASK_RUN_OUTPUT_REFERENCES',
    payload = 'data_task_run_output_references',
    note = 'per-run output file or artifact references. Path value locates or references an artifact, file, URL, source reference, output reference, or repository path.'
WHERE id = 'fld_ES5OZEMA';

UPDATE trading_registry
SET key = 'EXECUTION_ALLOWED_PATHS',
    payload = 'execution_allowed_paths',
    note = 'allowed path slots for execution keys. Path value locates or references an artifact, file, URL, source reference, output reference, or repository path.'
WHERE id = 'fld_YLTWJKTJ';

UPDATE trading_registry
SET key = 'EXECUTION_BLOCKED_PATHS',
    payload = 'execution_blocked_paths',
    note = 'blocked path slots for execution keys. Path value locates or references an artifact, file, URL, source reference, output reference, or repository path.'
WHERE id = 'fld_H2OBUVA0';

UPDATE trading_registry
SET key = 'COMPLETION_CHANGED_FILE_PATHS',
    payload = 'completion_changed_file_paths',
    note = 'changed file path list slots for completion receipts. Path value locates or references an artifact, file, URL, source reference, output reference, or repository path.'
WHERE id = 'fld_9BAEN7ZS';

UPDATE trading_registry
SET key = 'ACCEPTANCE_REVIEWED_FILE_PATHS',
    payload = 'acceptance_reviewed_file_paths',
    note = 'reviewed file path list slots for acceptance receipts. Path value locates or references an artifact, file, URL, source reference, output reference, or repository path.'
WHERE id = 'fld_Q9KQLPH4';

UPDATE trading_registry
SET kind = 'field',
    key = 'TRADING_ECONOMICS_REFERENCE_PERIOD',
    payload = 'reference_period',
    note = 'Trading Economics calendar reference period; this is a source-visible period label, not a locator/path reference.'
WHERE id = 'fld_TEC005';


UPDATE trading_registry
SET payload = 'event_report_url',
    note = 'local or object-store URL for the Markdown or human-readable event analysis report artifact. Path value locates or references an artifact, file, URL, source reference, output reference, or repository path.'
WHERE id = 'fld_EVT034';

UPDATE trading_registry
SET payload = 'event_report_json_url',
    note = 'local or object-store URL for the structured JSON sidecar extracted from the event analysis report. Path value locates or references an artifact, file, URL, source reference, output reference, or repository path.'
WHERE id = 'fld_EVT035';


UPDATE trading_registry
SET payload = 'event_analysis_report_url',
    note = 'local or object-store URL pointing to the long-form agent/model analysis report artifact for this event. Path value locates or references an artifact, file, URL, source reference, output reference, or repository path.'
WHERE id = 'fld_EVT021';
