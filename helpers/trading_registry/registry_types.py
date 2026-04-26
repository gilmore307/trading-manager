"""Registry kind validation helpers."""

REGISTRY_KINDS = (
    "field",
    "output",
    "repo",
    "config",
    "term",
    "script",
    "payload_format",
    "artifact_type",
    "manifest_type",
    "ready_signal_type",
    "request_type",
    "task_lifecycle_state",
    "review_readiness",
    "acceptance_outcome",
    "test_status",
    "maintenance_status",
    "docs_status",
)


def is_registry_kind(value: str) -> bool:
    """Return whether *value* is an accepted registry kind."""
    return value in REGISTRY_KINDS


def assert_registry_kind(value: str) -> str:
    """Return *value* when it is valid, otherwise raise ``ValueError``."""
    if not is_registry_kind(value):
        expected = ", ".join(REGISTRY_KINDS)
        raise ValueError(f"Invalid registry kind: {value}. Expected one of: {expected}")
    return value
