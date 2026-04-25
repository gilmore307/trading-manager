# Path

## Kind Boundary

Canonical filesystem path values. Use only for stable reviewed paths that should be referenced consistently.

## Range

Register stable reviewed paths only. Do not register disposable generated paths, secrets paths that expose sensitive structure, or artifact instance paths.

## Reject Or Re-scope

Reject or re-scope entries that are actually:

- generated artifact paths;
- secret file paths unless explicitly approved as aliases elsewhere;
- repo names without paths;
