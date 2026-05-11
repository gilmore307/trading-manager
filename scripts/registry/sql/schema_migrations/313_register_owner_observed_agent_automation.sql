-- Register owner-observed agent automation policy for historical provider, promotion, and storage decisions.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'trm_OWNEROBS001',
    'term',
    'OWNER_OBSERVED_AGENT_PROVIDER_AUTOMATION',
    'text',
    'owner_observed_agent_reviewed_provider_data_acquisition',
    'trading-manager/docs/81_decision.md',
    'live_call_approval_v1;manager_live_call_approval_packet_v1;manager_live_call_approval_proposal_validation_v1;provider_dispatch;historical_backfill',
    'sync_artifact',
    'Historical provider acquisition may be agent-reviewed, proposal-validated, dispatched, and reconciled automatically while the owner observes and can intervene. Scope remains provider_data_acquisition_only; broker execution, model activation, and storage lifecycle mutation remain false.'
  ),
  (
    'scr_LCAPKT005',
    'script',
    'AGENT_REVIEW_LIVE_CALL_APPROVAL_PACKET',
    'command',
    'PYTHONPATH=src python3 scripts/tasks/agent_review_live_call_approval_packet.py --packet ${PACKET_JSON} --write',
    '/root/projects/trading-manager/scripts/tasks/agent_review_live_call_approval_packet.py',
    'manager_live_call_approval_packet_v1;live_call_approval_v1;manager_live_call_approval_proposal_validation_v1;owner_observed_agent_provider_automation',
    'sync_artifact',
    'Fills a bounded live-call packet reviewed_approval.json, writes proposal validation, and writes plan-only dispatch evidence under owner-observed agent automation. It performs zero provider calls; dispatch remains a separately audited command or controller step.'
  ),
  (
    'term_AGENTPROMO001',
    'term',
    'AGENT_MODEL_PROMOTION_DECISION',
    'text',
    'agent_model_promotion_decision_v1',
    'trading-manager/docs/96_model_promotion.md',
    'model_promotion_review_v1;activation_record_v1;production_promotion;owner_observed_agent_decision',
    'sync_artifact',
    'Script-called agent decision artifact required before production model activation. Legacy review_decision_v1 artifacts are advisory/evidence scaffolding unless converted through this agent decision boundary.'
  ),
  (
    'trm_MODELPROMO002',
    'term',
    'MODEL_PROMOTION_SCRIPT_CALLED_AGENT_DECISION_POLICY',
    'text',
    'model_promotion_no_activation_without_agent_decision',
    'trading-manager/docs/96_model_promotion.md',
    'model_promotion_review_v1;agent_model_promotion_decision_v1;activation_record_v1',
    'sync_artifact',
    'Production promotion/activation is decided by a script-called agent under owner observation, not by a routine manual approval gate.'
  ),
  (
    'term_STORLIFE001',
    'term',
    'AGENT_STORAGE_LIFECYCLE_DECISION',
    'text',
    'agent_storage_lifecycle_decision_v1',
    'trading-manager/docs/95_task_system.md',
    'storage_lifecycle_request_v1;storage_lifecycle;archive;delete;compress;restore;owner_observed_agent_decision',
    'sync_artifact',
    'Script-called agent decision artifact required before storage lifecycle mutation. The manager may schedule lifecycle requests; storage remains responsible for protected-set checks and physical mutation receipts.'
  ),
  (
    'trm_BROKEROUT001',
    'term',
    'BROKER_ACCOUNT_MUTATION_OUT_OF_HISTORICAL_MODELING_SCOPE',
    'text',
    'broker_order_fill_account_mutation_execution_library_scope',
    'trading-manager/docs/81_decision.md',
    'historical_backfill;model_training_workflow;execution_library',
    'sync_artifact',
    'Broker/order/fill/account mutation is not part of current historical modeling automation and belongs to execution-library work.'
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
