# Templates

Templates are reviewed reusable shapes for requests, payloads, contracts, reports, or storage-facing examples. They are not generated runtime outputs.

`template` is not a registry kind. Register the concrete thing instead: checked-in systemd unit files use `systemd_unit`; request, artifact, manifest, and ready-signal categories use their narrow type kinds; reusable shared files use `shared_artifact`.

## Boundary

- Manager owns template rules and registry vocabulary.
- Component repositories own component-local templates when they define local runtime shape.
- Generated task payloads, receipts, logs, and artifacts belong under runtime/storage paths, not in source templates.

## Rules

- Templates must avoid secrets and provider credentials.
- Template fields should use registered names when they cross repository boundaries.
- A template should state its consumer, producer, and point-in-time assumptions.
- If a template becomes executable automation, add a script/helper contract instead of hiding behavior in Markdown.

## Current Use

Manager task scripts generate request payloads and evidence reports from code. Markdown templates are secondary explanatory aids; code and registry contracts own active machine-readable behavior.
