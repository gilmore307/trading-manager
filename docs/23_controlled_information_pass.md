# Controlled Information Pass

A controlled information pass is a safe way to inspect whether required evidence exists before expanding modeling or runtime scope.

## Purpose

- Collect facts from existing manager/component evidence.
- Avoid provider calls by default.
- Produce a report that identifies ready, blocked, missing, or review-required inputs.
- Prevent accidental promotion of stale or unavailable information.

## Rules

- No broker/account mutation.
- No production activation.
- No provider calls unless explicitly routed through provider-dispatch contracts.
- Point-in-time availability must be recorded for model-facing evidence.
- Missing evidence should become a blocker or request, not an implicit assumption.

## Command

```bash
PYTHONPATH=src python3 scripts/tasks/plan_controlled_information_pass.py --start-month 2016-01 --end-month 2016-01 --write
```
