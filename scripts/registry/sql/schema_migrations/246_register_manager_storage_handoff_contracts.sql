-- Register manager/storage V1 handoff contracts and non-production hardening policies.
-- These rows define stable control-plane vocabulary only; they do not approve
-- production promotion, live execution, or unattended provider calls.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_MSH001',
    'config',
    'MANAGER_STORAGE_HANDOFF_CONTRACTS',
    'text',
    'manager_request_v1;run_manifest_v1;artifact_ref_v1;ready_signal_v1',
    'trading-storage/main/templates/contracts/README.md',
    'trading-manager;trading-storage;control_plane;handoff_contracts;production_hardening',
    'sync_artifact',
    'Accepted V1 logical handoff contracts for manager-issued requests, run manifests, immutable artifact references, and downstream ready signals. Physical SQL/storage implementation remains pending.'
  ),
  (
    'cfg_MSH002',
    'config',
    'MANAGER_REQUEST_V1_REQUIRED_FIELDS',
    'text',
    'contract_version;request_id;idempotency_key;requester;target_repo;target_workflow;request_type;production_mode;priority;created_at;not_before;parameters;input_artifact_refs;expected_output_types;live_call_policy;retry_policy;cancellation_policy',
    'trading-storage/main/templates/contracts/request.md',
    'manager_request_v1;trading-manager;control_plane;request_contract',
    'sync_artifact',
    'Required logical fields for manager_request_v1. Secrets must be referenced by alias/config id only, and live provider calls are disabled unless the request policy explicitly permits them.'
  ),
  (
    'cfg_MSH003',
    'config',
    'RUN_MANIFEST_V1_REQUIRED_FIELDS',
    'text',
    'contract_version;manifest_id;request_id;run_id;producer_repo;workflow_id;workflow_kind;started_at;finished_at;run_status;git_commit;git_dirty;config_refs;input_artifact_refs;output_artifact_refs;validation_checks;ready_signal_policy',
    'trading-storage/main/templates/contracts/manifest.md',
    'run_manifest_v1;trading-storage;run_evidence;production_hardening',
    'sync_artifact',
    'Required logical fields for run_manifest_v1. Manifests record run evidence but do not authorize downstream consumption without a ready signal.'
  ),
  (
    'cfg_MSH004',
    'config',
    'ARTIFACT_REF_V1_REQUIRED_FIELDS',
    'text',
    'contract_version;artifact_id;artifact_type;producer_repo;producer_workflow;produced_at;storage_backend;storage_uri;content_format;schema_ref;content_hash_sha256;mutability;visibility_time;retention_policy;manifest_id',
    'trading-storage/main/templates/contracts/artifact.md',
    'artifact_ref_v1;trading-storage;artifact_reference;durable_storage',
    'sync_artifact',
    'Required logical fields for artifact_ref_v1. Production artifacts must be immutable and must not point to ignored local development storage paths.'
  ),
  (
    'cfg_MSH005',
    'config',
    'READY_SIGNAL_V1_REQUIRED_FIELDS',
    'text',
    'contract_version;signal_id;signal_type;producer_repo;workflow_id;manifest_refs;artifact_refs;ready_status;ready_at;valid_after;consumption_scope;blocking_policy',
    'trading-storage/main/templates/contracts/ready_signal.md',
    'ready_signal_v1;trading-storage;downstream_consumability;control_plane',
    'sync_artifact',
    'Required logical fields for ready_signal_v1. Consumers must reject/wait on not_ready, failed, unknown, superseded, or expired signals.'
  ),
  (
    'cfg_MSH006',
    'config',
    'DATA_PRODUCTION_HARDENING_POLICY',
    'text',
    'live_calls_disabled_by_default;explicit_live_call_policy_required;retry_backoff_required_for_live_calls;checkpoint_resume_required_for_segmented_runs;durable_manifest_required;ready_signal_required_for_downstream_consumption;secrets_by_alias_only;ignored_local_storage_not_durable',
    'trading-data/docs/96_production_hardening.md',
    'trading-data;trading-manager;production_hardening;data_source;data_feed;control_plane',
    'sync_artifact',
    'Accepted non-production hardening policy that can be implemented before accumulated production data exists. It does not approve unattended production orchestration.'
  ),
  (
    'cfg_MSH007',
    'config',
    'CHECKPOINT_RESUME_POLICY',
    'text',
    'segment_id_required;segment_status_required;last_successful_cursor_required;retry_count_recorded;provider_window_recorded;resume_must_be_idempotent;partial_segments_not_ready',
    'trading-data/docs/96_production_hardening.md',
    'trading-data;segmented_runs;checkpoint_resume;run_manifest_v1',
    'sync_artifact',
    'Accepted checkpoint/resume evidence policy for segmented data/feed runs. Partial segments do not emit ready signals unless explicitly reviewed as partial_ready.'
  ),
  (
    'cfg_MSH008',
    'config',
    'LIVE_CALL_GUARDRAILS_POLICY',
    'text',
    'provider_allowlist_required;max_requests_required;max_window_required;dry_run_default;retry_after_respected;rate_limit_backoff_recorded;secret_values_never_logged;manual_approval_required_for_production_mode',
    'trading-data/docs/96_production_hardening.md',
    'trading-data;provider_calls;live_call_policy;control_plane;production_hardening',
    'sync_artifact',
    'Accepted live-call guardrails policy for provider/API access before unattended production use.'
  ),
  (
    'req_MSH001',
    'request_type',
    'DATA_SOURCE_RUN_REQUEST',
    'text',
    'data_source_run',
    'trading-storage/main/templates/contracts/request.md',
    'manager_request_v1;trading-data;data_source',
    'registry_only',
    'Request type for manager-issued data_source runs.'
  ),
  (
    'req_MSH002',
    'request_type',
    'DATA_FEATURE_RUN_REQUEST',
    'text',
    'data_feature_run',
    'trading-storage/main/templates/contracts/request.md',
    'manager_request_v1;trading-data;data_feature',
    'registry_only',
    'Request type for manager-issued data_feature generation runs.'
  ),
  (
    'req_MSH003',
    'request_type',
    'MODEL_GENERATE_RUN_REQUEST',
    'text',
    'model_generate_run',
    'trading-storage/main/templates/contracts/request.md',
    'manager_request_v1;trading-model;model_generate',
    'registry_only',
    'Request type for manager-issued model generation runs.'
  ),
  (
    'req_MSH004',
    'request_type',
    'MODEL_EVALUATE_RUN_REQUEST',
    'text',
    'model_evaluate_run',
    'trading-storage/main/templates/contracts/request.md',
    'manager_request_v1;trading-model;model_evaluate',
    'registry_only',
    'Request type for manager-issued model evaluation runs.'
  ),
  (
    'req_MSH005',
    'request_type',
    'MODEL_REVIEW_RUN_REQUEST',
    'text',
    'model_review_run',
    'trading-storage/main/templates/contracts/request.md',
    'manager_request_v1;trading-model;model_review;promotion_review',
    'registry_only',
    'Request type for manager-issued or reviewer-agent model review runs.'
  ),
  (
    'mft_MSH001',
    'manifest_type',
    'RUN_MANIFEST_V1',
    'text',
    'run_manifest_v1',
    'trading-storage/main/templates/contracts/manifest.md',
    'run_evidence;trading-data;trading-model;trading-manager',
    'registry_only',
    'Manifest type for durable run evidence across trading repositories.'
  ),
  (
    'art_MSH001',
    'artifact_type',
    'DATA_SOURCE_OUTPUT_ARTIFACT',
    'text',
    'data_source_output',
    'trading-storage/main/templates/contracts/artifact.md',
    'artifact_ref_v1;trading-data;data_source',
    'registry_only',
    'Artifact type for durable data_source outputs.'
  ),
  (
    'art_MSH002',
    'artifact_type',
    'DATA_FEATURE_OUTPUT_ARTIFACT',
    'text',
    'data_feature_output',
    'trading-storage/main/templates/contracts/artifact.md',
    'artifact_ref_v1;trading-data;data_feature',
    'registry_only',
    'Artifact type for durable data_feature outputs.'
  ),
  (
    'art_MSH003',
    'artifact_type',
    'MODEL_OUTPUT_ARTIFACT',
    'text',
    'model_output',
    'trading-storage/main/templates/contracts/artifact.md',
    'artifact_ref_v1;trading-model;model_generate',
    'registry_only',
    'Artifact type for durable model output rows/files.'
  ),
  (
    'art_MSH004',
    'artifact_type',
    'MODEL_EVAL_LABELS_ARTIFACT',
    'text',
    'model_eval_labels',
    'trading-storage/main/templates/contracts/artifact.md',
    'artifact_ref_v1;trading-model;model_evaluation;promotion_evidence',
    'registry_only',
    'Artifact type for durable model evaluation labels.'
  ),
  (
    'art_MSH005',
    'artifact_type',
    'MODEL_PROMOTION_EVIDENCE_ARTIFACT',
    'text',
    'model_promotion_evidence',
    'trading-storage/main/templates/contracts/artifact.md',
    'artifact_ref_v1;trading-model;model_promotion;promotion_evidence',
    'registry_only',
    'Artifact type for durable model promotion evidence packages.'
  ),
  (
    'art_MSH006',
    'artifact_type',
    'REGISTRY_SNAPSHOT_ARTIFACT',
    'text',
    'registry_snapshot',
    'trading-storage/main/templates/contracts/artifact.md',
    'artifact_ref_v1;trading-manager;registry',
    'registry_only',
    'Artifact type for durable registry snapshots such as current.csv exports.'
  ),
  (
    'rst_MSH001',
    'ready_signal_type',
    'DATA_SOURCE_READY_SIGNAL',
    'text',
    'data_source_ready',
    'trading-storage/main/templates/contracts/ready_signal.md',
    'ready_signal_v1;trading-data;data_source',
    'registry_only',
    'Ready-signal type for consumable data_source outputs.'
  ),
  (
    'rst_MSH002',
    'ready_signal_type',
    'DATA_FEATURE_READY_SIGNAL',
    'text',
    'data_feature_ready',
    'trading-storage/main/templates/contracts/ready_signal.md',
    'ready_signal_v1;trading-data;data_feature',
    'registry_only',
    'Ready-signal type for consumable data_feature outputs.'
  ),
  (
    'rst_MSH003',
    'ready_signal_type',
    'MODEL_EVAL_READY_SIGNAL',
    'text',
    'model_eval_ready',
    'trading-storage/main/templates/contracts/ready_signal.md',
    'ready_signal_v1;trading-model;model_evaluation',
    'registry_only',
    'Ready-signal type for consumable model evaluation outputs.'
  ),
  (
    'rst_MSH004',
    'ready_signal_type',
    'PROMOTION_REVIEW_READY_SIGNAL',
    'text',
    'promotion_review_ready',
    'trading-storage/main/templates/contracts/ready_signal.md',
    'ready_signal_v1;trading-model;model_promotion;promotion_review',
    'registry_only',
    'Ready-signal type for reviewed promotion evidence packages or decision records.'
  )
ON CONFLICT (id) DO UPDATE SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  artifact_sync_policy = EXCLUDED.artifact_sync_policy,
  note = EXCLUDED.note,
  updated_at = NOW();
