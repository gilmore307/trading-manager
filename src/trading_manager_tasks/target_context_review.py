"""Script-called agent review for target-to-Layer-2 context mappings.

The mapping artifact lives in ``trading-storage`` because it is shared market
structure. ``trading-manager`` owns the review entrypoint so scripts and the
scheduler can ask an agent to review target/context/proxy rows without directly
mutating Layer 1/2 universes, calling providers, activating models, or touching
broker/account state.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping, TextIO

from .control_plane import TaskSystemError

TARGET_CONTEXT_AGENT_REVIEW_REQUEST_CONTRACT = "target_layer2_context_agent_review_request"
TARGET_CONTEXT_AGENT_REVIEW_DECISION_CONTRACT = "target_layer2_context_agent_review_decision"
DEFAULT_MAPPING_CSV = Path("/root/projects/trading-storage/main/shared/layer_2_target_context_mapping.csv")
DEFAULT_OUTPUT_ROOT = Path("storage/runtime/target_layer2_context_agent_review")
DEFAULT_AGENT_REF = "openclaw_agent_under_owner_observation"
DEFAULT_REVIEW_SCOPE = "target_layer2_context_mapping"
REQUIRED_COLUMNS = (
    "target_symbol",
    "target_asset_class",
    "spot_ref",
    "layer2_context_symbol",
    "layer2_mapping_method_type",
    "listed_proxy_symbol",
    "optionable_proxy_symbol",
    "optionable_proxy_status",
    "proxy_role_type",
    "proxy_use",
    "review_status",
    "interpretation",
)
FORBIDDEN_ACTIONS = (
    "do not add listed_proxy_symbol or optionable_proxy_symbol values to Layer 1/2 ETF universe files",
    "do not dispatch provider calls",
    "do not activate models or switch production pointers",
    "do not submit broker orders or mutate accounts",
    "do not perform storage lifecycle mutation",
    "do not edit repository files from the review runner; return a decision artifact only",
)
REQUIRED_CHECKS = (
    "verify every target has a reviewed Layer 2 context symbol",
    "verify proxy symbols remain target-specific auxiliary evidence references",
    "verify optionable_proxy_status gates option-specific provider tasks",
    "verify non-equity target mappings are business/theme mappings, not Layer 1/2 universe additions",
)


def _now_utc() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


def _stable_id(prefix: str, *parts: object) -> str:
    payload = json.dumps(parts, sort_keys=True, separators=(",", ":"), default=str)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def _read_mapping_rows(mapping_csv: Path, *, target_symbols: Iterable[str] | None = None) -> list[dict[str, str]]:
    if not mapping_csv.exists():
        raise TaskSystemError(f"mapping CSV does not exist: {mapping_csv}")
    with mapping_csv.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        if tuple(reader.fieldnames or ()) != REQUIRED_COLUMNS:
            raise TaskSystemError("target Layer 2 context mapping CSV has unexpected columns")
        rows = [dict(row) for row in reader]
    wanted = {symbol.strip().upper() for symbol in target_symbols or [] if symbol.strip()}
    if wanted:
        rows = [row for row in rows if row["target_symbol"].upper() in wanted]
        found = {row["target_symbol"].upper() for row in rows}
        missing = sorted(wanted - found)
        if missing:
            raise TaskSystemError(f"target symbols not found in mapping CSV: {', '.join(missing)}")
    if not rows:
        raise TaskSystemError("no target Layer 2 context mapping rows selected")
    return rows


def _rows_digest(rows: Iterable[Mapping[str, Any]]) -> str:
    payload = json.dumps(list(rows), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_agent_prompt(request: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "You are reviewing a trading-system target-to-Layer-2 context mapping artifact.",
            "Decide whether the selected rows are approved, deferred, or rejected for use as target-study context/proxy metadata.",
            "Review request:",
            json.dumps({key: value for key, value in request.items() if key != "agent_prompt"}, indent=2, sort_keys=True),
            "Required output: JSON with contract_type=target_layer2_context_agent_review_decision, request_ref, agent_ref, decision_status, decision_reason, reviewed_rows, and completed_at_utc.",
            "Safety: do not call providers, mutate broker/account state, activate models, change storage lifecycle, or edit Layer 1/2 universe files.",
        ]
    )


def validate_target_context_agent_review_request(request: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(request)
    required = (
        "contract_type",
        "schema_version",
        "request_id",
        "agent_ref",
        "review_scope",
        "mapping_ref",
        "mapping_path",
        "target_symbols",
        "mapping_rows",
        "required_checks",
        "forbidden_actions",
        "agent_prompt",
        "created_at_utc",
    )
    for field in required:
        value = normalized.get(field)
        if value in (None, "", []):
            raise TaskSystemError(f"missing required target context review request field: {field}")
    if normalized["contract_type"] != TARGET_CONTEXT_AGENT_REVIEW_REQUEST_CONTRACT:
        raise TaskSystemError(f"contract_type must be {TARGET_CONTEXT_AGENT_REVIEW_REQUEST_CONTRACT}")
    if str(normalized["schema_version"]) != "1":
        raise TaskSystemError("schema_version must be 1")
    if not all(str(row.get("target_symbol") or "").strip() for row in normalized["mapping_rows"]):
        raise TaskSystemError("every selected mapping row must include target_symbol")
    return normalized


def build_target_context_agent_review_request(
    *,
    mapping_csv: Path = DEFAULT_MAPPING_CSV,
    target_symbols: Iterable[str] | None = None,
    review_scope: str = DEFAULT_REVIEW_SCOPE,
    evidence_refs: Iterable[str] | None = None,
    requested_by: str = "openclaw",
    agent_ref: str = DEFAULT_AGENT_REF,
    request_id: str | None = None,
) -> dict[str, Any]:
    rows = _read_mapping_rows(mapping_csv, target_symbols=target_symbols)
    selected_targets = [row["target_symbol"] for row in rows]
    digest = _rows_digest(rows)
    stable_id = request_id or _stable_id("tl2ctxreview", str(mapping_csv), review_scope, selected_targets, digest)
    request = {
        "contract_type": TARGET_CONTEXT_AGENT_REVIEW_REQUEST_CONTRACT,
        "schema_version": "1",
        "request_id": stable_id,
        "agent_ref": agent_ref,
        "requested_by": requested_by,
        "review_scope": review_scope,
        "mapping_ref": "trading-storage/main/shared/layer_2_target_context_mapping.csv",
        "mapping_path": str(mapping_csv),
        "mapping_content_sha256": digest,
        "target_symbols": selected_targets,
        "mapping_rows": rows,
        "evidence_refs": [str(ref) for ref in evidence_refs or []],
        "required_checks": list(REQUIRED_CHECKS),
        "forbidden_actions": list(FORBIDDEN_ACTIONS),
        "expected_outputs": [TARGET_CONTEXT_AGENT_REVIEW_DECISION_CONTRACT],
        "policy_refs": [
            "target_layer2_context_mapping_v1",
            "crypto_target_proxy_not_layer_context",
            "script_called_agent_review",
        ],
        "created_at_utc": _now_utc(),
    }
    request["agent_prompt"] = build_agent_prompt(request)
    return validate_target_context_agent_review_request(request)


def validate_target_context_agent_review_decision(decision: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(decision)
    required = ("contract_type", "schema_version", "decision_id", "request_ref", "agent_ref", "decision_status", "decision_reason", "completed_at_utc")
    for field in required:
        value = normalized.get(field)
        if value in (None, ""):
            raise TaskSystemError(f"missing required target context review decision field: {field}")
    if normalized["contract_type"] != TARGET_CONTEXT_AGENT_REVIEW_DECISION_CONTRACT:
        raise TaskSystemError(f"contract_type must be {TARGET_CONTEXT_AGENT_REVIEW_DECISION_CONTRACT}")
    if str(normalized["schema_version"]) != "1":
        raise TaskSystemError("schema_version must be 1")
    if normalized["decision_status"] not in {"approved", "deferred", "rejected", "queued", "agent_call_failed"}:
        raise TaskSystemError(f"unsupported target context review decision status: {normalized['decision_status']}")
    return normalized


def build_queued_decision(request: Mapping[str, Any], *, reason: str = "agent call not requested") -> dict[str, Any]:
    decision = {
        "contract_type": TARGET_CONTEXT_AGENT_REVIEW_DECISION_CONTRACT,
        "schema_version": "1",
        "decision_id": _stable_id("tl2ctxdecision", request["request_id"], reason),
        "request_ref": request["request_id"],
        "agent_ref": request["agent_ref"],
        "decision_status": "queued",
        "decision_reason": reason,
        "reviewed_rows": [],
        "completed_at_utc": _now_utc(),
    }
    return validate_target_context_agent_review_decision(decision)


def call_agent_runner(
    request: Mapping[str, Any],
    *,
    runner_command: str,
    timeout_seconds: int = 1800,
) -> dict[str, Any]:
    argv = shlex.split(runner_command)
    if not argv:
        raise TaskSystemError("agent runner command is empty")
    started = _now_utc()
    try:
        result = subprocess.run(
            argv,
            input=json.dumps(dict(request), sort_keys=True),
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
        stdout = result.stdout
        stderr = result.stderr
        return_code = result.returncode
        if result.returncode == 0:
            try:
                parsed = json.loads(stdout)
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, dict) and parsed.get("contract_type") == TARGET_CONTEXT_AGENT_REVIEW_DECISION_CONTRACT:
                return validate_target_context_agent_review_decision(parsed)
        decision_status = "deferred" if result.returncode == 0 else "agent_call_failed"
        decision_reason = stdout[-8000:] if result.returncode == 0 else stderr[-8000:] or stdout[-8000:]
    except subprocess.TimeoutExpired as exc:
        stdout = str(exc.stdout or "")
        stderr = f"agent runner timed out after {timeout_seconds} seconds\n{exc.stderr or ''}"
        return_code = None
        decision_status = "agent_call_failed"
        decision_reason = stderr[-8000:]
    decision = {
        "contract_type": TARGET_CONTEXT_AGENT_REVIEW_DECISION_CONTRACT,
        "schema_version": "1",
        "decision_id": _stable_id("tl2ctxdecision", request["request_id"], started, return_code, stdout, stderr),
        "request_ref": request["request_id"],
        "agent_ref": request["agent_ref"],
        "decision_status": decision_status,
        "decision_reason": decision_reason or "agent runner returned no parseable decision artifact",
        "reviewed_rows": [],
        "runner_command": runner_command,
        "return_code": return_code,
        "stdout": stdout[-8000:],
        "stderr": stderr[-8000:],
        "started_at_utc": started,
        "completed_at_utc": _now_utc(),
    }
    return validate_target_context_agent_review_decision(decision)


def request_path(request: Mapping[str, Any], output_root: Path = DEFAULT_OUTPUT_ROOT) -> Path:
    return output_root / str(request["request_id"]) / "target_layer2_context_agent_review_request.json"


def decision_path(request: Mapping[str, Any], output_root: Path = DEFAULT_OUTPUT_ROOT) -> Path:
    return output_root / str(request["request_id"]) / "target_layer2_context_agent_review_decision.json"


def write_json_artifact(payload: Mapping[str, Any], *, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(dict(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp_path.replace(path)


def handle_target_context_agent_review(
    *,
    mapping_csv: Path = DEFAULT_MAPPING_CSV,
    target_symbols: Iterable[str] | None = None,
    review_scope: str = DEFAULT_REVIEW_SCOPE,
    evidence_refs: Iterable[str] | None = None,
    requested_by: str = "openclaw",
    agent_ref: str = DEFAULT_AGENT_REF,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    call_agent: bool = False,
    runner_command: str | None = None,
    timeout_seconds: int = 1800,
    write: bool = False,
) -> dict[str, Any]:
    request = build_target_context_agent_review_request(
        mapping_csv=mapping_csv,
        target_symbols=target_symbols,
        review_scope=review_scope,
        evidence_refs=evidence_refs,
        requested_by=requested_by,
        agent_ref=agent_ref,
    )
    configured_runner = runner_command or os.environ.get("MANAGER_TARGET_CONTEXT_AGENT_RUNNER_COMMAND", "").strip()
    if call_agent and configured_runner:
        decision = call_agent_runner(request, runner_command=configured_runner, timeout_seconds=timeout_seconds)
    else:
        reason = "agent runner not configured" if call_agent else "agent call not requested"
        decision = build_queued_decision(request, reason=reason)
    result = {
        "contract_type": "target_layer2_context_agent_review_result",
        "schema_version": "1",
        "request_id": request["request_id"],
        "decision_id": decision["decision_id"],
        "decision_status": decision["decision_status"],
        "target_symbols": request["target_symbols"],
        "mapping_path": request["mapping_path"],
    }
    if write:
        req_path = request_path(request, output_root)
        dec_path = decision_path(request, output_root)
        write_json_artifact(request, path=req_path)
        write_json_artifact(decision, path=dec_path)
        result["request_path"] = str(req_path)
        result["decision_path"] = str(dec_path)
    else:
        result["request"] = request
        result["decision"] = decision
    return result


def write_result(result: Mapping[str, Any], *, output: TextIO) -> None:
    json.dump(dict(result), output, indent=2, sort_keys=True)
    output.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create or call an agent review for target-to-Layer-2 context mapping rows.")
    parser.add_argument("--mapping-csv", default=str(DEFAULT_MAPPING_CSV))
    parser.add_argument("--target-symbol", action="append", default=[])
    parser.add_argument("--review-scope", default=DEFAULT_REVIEW_SCOPE)
    parser.add_argument("--evidence-ref", action="append", default=[])
    parser.add_argument("--requested-by", default="openclaw")
    parser.add_argument("--agent-ref", default=DEFAULT_AGENT_REF)
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--write", action="store_true", help="Write request/decision artifacts under the output root.")
    parser.add_argument("--call-agent", action="store_true", help="Invoke the configured reviewed agent runner; otherwise queue a decision artifact.")
    parser.add_argument("--agent-runner-command", help="Reviewed local command that accepts request JSON on stdin and returns a decision JSON on stdout.")
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    args = parser.parse_args(argv)
    result = handle_target_context_agent_review(
        mapping_csv=Path(args.mapping_csv),
        target_symbols=args.target_symbol,
        review_scope=args.review_scope,
        evidence_refs=args.evidence_ref,
        requested_by=args.requested_by,
        agent_ref=args.agent_ref,
        output_root=Path(args.output_root),
        call_agent=args.call_agent,
        runner_command=args.agent_runner_command,
        timeout_seconds=args.timeout_seconds,
        write=args.write,
    )
    write_result(result, output=sys.stdout)
    return 0


__all__ = [
    "TARGET_CONTEXT_AGENT_REVIEW_DECISION_CONTRACT",
    "TARGET_CONTEXT_AGENT_REVIEW_REQUEST_CONTRACT",
    "build_target_context_agent_review_request",
    "call_agent_runner",
    "handle_target_context_agent_review",
    "validate_target_context_agent_review_decision",
    "validate_target_context_agent_review_request",
]
