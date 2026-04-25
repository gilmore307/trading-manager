# Request Contract

## Purpose

This file will define the system-level cross-repository request contract.

A request records intended work from `trading-manager`, a human, or an approved Agent into a component repository.

## Initial Contract Boundary

This file should define:

- request identity and versioning;
- caller and target repository;
- target workflow;
- parameters;
- input references;
- expected outputs;
- priority;
- schedule/deadline expectations;
- idempotency expectations;
- retry/cancellation/supersession expectations;
- manual override fields.

## Open Gap

The exact request schema is not yet defined.
