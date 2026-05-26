# SQL Table

## Meaning

`sql_table` names reviewed canonical SQL table surfaces.

## Register Here

Register durable SQL table names that are shared across repositories, contracts, runtime surfaces, dashboards, evaluations, or future gated execution boundaries.

## Do Not Register Here

- glossary concepts;
- generated table instances or temporary scratch tables;
- field/column names;
- SQL schemas without a concrete table;
- migration history;
- ordinary source files that create or query tables;

## Row Rules

- `payload` must hold the canonical SQL table name.
- Use schema-qualified lowercase snake_case names when the table has an accepted repository-owned schema.
- Unqualified payloads are allowed only for documented generic logical table names whose schema is intentionally owned by the consuming repository.
- `applies_to` must include `sql_table`.
- Registration reserves or names a table; it does not authorize broker, account, order, position, provider, or storage lifecycle mutation.
- Never register secrets, generated blobs, local scratch files, or unreviewed experiment labels.
