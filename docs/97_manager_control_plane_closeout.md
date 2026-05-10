# Manager Control-Plane Closeout

## Status

The current `trading-manager` manager/control-plane design-and-MVP phase is closed.

This closeout covers the manager-owned control-plane surfaces needed before component production phases continue:

- registry-backed shared naming and kind boundaries;
- MVP request/run/artifact/ready SQL contracts;
- global task summary read model;
- monthly historical backfill planning;
- request payload materialization and dry-run handoff validation;
- storage-owned completion receipt payload reference flow;
- unified model-promotion review request route;
- generic review decision and activation-record artifact builders;
- live-call approval gate for bounded provider acquisition;
- execution-side `trade_risk_cap` validation entrypoint registration.

## Accepted Manager-Owned Shape

`trading-manager` owns control-plane facts, not component runtime implementation.

The accepted lifecycle is:

```text
manager_request_v1
  -> component-owned run
  -> component completion receipt
  -> run_manifest_v1
  -> artifact_ref_v1
  -> ready_signal_v1
  -> task_summary read model
```

The accepted promotion route is:

```text
model evidence package
  -> model_promotion_review_v1 manager request
  -> review_decision_v1
  -> activation_record_v1 only after approve
```

The accepted live-provider gate is:

```text
dry-run request/payload/handoff evidence
  -> non-dry-run manager_request_v1 with live-call policy refs
  -> reviewed live_call_approval_v1
  -> validate_live_call_approval.py
  -> component dispatch may be considered outside this closeout
```

## Boundaries Preserved

This closeout does not enable or claim:

- unattended production provider orchestration;
- broker order construction;
- broker order placement;
- fills, positions, or account mutation;
- model production activation without an approving review decision;
- durable object-store backend implementation beyond the current storage-owned payload helper;
- dashboard UI implementation.

Those are component production phases, not manager closeout blockers.

## Not Included In This Closeout

The manager/control-plane closeout did not include an always-on production scheduler. Future scheduler work should begin from concrete lifecycle pressure and preserve these boundaries:

- live provider dispatch worker implementation after a validated `live_call_approval_v1` exists;
- durable object-store/SQL partitioning beyond current payload-reference helpers;
- execution-owned broker/order/fill/account lifecycle;
- dashboard surfaces over `task_summary`, promotion decisions, and ready signals;
- additional manager SQL tables only when lifecycle/query/audit pressure justifies them;
- component catalog only if registry-backed component fields become insufficient.

The target direction after closeout is not a passive script pile: `trading-manager` should grow into the always-on automation scheduler described in `docs/98_automation_scheduler.md`, with historical training/maintenance progressing continuously whenever approvals, resources, dependencies, and market-hours protection permit.

## Acceptance Evidence

The closeout is acceptable only while these gates pass:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
python3 scripts/registry/apply_registry_migrations.py --dry-run
python3 -m compileall src scripts
python3 scripts/tasks/validate_live_call_approval.py --help
```

No command in this closeout performs provider calls, component dispatch, broker execution, or production activation.
