"""Small dependency-light BigQuery REST API helper.

Credentials are resolved from the trading registry and /root/secrets. This
module intentionally avoids google-cloud-bigquery so lightweight data bundles can
query public datasets with a service-account JSON secret without extra runtime
installation.
"""

from __future__ import annotations

import base64
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Mapping

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from trading_registry import SecretResolver, create_csv_registry_query

GDELT_BIGQUERY_CONFIG_ID = "cfg_GDELTBQ1"
DEFAULT_REGISTRY_CSV = Path("/root/projects/trading-main/scripts/current.csv")
DEFAULT_SECRETS_REGISTRY = Path("/root/secrets/registry.json")
DEFAULT_SCOPE = "https://www.googleapis.com/auth/bigquery.readonly"
BIGQUERY_ENDPOINT = "https://bigquery.googleapis.com/bigquery/v2"
DEFAULT_TIMEOUT_SECONDS = 30


@dataclass(frozen=True)
class BigQueryResult:
    """Normalized BigQuery query result."""

    schema: list[str]
    rows: list[dict[str, Any]]
    job_reference: dict[str, Any] = field(default_factory=dict)
    total_rows: int | None = None
    total_bytes_processed: int | None = None
    cache_hit: bool | None = None
    dry_run: bool = False


class BigQueryError(RuntimeError):
    """Raised when BigQuery auth/query handling fails."""


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _jwt_encode_rs256(claims: Mapping[str, Any], private_key_pem: str) -> str:
    header = {"alg": "RS256", "typ": "JWT"}
    signing_input = f"{_b64url(json.dumps(header, separators=(',', ':')).encode())}.{_b64url(json.dumps(dict(claims), separators=(',', ':')).encode())}".encode()
    key = serialization.load_pem_private_key(private_key_pem.encode(), password=None)
    signature = key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
    return signing_input.decode() + "." + _b64url(signature)


def _load_service_account_json(
    *,
    config_id: str = GDELT_BIGQUERY_CONFIG_ID,
    registry_csv: Path = DEFAULT_REGISTRY_CSV,
    secrets_registry: Path = DEFAULT_SECRETS_REGISTRY,
) -> dict[str, Any]:
    resolver = SecretResolver(create_csv_registry_query(registry_csv), registry_path=str(secrets_registry))
    raw = resolver.load_secret_text_by_config_id(config_id)
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise BigQueryError("BigQuery secret payload was not a JSON object")
    for key in ("type", "project_id", "private_key", "client_email", "token_uri"):
        if not payload.get(key):
            raise BigQueryError(f"BigQuery service-account secret missing {key}")
    if payload.get("type") != "service_account":
        raise BigQueryError("BigQuery credential is not a service_account JSON")
    return payload


def _cell_value(cell: Mapping[str, Any]) -> Any:
    value = cell.get("v")
    if isinstance(value, list):
        return [_cell_value(item) if isinstance(item, Mapping) else item for item in value]
    if isinstance(value, Mapping) and "f" in value:
        return {str(field.get("name") or index): _cell_value(child) for index, (field, child) in enumerate(zip(value.get("schema", {}).get("fields", []), value.get("f", []), strict=False))}
    return value


def _parse_query_result(payload: Mapping[str, Any]) -> BigQueryResult:
    schema_fields = payload.get("schema", {}).get("fields", []) if isinstance(payload.get("schema"), Mapping) else []
    names = [str(field.get("name")) for field in schema_fields if isinstance(field, Mapping)]
    rows: list[dict[str, Any]] = []
    for row in payload.get("rows", []) or []:
        cells = row.get("f", []) if isinstance(row, Mapping) else []
        rows.append({name: _cell_value(cell) for name, cell in zip(names, cells, strict=False) if isinstance(cell, Mapping)})
    total_rows = payload.get("totalRows")
    total_bytes_processed = payload.get("totalBytesProcessed")
    cache_hit = payload.get("cacheHit")
    return BigQueryResult(
        schema=names,
        rows=rows,
        job_reference=dict(payload.get("jobReference") or {}),
        total_rows=int(total_rows) if isinstance(total_rows, str) and total_rows.isdigit() else None,
        total_bytes_processed=int(total_bytes_processed) if isinstance(total_bytes_processed, str) and total_bytes_processed.isdigit() else None,
        cache_hit=bool(cache_hit) if isinstance(cache_hit, bool) else None,
        dry_run=bool(payload.get("dryRun", False)),
    )


class BigQueryClient:
    """Minimal BigQuery query client using service-account JWT auth."""

    def __init__(
        self,
        service_account: Mapping[str, Any] | None = None,
        *,
        config_id: str = GDELT_BIGQUERY_CONFIG_ID,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self.service_account = dict(service_account or _load_service_account_json(config_id=config_id))
        self.timeout_seconds = timeout_seconds
        self._access_token: str | None = None
        self._token_expiry = 0

    @property
    def project_id(self) -> str:
        return str(self.service_account["project_id"])

    def _access_token_value(self) -> str:
        now = int(time.time())
        if self._access_token and now < self._token_expiry - 60:
            return self._access_token
        claims = {
            "iss": self.service_account["client_email"],
            "scope": DEFAULT_SCOPE,
            "aud": self.service_account["token_uri"],
            "iat": now,
            "exp": now + 3600,
        }
        assertion = _jwt_encode_rs256(claims, str(self.service_account["private_key"]))
        body = urllib.parse.urlencode({"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": assertion}).encode()
        request = urllib.request.Request(str(self.service_account["token_uri"]), data=body, headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            raise BigQueryError(f"BigQuery token request failed: {exc}") from exc
        token = payload.get("access_token") if isinstance(payload, Mapping) else None
        if not token:
            raise BigQueryError("BigQuery token response missing access_token")
        self._access_token = str(token)
        self._token_expiry = now + int(payload.get("expires_in", 3600))
        return self._access_token

    def query(
        self,
        sql: str,
        *,
        project_id: str | None = None,
        max_results: int | None = None,
        use_legacy_sql: bool = False,
        dry_run: bool = False,
        maximum_bytes_billed: int | None = None,
        max_bytes_billed: int | None = None,
    ) -> BigQueryResult:
        if not sql.strip():
            raise ValueError("sql must be non-empty")
        payload: dict[str, Any] = {"query": sql, "useLegacySql": use_legacy_sql, "dryRun": dry_run}
        bytes_cap = maximum_bytes_billed if maximum_bytes_billed is not None else max_bytes_billed
        if bytes_cap is not None:
            if bytes_cap < 1:
                raise ValueError("maximum_bytes_billed must be positive")
            payload["maximumBytesBilled"] = str(bytes_cap)
        if max_results is not None:
            payload["maxResults"] = max_results
        url = f"{BIGQUERY_ENDPOINT}/projects/{project_id or self.project_id}/queries"
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": "Bearer " + self._access_token_value(), "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                result_payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise BigQueryError(f"BigQuery query HTTP {exc.code}: {detail}") from exc
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            raise BigQueryError(f"BigQuery query failed: {exc}") from exc
        if not isinstance(result_payload, Mapping):
            raise BigQueryError("BigQuery query response was not a JSON object")
        if result_payload.get("errors"):
            raise BigQueryError("BigQuery query returned errors: " + json.dumps(result_payload.get("errors"))[:500])
        result = _parse_query_result(result_payload)
        return replace(result, dry_run=True) if dry_run else result


def bigquery_query(sql: str, **kwargs: Any) -> BigQueryResult:
    """Run a BigQuery Standard SQL query with the default secret-backed client."""
    return BigQueryClient().query(sql, **kwargs)
