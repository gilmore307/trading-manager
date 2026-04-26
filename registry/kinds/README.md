# Registry Kind Boundaries

This directory owns one Markdown boundary file per registry `kind`.

Each file defines:

- what the kind means;
- what belongs in the kind;
- what should be rejected or re-scoped elsewhere.

Do not list concrete active registry rows here. Concrete entries live in SQL migrations under `../sql/schema_migrations/`, and the generated visible snapshot is `../current.csv`.

`../reviews/` is for review notes and assessments, not kind source-of-truth files.
