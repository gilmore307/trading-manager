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
- autonomous bounded historical provider acquisition with reconciliation/coverage guards;
- execution-side `trade_risk_cap` validation entrypoint registration.

## Accepted Manager-Owned Shape

`trading-manager` owns control-plane facts, not component runtime implementation.

The accepted lifecycle is:

```text
manager_request
  -> component-owned run
  -> component completion receipt
  -> run_manifest
  -> artifact_ref
  -> ready_signal
  -> task_summary read model
```

The accepted promotion route is:

```text
model evidence package
  -> model_promotion_review manager request
  -> agent_model_promotion_decision
  -> activation_record only after agent approve
```

The accepted live-provider gate is:

```text
dry-run request/payload/handoff evidence
  -> non-dry-run manager_request with provider-dispatch policy refs
  -> autonomous historical provider dispatch
  -> provider receipt reconciliation / coverage validation
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

- historical provider dispatch worker operation under autonomous scheduler/resource controls;
- durable object-store/SQL partitioning beyond current payload-reference helpers;
- execution-owned broker/order/fill/account lifecycle;
- dashboard surfaces over `task_summary`, promotion decisions, and ready signals;
- additional manager SQL tables only when lifecycle/query/audit pressure justifies them;
- component catalog only if registry-backed component fields become insufficient.

The target direction after closeout is not a passive script pile: `trading-manager` should grow into the always-on automation scheduler described in `docs/98_automation_scheduler.md`, with historical training/maintenance progressing continuously whenever approvals, resources, dependencies, and regular-trading-day market-hours protection permit.

## Acceptance Evidence

The closeout is acceptable only while these gates pass:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
python3 scripts/registry/apply_registry_migrations.py --dry-run
python3 -m compileall src scripts
python3 scripts/tasks/dispatch_provider_acquisition.py --help
```

No command in this closeout performs provider calls, component dispatch, broker execution, or production activation.
