"""Validate manager request payload handoff to component repositories.

This module checks that a materialized request payload is concrete enough for a
component-facing dry-run handoff without dispatching work or calling providers.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Literal, Mapping, Sequence, TextIO

from .control_plane import (
    TaskSystemError,
    fetch_input_bindings,
    fetch_manager_requests,
    load_json_or_jsonl,
    validate_manager_request,
)
from .request_payloads import DEFAULT_STORAGE_ROOT, PARAMETER_SCHEMA_REF, storage_uri_to_local_path

DEFAULT_TRADING_DATA_SRC = Path("/root/projects/trading-data/src")
DEFAULT_RUN_ID = "manager_handoff_validation"


@dataclass(frozen=True)
class RequestHandoffValidation:
    """Result of validating one request payload handoff boundary."""

    request_id: str
    target_component_id: str
    parameter_ref: str
    local_path: Path
    content_hash: str
    byte_size: int
    pipeline_module: str
    context_run_dir: str | None
    status: str = "validated"
    provider_calls: int = 0
    dispatch_performed: bool = False

    def summary_row(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "target_component_id": self.target_component_id,
            "parameter_ref": self.parameter_ref,
            "local_path": str(self.local_path),
            "content_hash": self.content_hash,
            "byte_size": self.byte_size,
            "pipeline_module": self.pipeline_module,
            "context_run_dir": self.context_run_dir,
            "status": self.status,
            "provider_calls": self.provider_calls,
            "dispatch_performed": self.dispatch_performed,
        }


def _payload_bytes(path: Path) -> bytes:
    if not path.exists():
        raise TaskSystemError(f"materialized payload is missing: {path}")
    if not path.is_file():
        raise TaskSystemError(f"materialized payload is not a file: {path}")
    return path.read_bytes()


def _payload_hash(content: bytes) -> str:
    return "sha256:" + hashlib.sha256(content).hexdigest()


def _load_payload(path: Path) -> tuple[dict[str, Any], str, int]:
    content = _payload_bytes(path)
    try:
        payload = json.loads(content.decode("utf-8"))
    except json.JSONDecodeError as exc:  # pragma: no cover - exception message shape is stdlib owned.
        raise TaskSystemError(f"payload is not valid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise TaskSystemError("materialized payload must be a JSON object")
    return payload, _payload_hash(content), len(content)


def _pipeline_module_for_component(component_id: str) -> str:
    if not component_id.startswith(tuple(str(i).zfill(2) + "_feed_" for i in range(1, 100))):
        raise TaskSystemError(f"handoff validation currently supports data_feed components only: {component_id}")
    return f"data_feed.{component_id}.pipeline"


def _import_pipeline(module_name: str, *, component_src_root: Path):
    root = str(component_src_root)
    inserted = False
    module_parts = module_name.split(".")
    module_prefixes = [".".join(module_parts[:idx]) for idx in range(1, len(module_parts) + 1)]
    previous_modules = {name: sys.modules.pop(name) for name in module_prefixes if name in sys.modules}
    if root not in sys.path:
        sys.path.insert(0, root)
        inserted = True
    try:
        importlib.invalidate_caches()
        return importlib.import_module(module_name)
    finally:
        for name in module_prefixes:
            sys.modules.pop(name, None)
        sys.modules.update(previous_modules)
        if inserted:
            try:
                sys.path.remove(root)
            except ValueError:  # pragma: no cover - defensive cleanup.
                pass


def _require_dry_run_safety(payload: Mapping[str, Any], *, allow_live: bool) -> None:
    if allow_live:
        return
    if payload.get("dry_run") is not True:
        raise TaskSystemError("handoff validation refuses non-dry-run payloads")
    controls = payload.get("manager_controls") or {}
    if controls.get("allow_live_provider_calls") not in (False, None):
        raise TaskSystemError("manager_controls.allow_live_provider_calls must be false for dry-run handoff validation")


def _validate_payload_alignment(request: Mapping[str, Any], payload: Mapping[str, Any], *, allow_live: bool) -> None:
    if payload.get("contract_type") != PARAMETER_SCHEMA_REF:
        raise TaskSystemError(f"payload.contract_type must be {PARAMETER_SCHEMA_REF}")
    if payload.get("request_id") != request["request_id"]:
        raise TaskSystemError("payload.request_id does not match manager request")
    if payload.get("task_id") != request["request_id"]:
        raise TaskSystemError("payload.task_id does not match manager request")
    if payload.get("feed") != request["target_component_id"]:
        raise TaskSystemError("payload.feed does not match request target_component_id")
    if payload.get("target_repo_id") != request["target_repo_id"]:
        raise TaskSystemError("payload.target_repo_id does not match manager request")
    controls = payload.get("manager_controls") or {}
    if controls.get("parameter_ref") != request.get("parameter_ref"):
        raise TaskSystemError("payload manager_controls.parameter_ref does not match request parameter_ref")
    params = payload.get("params") or {}
    if params.get("manager_request_id") != request["request_id"]:
        raise TaskSystemError("payload.params.manager_request_id does not match manager request")
    output_root = Path(str(payload.get("output_root") or ""))
    if not str(output_root) or output_root.is_absolute() or ".." in output_root.parts:
        raise TaskSystemError("payload.output_root must be a safe relative path")
    _require_dry_run_safety(payload, allow_live=allow_live)


def _binding_by_request(bindings: Iterable[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    for binding in bindings:
        request_id = str(binding.get("request_id") or "")
        if request_id in result:
            raise TaskSystemError(f"multiple parameter payload input bindings found for {request_id}")
        result[request_id] = binding
    return result


def _validate_input_binding(request: Mapping[str, Any], binding: Mapping[str, Any] | None, *, content_hash: str) -> None:
    if binding is None:
        raise TaskSystemError(f"missing parameter_payload input_binding for {request['request_id']}")
    if binding.get("input_ref") != request.get("parameter_ref"):
        raise TaskSystemError("input_binding.input_ref does not match request parameter_ref")
    if binding.get("schema_ref") != PARAMETER_SCHEMA_REF:
        raise TaskSystemError(f"input_binding.schema_ref must be {PARAMETER_SCHEMA_REF}")
    if binding.get("version_ref") != content_hash:
        raise TaskSystemError("input_binding.version_ref does not match materialized payload hash")


def validate_request_handoff(
    request_row: Mapping[str, Any],
    *,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    component_src_root: Path = DEFAULT_TRADING_DATA_SRC,
    run_id: str = DEFAULT_RUN_ID,
    input_binding: Mapping[str, Any] | None = None,
    require_input_binding: bool = False,
    allow_live: bool = False,
) -> RequestHandoffValidation:
    """Validate one materialized payload against a component build_context path.

    The validation imports the component pipeline and calls only `build_context`.
    It never calls component `run`, `fetch`, or provider/client code.
    """

    request = validate_manager_request(request_row)
    if request["target_repo_id"] != "trading-data":
        raise TaskSystemError("handoff validation currently supports target_repo_id=trading-data")
    parameter_ref = str(request.get("parameter_ref") or "")
    local_path = storage_uri_to_local_path(parameter_ref, storage_root=storage_root)
    payload, content_hash, byte_size = _load_payload(local_path)
    _validate_payload_alignment(request, payload, allow_live=allow_live)
    if require_input_binding:
        _validate_input_binding(request, input_binding, content_hash=content_hash)
    module_name = _pipeline_module_for_component(str(request["target_component_id"]))
    pipeline = _import_pipeline(module_name, component_src_root=component_src_root)
    build_context = getattr(pipeline, "build_context", None)
    if build_context is None:
        raise TaskSystemError(f"{module_name} does not expose build_context")
    context = build_context(payload, run_id)
    context_run_dir = getattr(context, "run_dir", None)
    return RequestHandoffValidation(
        request_id=str(request["request_id"]),
        target_component_id=str(request["target_component_id"]),
        parameter_ref=parameter_ref,
        local_path=local_path,
        content_hash=content_hash,
        byte_size=byte_size,
        pipeline_module=module_name,
        context_run_dir=None if context_run_dir is None else str(context_run_dir),
    )


def validate_request_handoffs(
    request_rows: Iterable[Mapping[str, Any]],
    *,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    component_src_root: Path = DEFAULT_TRADING_DATA_SRC,
    run_id: str = DEFAULT_RUN_ID,
    input_bindings: Iterable[Mapping[str, Any]] = (),
    require_input_binding: bool = False,
    allow_live: bool = False,
) -> list[RequestHandoffValidation]:
    binding_map = _binding_by_request(input_bindings)
    return [
        validate_request_handoff(
            row,
            storage_root=storage_root,
            component_src_root=component_src_root,
            run_id=run_id,
            input_binding=binding_map.get(str(row.get("request_id") or "")),
            require_input_binding=require_input_binding,
            allow_live=allow_live,
        )
        for row in request_rows
    ]


def write_handoff_output(
    validations: Sequence[RequestHandoffValidation],
    *,
    output: TextIO,
    output_format: Literal["jsonl", "json"] = "jsonl",
) -> None:
    rows = [item.summary_row() for item in validations]
    if output_format == "json":
        json.dump(rows, output, indent=2, sort_keys=True)
        output.write("\n")
        return
    for row in rows:
        output.write(json.dumps(row, sort_keys=True) + "\n")


def _load_rows_from_args(args: argparse.Namespace) -> list[dict[str, Any]]:
    if args.from_db:
        if args.path is not None:
            raise TaskSystemError("pass either path or --from-db, not both")
        return fetch_manager_requests(
            database_url=args.database_url,
            request_kind=args.request_kind,
            status=args.status,
            request_ids=args.request_id,
            limit=args.limit,
            include_rehearsals=args.include_rehearsals,
        )
    if args.path is None:
        raise TaskSystemError("path is required unless --from-db is set")
    return [validate_manager_request(row) for row in load_json_or_jsonl(args.path)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate materialized request payload handoff without dispatch/provider calls.")
    parser.add_argument("path", nargs="?", type=Path, help="JSON, JSON array, or JSONL manager_request rows.")
    parser.add_argument("--from-db", action="store_true", help="Fetch request rows from trading_manager.manager_request.")
    parser.add_argument("--database-url")
    parser.add_argument("--request-kind", default="data_backfill_month")
    parser.add_argument("--status", default="requested")
    parser.add_argument("--request-id", action="append", help="Limit SQL fetch to one request id; repeatable.")
    parser.add_argument("--include-rehearsals", action="store_true", help="Include mgrreq_rehearsal_* rows when fetching from SQL.")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--storage-root", type=Path, default=DEFAULT_STORAGE_ROOT)
    parser.add_argument("--component-src-root", type=Path, default=DEFAULT_TRADING_DATA_SRC)
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    parser.add_argument("--skip-input-binding-check", action="store_true")
    parser.add_argument("--allow-live", action="store_true", help="Allow non-dry-run payloads. Not for current backfill validation.")
    parser.add_argument("--format", choices=("jsonl", "json"), default="jsonl")
    args = parser.parse_args(argv)

    rows = _load_rows_from_args(args)
    bindings: list[dict[str, Any]] = []
    require_input_binding = args.from_db and not args.skip_input_binding_check
    if require_input_binding:
        bindings = fetch_input_bindings(
            database_url=args.database_url,
            request_ids=[str(row["request_id"]) for row in rows],
            input_role="parameter_payload",
            schema_ref=PARAMETER_SCHEMA_REF,
        )
    validations = validate_request_handoffs(
        rows,
        storage_root=args.storage_root,
        component_src_root=args.component_src_root,
        run_id=args.run_id,
        input_bindings=bindings,
        require_input_binding=require_input_binding,
        allow_live=args.allow_live,
    )
    write_handoff_output(validations, output=sys.stdout, output_format=args.format)
    return 0


__all__ = [
    "DEFAULT_RUN_ID",
    "DEFAULT_TRADING_DATA_SRC",
    "RequestHandoffValidation",
    "validate_request_handoff",
    "validate_request_handoffs",
    "write_handoff_output",
]


if __name__ == "__main__":  # pragma: no cover - exercised through script wrapper.
    raise SystemExit(main())
