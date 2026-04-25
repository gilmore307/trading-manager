# Artifact Contract

## Purpose

This file will define the system-level artifact contract used for cross-repository handoff.

Artifacts are durable outputs produced by component repositories and consumed by downstream repositories or `trading-manager`.

## Initial Contract Boundary

This file should define:

- artifact identity and reference format;
- artifact classes;
- producer and consumer expectations;
- path and partition expectations at the system level;
- mutability and overwrite rules;
- relationship to manifests;
- relationship to ready signals;
- retention, archive, and rehydrate expectations at the system level.

## Open Gap

The exact artifact schema and reference format are not yet defined.
