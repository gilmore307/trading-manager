# Controlled Information Pass

The controlled information pass is the evidence-gathering step before broad scheduler, provider-dispatch, target-queue, dataset-threshold, artifact-discovery, or storage-lifecycle defaults are accepted.

It starts with the first formal historical month, `2016-01`, and answers: what do we still need to measure before the manager is allowed to widen automation?

## Contract

The report contract is `manager_controlled_information_pass_v1`.

It summarizes:

- a lightweight resource snapshot;
- the current dataset-expansion decision;
- optional plan-only provider acquisition preview for Layer 1;
- remaining information needs for provider dispatch, concurrency, L3-L7 target queues, dataset thresholds, artifact discovery, and storage lifecycle;
- explicit safety counters proving no provider calls, model activation, broker execution, or storage lifecycle mutation occurred.

## Safety boundary

The information pass may write manager-side report artifacts and safe preparation payloads.

It must not:

- call market-data providers;
- run model activation;
- route broker/paper/live execution;
- delete, compress, archive, restore, or mutate storage lifecycle state;
- weaken `agent_model_promotion_decision_v1`, `agent_storage_lifecycle_decision_v1`, or broker/order/account mutation gates.

Provider dispatch preview is plan-only inside the information-pass boundary. Actual autonomous historical provider acquisition runs outside the information-pass boundary through the scheduler/provider-stage adapter.

## Command

Plan only:

```bash
PYTHONPATH=src python3 scripts/tasks/plan_controlled_information_pass.py \
  --start-month 2016-01 \
  --end-month 2016-01
```

Write the report and safe Layer 1 preparation payloads without provider calls:

```bash
PYTHONPATH=src python3 scripts/tasks/plan_controlled_information_pass.py \
  --start-month 2016-01 \
  --end-month 2016-01 \
  --write
```

Optionally include a plan-only provider dispatch preview without calling providers:

```bash
PYTHONPATH=src python3 scripts/tasks/plan_controlled_information_pass.py \
  --start-month 2016-01 \
  --end-month 2016-01 \
  --preview-provider-dispatch
```

Default report path when `--write` is used:

```text
storage/runtime/information_pass/controlled_information_pass_2016-01.json
```

## Information packages

The report intentionally keeps six items open until evidence exists:

1. **Provider dispatch expansion** — validate each provider adapter, then measure actual request counts, latency, error classes, retry behavior, and quota pressure.
2. **Concurrency defaults** — measure CPU, memory, disk I/O, PostgreSQL pressure, and provider pressure during a small autonomous batch before setting worker defaults.
3. **L3-L7 target queue rules** — inventory target candidates, ranking signals, sector coverage, data completeness, and one-target-at-a-time chain receipts.
4. **Dataset thresholds** — collect real month/sample/label/eval coverage plus baseline, split-stability, regime, and no-leakage evidence before hardening thresholds.
5. **Artifact discovery** — use real component receipt samples to define stable output refs, hashes, schema refs, retention hints, and ready-signal refs.
6. **Storage lifecycle implementation** — build artifact index/protected-set dry-runs before any destructive executor is considered.

## Acceptance

A controlled information pass is acceptable when:

- it reports `provider_calls=0`;
- it reports `model_activation_performed=false`;
- it reports `broker_execution_performed=false`;
- it reports `storage_lifecycle_mutation_performed=false`;
- its selected dataset-expansion action is explicit;
- each remaining information package names the evidence required to close it.
