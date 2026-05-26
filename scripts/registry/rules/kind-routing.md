# Kind Routing Rules

Use the narrowest kind that states what the row actually is.

## Field-Like Rows

| Row role | Kind |
|---|---|
| entity id, symbol, name, title, headline | `identity_field` |
| path, URL, source ref, output ref, artifact locator | `path_field` |
| date, time, timestamp, availability/effective/window bound | `temporal_field` |
| category/type/scope/tag/status slot | `classification_field` |
| free-text summary, explanation, error, caveat, note | `text_field` |
| request/task parameter object or parameter collection | `parameter_field` |
| metric, count, boolean, score, generic structured slot | `field` |

Allowed values for a status slot are `status_value`; the slot carrying them is `classification_field`.

## Data Rows

| Row role | Kind |
|---|---|
| provider organization/platform/source owner | `provider` |
| implemented feed adapter or data-access interface | `data_feed` |
| feed endpoint family, record family, entitlement capability | `feed_capability` |
| manager-requestable source output | `data_source` |
| deterministic model-facing feature output | `data_feature` |
| final saved data shape with accepted storage contract | `data_kind` |

## Automation Rows

| Row role | Kind |
|---|---|
| stable callable command/export | `script` |
| checked-in systemd service/timer/path unit file | `systemd_unit` |
| canonical SQL table name | `sql_table` |
| durable checked-in shared data/config file | `shared_artifact` |
| repository identity | `repo` |
| non-secret config or secret alias | `config` |
| request category | `request_type` |
| artifact category | `artifact_type` |
| manifest category | `manifest_type` |
| ready-signal category | `ready_signal_type` |
| registry payload-format token | `payload_format` |
| system dictionary concept / shared noun definition | `term` |

## Rejection Defaults

Do not register:

- secret values;
- generated payload blobs;
- runtime scratch paths;
- unreviewed experiment labels;
- ordinary implementation files as scripts;
- duplicate semantics under different keys;
- broad terms when a concrete field/status/source/feed kind applies.
