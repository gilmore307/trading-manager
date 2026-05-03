# Registry Kind Boundaries

This directory owns one Markdown boundary file per allowed `trading_registry.kind` value.

Each file defines:

- what the kind means;
- what belongs in the kind;
- what should be rejected or re-scoped elsewhere.

Do not list concrete active registry rows here. Concrete entries live in SQL migrations under `../sql/schema_migrations/`, and the generated visible snapshot is `../current.csv`.

A kind may be allowed by the SQL constraint even when `../current.csv` currently has zero active rows for that kind. Remove an unused kind only through a reviewed SQL constraint migration and matching deletion of its Markdown boundary file.

Cross-kind and table-shape rules live in `../rules/`. Kind files remain the source of truth for per-kind boundaries only.
