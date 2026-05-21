-- Register current fold-settlement metric assembly and execution monitor service surfaces.

UPDATE trading_registry
SET
  path = 'trading-evaluation/docs/30_fold_settlement.md;trading-evaluation/src/trading_evaluation/settlement.py',
  applies_to = 'trading-evaluation;fold_settlement;model_evaluation;promotion_eligibility;auroc;pca;pcoa;agent_review_required',
  note = 'Evaluation-owned settlement run over replay decision rows from one completed fold and one accepted benchmark contract. It emits deterministic scalar metrics plus AUROC, PCA, and PCoA-style structure diagnostics; promotion-evaluation-review agent review remains required before promotion readiness.'
WHERE key = 'FOLD_SETTLEMENT_RUN';

UPDATE trading_registry
SET
  path = 'trading-evaluation/docs/30_fold_settlement.md;trading-evaluation/src/trading_evaluation/settlement.py',
  applies_to = 'trading-evaluation;fold_settlement;metric;model_evaluation;auroc;pca;pcoa;brier_score;promotion_evidence',
  note = 'Metric row emitted by fold settlement for return, drawdown, hit-rate, payoff, calibration/Brier, AUROC, PCA top-two variance, and PCoA-style pairwise-distance evidence. Metrics are advisory inputs to the agent review and do not activate models.'
WHERE key = 'FOLD_SETTLEMENT_METRIC';

UPDATE trading_registry
SET payload = 'execution_realtime_monitor_loop_receipt'
WHERE key = 'EXECUTION_REALTIME_MONITOR_LOOP_RECEIPT';

UPDATE trading_registry
SET payload = 'execution_realtime_monitor_cycle_summary'
WHERE key = 'EXECUTION_REALTIME_MONITOR_CYCLE_SUMMARY';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_EVALSETTLE001',
    'script',
    'TRADING_EVALUATION_BUILD_FOLD_SETTLEMENT_RUN',
    'command',
    'PYTHONPATH=src python3 scripts/evaluation/build_fold_settlement_run.py --decision-rows $DECISION_ROWS --fold-id $FOLD_ID --candidate-model-ref $CANDIDATE_MODEL_REF --benchmark-contract-ref $BENCHMARK_CONTRACT_REF --replay-result-ref $REPLAY_RESULT_REF --output-path $OUTPUT_PATH',
    '/root/projects/trading-evaluation/scripts/evaluation/build_fold_settlement_run.py',
    'trading-evaluation;fold_settlement;promotion_eligibility;auroc;pca;pcoa;agent_review_required',
    'sync_artifact',
    'Build a fold_settlement_run artifact from replay decision rows. The script computes AUROC, PCA, and PCoA-style diagnostics when inputs support them, requires later promotion-evaluation-review agent judgment, and performs no provider, model activation, broker, account, or SQL mutation.'
  ),
  (
    'cfg_EXEC_RT_MONITOR003',
    'config',
    'EXECUTION_REALTIME_MONITOR_LOOP_SYSTEMD_SERVICE',
    'text',
    'plan_only_by_default;provider_observe_requires_TRADING_EXECUTION_REALTIME_MONITOR_EXECUTE_LIVE_OBSERVE_1;no_model_activation;no_order_construction;no_account_mutation',
    'trading-execution/deploy/systemd/trading-execution-realtime-monitor-loop.service',
    'trading-execution;systemd;realtime_monitoring;runtime_loop;read_only_live_observe_gate',
    'sync_artifact',
    'Execution-owned systemd service template for the realtime monitor loop. The checked-in service is plan-only by default; live provider observation requires an explicit host override and still does not activate models, construct orders, call broker mutation, or mutate accounts.'
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
