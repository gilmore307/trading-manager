# Field

## Kind Boundary

Canonical shared field names used in task records, receipts, manifests, requests, review artifacts, maintenance outputs, and helper-facing schemas.

## Range

Use for field-name registrations only. Do not use for status values, repo names, or config values.

## Entries

| id | key | payload_format | payload | note | source_migration |
|---|---|---|---|---|---|
| `fld_GI3OL5K5` | `ACCEPTANCE_OUTCOME` | `text` | `acceptance_outcome` | canonical shared field name for acceptance outcome slots | `002_bootstrap_universal_catalog.sql` |
| `fld_J6FURQOE` | `ACCEPTANCE_REFERENCE` | `text` | `acceptance_reference` | canonical shared field name for acceptance reference slots | `002_bootstrap_universal_catalog.sql` |
| `fld_XYGQ3TIC` | `ACCEPTANCE_SUMMARY` | `text` | `acceptance_summary` | canonical shared field name for acceptance summary slots | `002_bootstrap_universal_catalog.sql` |
| `fld_YLTWJKTJ` | `ALLOWED_PATHS` | `text` | `allowed_paths` | canonical shared field name for allowed path slots | `002_bootstrap_universal_catalog.sql` |
| `fld_H2OBUVA0` | `BLOCKED_PATHS` | `text` | `blocked_paths` | canonical shared field name for blocked path slots | `002_bootstrap_universal_catalog.sql` |
| `fld_FN9DUG5U` | `BLOCKED_TASK_LIST` | `text` | `blocked_task_list` | canonical shared field name for blocked task list slots | `002_bootstrap_universal_catalog.sql` |
| `fld_P8L2C4TY` | `CATALOG_ITEM_CREATED_AT` | `text` | `created_at` | canonical column name for the historical registry table column created_at | `002_bootstrap_universal_catalog.sql` |
| `fld_A7K3P2Q9` | `CATALOG_ITEM_ID` | `text` | `id` | canonical column name for the historical registry table column id | `002_bootstrap_universal_catalog.sql` |
| `fld_R7P1C6LW` | `CATALOG_ITEM_KEY` | `text` | `key` | canonical column name for the historical registry table column key | `002_bootstrap_universal_catalog.sql` |
| `fld_M4N8X2KD` | `CATALOG_ITEM_KIND` | `text` | `kind` | canonical column name for the historical registry table column kind | `002_bootstrap_universal_catalog.sql` |
| `fld_D3W7K1RM` | `CATALOG_ITEM_NOTE` | `text` | `note` | canonical column name for the historical registry table column note | `002_bootstrap_universal_catalog.sql` |
| `fld_B6J4N8XP` | `CATALOG_ITEM_PAYLOAD` | `text` | `payload` | canonical column name for the historical registry table column payload | `002_bootstrap_universal_catalog.sql` |
| `fld_T9V2H5QS` | `CATALOG_ITEM_PAYLOAD_FORMAT` | `text` | `payload_format` | canonical column name for the historical registry table column payload_format | `002_bootstrap_universal_catalog.sql` |
| `fld_Q5F9M2NZ` | `CATALOG_ITEM_UPDATED_AT` | `text` | `updated_at` | canonical column name for the historical registry table column updated_at | `002_bootstrap_universal_catalog.sql` |
| `fld_9BAEN7ZS` | `CHANGED_FILES` | `text` | `changed_files` | canonical shared field name for changed file list slots | `002_bootstrap_universal_catalog.sql` |
| `fld_GNNVKXOG` | `CHANGE_SUMMARY` | `text` | `change_summary` | canonical shared field name for change summary slots | `002_bootstrap_universal_catalog.sql` |
| `fld_B29IDITT` | `CHECK_TIME` | `text` | `check_time` | canonical shared field name for maintenance check time slots | `002_bootstrap_universal_catalog.sql` |
| `fld_EIWWF5B5` | `COMMAND_LIST` | `text` | `command_list` | canonical shared field name for command list slots | `002_bootstrap_universal_catalog.sql` |
| `fld_H6WM9AVU` | `COMPLETION_RECEIPT_REFERENCE` | `text` | `completion_receipt_reference` | canonical shared field name for completion receipt reference slots | `002_bootstrap_universal_catalog.sql` |
| `fld_5NFMUN7N` | `CONSTRAINTS` | `text` | `constraints` | canonical shared field name for execution constraint slots | `002_bootstrap_universal_catalog.sql` |
| `fld_F4OFEVFJ` | `DECISION_REFERENCES` | `text` | `decision_references` | canonical shared field name for decision reference slots | `002_bootstrap_universal_catalog.sql` |
| `fld_4UWS48ZI` | `DICTIONARY_ISSUE_LIST` | `text` | `dictionary_issue_list` | canonical shared field name for dictionary issue list slots | `002_bootstrap_universal_catalog.sql` |
| `fld_2EZ9JU7F` | `DOCS_STATUS` | `text` | `docs_status` | canonical shared field name for docs status slots | `002_bootstrap_universal_catalog.sql` |
| `fld_RSIXOXTB` | `EXPECTED_OUTPUT` | `text` | `expected_output` | canonical shared field name for expected output slots | `002_bootstrap_universal_catalog.sql` |
| `fld_4ZRFN5AJ` | `FOLLOW_UP_TASK_LIST` | `text` | `follow_up_task_list` | canonical shared field name for follow-up task list slots | `002_bootstrap_universal_catalog.sql` |
| `fld_GXYBK246` | `ISSUE_LIST` | `text` | `issue_list` | canonical shared field name for issue list slots | `002_bootstrap_universal_catalog.sql` |
| `fld_BME8UR38` | `MAINTENANCE_STATUS` | `text` | `maintenance_status` | canonical shared field name for maintenance status slots | `002_bootstrap_universal_catalog.sql` |
| `fld_37IEP8QF` | `MAINTENANCE_SUMMARY` | `text` | `maintenance_summary` | canonical shared field name for maintenance summary slots | `002_bootstrap_universal_catalog.sql` |
| `fld_4BVOLV5F` | `MEMORY_ROUTE_ISSUE_LIST` | `text` | `memory_route_issue_list` | canonical shared field name for memory route issue list slots | `002_bootstrap_universal_catalog.sql` |
| `fld_BJGL5P8K` | `NEXT_TASK_REFERENCE` | `text` | `next_task_reference` | canonical shared field name for next task reference slots | `002_bootstrap_universal_catalog.sql` |
| `fld_Z7TPA496` | `OUTPUT_REFERENCE` | `text` | `output_reference` | canonical shared field name for output reference slots | `002_bootstrap_universal_catalog.sql` |
| `fld_WNQIX52F` | `PENDING_ACCEPTANCE_LIST` | `text` | `pending_acceptance_list` | canonical shared field name for pending acceptance list slots | `002_bootstrap_universal_catalog.sql` |
| `fld_O9Y3PMML` | `PENDING_DISPATCH_LIST` | `text` | `pending_dispatch_list` | canonical shared field name for pending dispatch list slots | `002_bootstrap_universal_catalog.sql` |
| `fld_4YALJN0B` | `REPOSITORY_PATH` | `text` | `repository_path` | canonical shared field name for repository path slots | `002_bootstrap_universal_catalog.sql` |
| `fld_6XFD3B1C` | `REVIEWED_COMMANDS` | `text` | `reviewed_commands` | canonical shared field name for reviewed command list slots | `002_bootstrap_universal_catalog.sql` |
| `fld_Q9KQLPH4` | `REVIEWED_FILES` | `text` | `reviewed_files` | canonical shared field name for reviewed file list slots | `002_bootstrap_universal_catalog.sql` |
| `fld_6RJNNWV1` | `REVIEW_READINESS` | `text` | `review_readiness` | canonical shared field name for review readiness slots | `002_bootstrap_universal_catalog.sql` |
| `fld_SBU4RCHA` | `SPLIT_ISSUE_LIST` | `text` | `split_issue_list` | canonical shared field name for split issue list slots | `002_bootstrap_universal_catalog.sql` |
| `fld_PVUM9JE5` | `TASK_GOAL` | `text` | `task_goal` | canonical shared field name for task goal slots | `002_bootstrap_universal_catalog.sql` |
| `fld_7X5H7N6Y` | `TASK_IDENTITY` | `text` | `task_identity` | canonical shared field name for task identity slots | `002_bootstrap_universal_catalog.sql` |
| `fld_5DVSJFM0` | `TASK_LIFECYCLE_STATE` | `text` | `task_lifecycle_state` | canonical shared field name for task lifecycle state slots | `002_bootstrap_universal_catalog.sql` |
| `fld_RSO93XMM` | `TASK_SCOPE` | `text` | `task_scope` | canonical shared field name for task scope slots | `002_bootstrap_universal_catalog.sql` |
| `fld_W9NA62KA` | `TASK_STATUS_SUMMARY` | `text` | `task_status_summary` | canonical shared field name for task status summary slots | `002_bootstrap_universal_catalog.sql` |
| `fld_VTD4KDTM` | `TEMPORARY_NEW_NAMES` | `text` | `temporary_new_names` | canonical shared field name for temporary new name slots | `002_bootstrap_universal_catalog.sql` |
| `fld_U27NM0BU` | `TEST_COMMANDS` | `text` | `test_commands` | canonical shared field name for test command slots | `002_bootstrap_universal_catalog.sql` |
| `fld_0YVMMK1A` | `TEST_EXPECTATION` | `text` | `test_expectation` | canonical shared field name for test expectation slots | `002_bootstrap_universal_catalog.sql` |
| `fld_YX5TMJN9` | `TEST_OUTPUT` | `text` | `test_output` | canonical shared field name for test output slots | `002_bootstrap_universal_catalog.sql` |
| `fld_T5PSOYKO` | `TEST_STATUS` | `text` | `test_status` | canonical shared field name for test status slots | `002_bootstrap_universal_catalog.sql` |
| `fld_ZGTS8P3D` | `WORKFLOW_IDENTITY` | `text` | `workflow_identity` | canonical shared field name for workflow identity slots | `002_bootstrap_universal_catalog.sql` |
