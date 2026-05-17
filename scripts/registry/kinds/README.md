# Registry Kinds

This directory has one Markdown file for each allowed `trading_registry.kind` value.

## Role

Kind files define per-kind boundaries:

- what the kind means;
- what belongs in it;
- what must be rejected or re-scoped;
- row-shape rules that are specific to that kind.

They do not list active rows. Concrete rows live in SQL migrations and the generated `../current.csv` snapshot.

## Change Rule

Adding, renaming, or removing a kind requires one coherent change:

1. SQL constraint migration.
2. Matching kind Markdown file.
3. Registry/current export.
4. Tests passing.

Cross-kind tie-breakers live in `../rules/`.
