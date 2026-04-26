"""Registry payload_format validation helpers."""

PAYLOAD_FORMATS = (
    "text",
    "file",
    "json",
    "integer",
    "decimal",
    "boolean",
    "iso_date",
    "iso_time",
    "iso_datetime",
    "iso_duration",
    "timezone",
    "secret_alias",
    "repo_name",
    "field_name",
    "status_value",
    "command",
    "python_symbol",
)


def is_payload_format(value: str) -> bool:
    """Return whether *value* is an accepted registry payload format."""
    return value in PAYLOAD_FORMATS


def assert_payload_format(value: str) -> str:
    """Return *value* when it is valid, otherwise raise ``ValueError``."""
    if not is_payload_format(value):
        expected = ", ".join(PAYLOAD_FORMATS)
        raise ValueError(f"Invalid registry payload_format: {value}. Expected one of: {expected}")
    return value
