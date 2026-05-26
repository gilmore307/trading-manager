# Registry Kinds

This directory has one Markdown file for each allowed `trading_registry.kind` value.

## Role

Kind files define per-kind boundaries:

- what the kind means;
- what belongs in it;
- what must be rejected or re-scoped;
- row-shape rules that are specific to that kind.

They do not list active rows. Concrete rows live in the reviewed `../current.csv` inventory.

## Change Rule

Adding, renaming, or removing a kind requires one coherent change:

1. Current SQL constraint update in `../sql/trading_registry.sql`.
2. Matching kind Markdown file.
3. Registry/current row update when needed.
4. Tests passing.

Cross-kind tie-breakers live in `../rules/`.
