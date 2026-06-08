"""Close completed server-error agent repairs with bounded internal actions."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from .agent_error_handler import DEFAULT_OUTPUT_ROOT, _stable_id

AGENT_REPAIR_CLOSURE_RECEIPT_CONTRACT = "agent_repair_closure_receipt"
DEFAULT_MANAGER_REPO_ROOT = Path("/root/projects/trading-manager")
DEFAULT_REPO_ROOTS = (
    Path("/root/projects/trading-manager"),
    Path("/root/projects/trading-data"),
    Path("/root/projects/trading-model"),
    Path("/root/projects/trading-evaluation"),
    Path("/root/projects/trading-execution"),
    Path("/root/projects/trading-storage"),
)
DEFAULT_DASHBOARD_REFRESH_SERVICE = "trading-storage-dashboard-read-model-refresh.service"
DEFAULT_HISTORICAL_SCHEDULER_SERVICE = "trading-manager-historical-scheduler.service"
FORBIDDEN_AUTOMATION_TERMS = (
    "broker",
    "account",
    "order",
    "fill",
    "position",
    "buying-power",
    "buying_power",
    "funds",
)


CommandRunner = Callable[..., subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class ClosureCandidate:
    request_dir: Path
    request_path: Path
    diagnosis_path: Path
    receipt_path: Path


def _now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_json(path: Path) -> dict[str, Any]:
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _parse_stdout_payload(diagnosis: Mapping[str, Any]) -> dict[str, Any]:
    stdout = diagnosis.get("stdout")
    if isinstance(stdout, Mapping):
        return dict(stdout)
    if not stdout:
        return {}
    try:
        parsed = json.loads(str(stdout))
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _payload_text(*values: object) -> str:
    return " ".join(str(value or "").lower() for value in values)


def _diagnosis_repaired(payload: Mapping[str, Any]) -> bool:
    diagnosis_status = str(payload.get("diagnosis_status") or "").lower()
    repair = payload.get("repair")
    repair_status = str(repair.get("repair_status") if isinstance(repair, Mapping) else "")
    return diagnosis_status.startswith(("fixed", "repaired")) or repair_status in {"repaired", "no_action_needed"}


def _automatic_retry_forbidden(payload: Mapping[str, Any]) -> bool:
    text = _payload_text(payload.get("retry_recommendation"), payload.get("blockers"))
    return any(marker in text for marker in ("manual_review", "manual review", "do_not_retry", "do not retry", "blocked"))


def _forbidden_runtime_scope(request: Mapping[str, Any], payload: Mapping[str, Any]) -> bool:
    text = _payload_text(
        request.get("source_component"),
        request.get("error_scope"),
        request.get("error_kind"),
        request.get("summary"),
        payload.get("retry_recommendation"),
        payload.get("root_cause"),
    )
    return any(term in text for term in FORBIDDEN_AUTOMATION_TERMS)


def _known_repo_for_path(raw_path: object, repo_roots: Iterable[Path]) -> Path | None:
    if not raw_path:
        return None
    try:
        path = Path(str(raw_path)).expanduser()
    except (TypeError, ValueError):
        return None
    if not path.is_absolute():
        return None
    for repo_root in repo_roots:
        try:
            path.relative_to(repo_root)
        except ValueError:
            continue
        return repo_root
    return None


def _repos_from_payload(payload: Mapping[str, Any], repo_roots: Iterable[Path]) -> tuple[Path, ...]:
    repos: set[Path] = set()
    for raw_path in payload.get("files_changed") or []:
        repo = _known_repo_for_path(raw_path, repo_roots)
        if repo is not None:
            repos.add(repo)
    return tuple(sorted(repos))


def _run(
    runner: CommandRunner,
    argv: list[str],
    *,
    cwd: Path | None = None,
    timeout: float = 60.0,
) -> subprocess.CompletedProcess[str]:
    return runner(argv, cwd=str(cwd) if cwd else None, text=True, capture_output=True, timeout=timeout, check=False)


def _git_current_branch(repo_root: Path, *, runner: CommandRunner) -> str | None:
    result = _run(runner, ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_root)
    if result.returncode != 0:
        return None
    branch = result.stdout.strip()
    return branch if branch and branch != "HEAD" else None


def _git_has_uncommitted_changes(repo_root: Path, *, runner: CommandRunner) -> bool:
    result = _run(runner, ["git", "status", "--porcelain"], cwd=repo_root)
    return bool(result.stdout.strip()) if result.returncode == 0 else True


def _git_ahead_of_origin(repo_root: Path, branch: str, *, runner: CommandRunner) -> bool:
    result = _run(runner, ["git", "rev-list", "--count", f"origin/{branch}..HEAD"], cwd=repo_root)
    if result.returncode != 0:
        return False
    try:
        return int(result.stdout.strip() or "0") > 0
    except ValueError:
        return False


def _push_repaired_repos(
    repos: Iterable[Path],
    *,
    runner: CommandRunner,
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for repo_root in repos:
        branch = _git_current_branch(repo_root, runner=runner)
        if branch is None:
            actions.append({"action": "git_push", "repo": str(repo_root), "status": "skipped", "reason": "no current branch"})
            continue
        if _git_has_uncommitted_changes(repo_root, runner=runner):
            actions.append({"action": "git_push", "repo": str(repo_root), "status": "blocked", "reason": "repo has uncommitted changes"})
            continue
        if not _git_ahead_of_origin(repo_root, branch, runner=runner):
            actions.append({"action": "git_push", "repo": str(repo_root), "status": "not_needed", "branch": branch})
            continue
        result = _run(runner, ["git", "push", "origin", branch], cwd=repo_root, timeout=120.0)
        actions.append(
            {
                "action": "git_push",
                "repo": str(repo_root),
                "branch": branch,
                "status": "completed" if result.returncode == 0 else "failed",
                "return_code": result.returncode,
                "stdout": result.stdout[-2000:],
                "stderr": result.stderr[-2000:],
            }
        )
    return actions


def _needs_scheduler_restart(request: Mapping[str, Any], payload: Mapping[str, Any], repos: Iterable[Path]) -> bool:
    text = _payload_text(payload.get("diagnosis_status"), payload.get("retry_recommendation"), payload.get("root_cause"))
    if any(marker in text for marker in ("restart_pending", "restart pending", "service restart", "restart service", "reload service")):
        return True
    if DEFAULT_MANAGER_REPO_ROOT in set(repos) and "scheduler" in _payload_text(
        request.get("source_component"), request.get("error_scope"), request.get("error_kind")
    ):
        return True
    return False


def _systemctl_action(
    action: str,
    service: str,
    *,
    runner: CommandRunner,
    timeout: float = 60.0,
) -> dict[str, Any]:
    result = _run(runner, ["systemctl", action, service], timeout=timeout)
    return {
        "action": f"systemctl_{action}",
        "service": service,
        "status": "completed" if result.returncode == 0 else "failed",
        "return_code": result.returncode,
        "stdout": result.stdout[-2000:],
        "stderr": result.stderr[-2000:],
    }


def discover_closure_candidates(output_root: Path = DEFAULT_OUTPUT_ROOT) -> tuple[ClosureCandidate, ...]:
    if not output_root.exists():
        return ()
    candidates: list[ClosureCandidate] = []
    for request_dir in sorted(output_root.iterdir()):
        if not request_dir.is_dir():
            continue
        request_path = request_dir / "server_error_agent_request.json"
        diagnosis_path = request_dir / "agent_error_diagnosis.json"
        receipt_path = request_dir / "agent_repair_closure_receipt.json"
        if request_path.exists() and diagnosis_path.exists() and not receipt_path.exists():
            candidates.append(
                ClosureCandidate(
                    request_dir=request_dir,
                    request_path=request_path,
                    diagnosis_path=diagnosis_path,
                    receipt_path=receipt_path,
                )
            )
    return tuple(candidates)


def close_agent_repair(
    candidate: ClosureCandidate,
    *,
    runner: CommandRunner = subprocess.run,
    repo_roots: Iterable[Path] = DEFAULT_REPO_ROOTS,
    restart_scheduler_service: str = DEFAULT_HISTORICAL_SCHEDULER_SERVICE,
    dashboard_refresh_service: str = DEFAULT_DASHBOARD_REFRESH_SERVICE,
    execute_actions: bool = True,
    write_receipt: bool = True,
) -> dict[str, Any]:
    request = _load_json(candidate.request_path)
    diagnosis = _load_json(candidate.diagnosis_path)
    payload = _parse_stdout_payload(diagnosis)
    actions: list[dict[str, Any]] = []
    blockers: list[str] = []
    closure_status = "not_closed"

    if diagnosis.get("status") != "completed":
        closure_status = "pending"
        blockers.append("agent diagnosis is not completed")
    elif not payload:
        blockers.append("completed diagnosis did not contain parseable JSON stdout")
    elif not _diagnosis_repaired(payload):
        blockers.append("agent diagnosis did not report a repaired/fixed status")
    elif _automatic_retry_forbidden(payload):
        blockers.append("agent retry recommendation forbids automatic retry or requires manual review")
    elif _forbidden_runtime_scope(request, payload):
        blockers.append("request scope touches broker/account/order/fill/position/buying-power/funds boundary")
    else:
        repos = _repos_from_payload(payload, repo_roots)
        if execute_actions:
            actions.extend(_push_repaired_repos(repos, runner=runner))
        else:
            actions.extend({"action": "git_push", "repo": str(repo), "status": "planned"} for repo in repos)
        if _needs_scheduler_restart(request, payload, repos):
            actions.append(
                _systemctl_action("restart", restart_scheduler_service, runner=runner)
                if execute_actions
                else {"action": "systemctl_restart", "service": restart_scheduler_service, "status": "planned"}
            )
        if execute_actions:
            actions.append(_systemctl_action("start", dashboard_refresh_service, runner=runner, timeout=15.0))
        else:
            actions.append({"action": "systemctl_start", "service": dashboard_refresh_service, "status": "planned"})
        closure_status = "closed" if not any(action.get("status") in {"failed", "blocked"} for action in actions) else "blocked"

    if blockers and closure_status != "pending":
        closure_status = "blocked"
    now = _now_utc()
    receipt = {
        "contract_type": AGENT_REPAIR_CLOSURE_RECEIPT_CONTRACT,
        "schema_version": "1",
        "closure_id": _stable_id("errclose", candidate.request_path, candidate.diagnosis_path, now),
        "request_ref": request.get("request_id"),
        "error_ref": request.get("error_ref"),
        "diagnosis_ref": diagnosis.get("diagnosis_id"),
        "closure_status": closure_status,
        "actions": actions,
        "blockers": blockers,
        "safety": {
            "broker_account_order_position_mutation_performed": False,
            "provider_calls_performed": False,
            "destructive_storage_mutation_performed": False,
        },
        "dry_run": not execute_actions,
        "closed_at_utc": now,
    }
    if write_receipt and closure_status != "pending":
        candidate.receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def close_pending_agent_repairs(
    *,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    runner: CommandRunner = subprocess.run,
    repo_roots: Iterable[Path] = DEFAULT_REPO_ROOTS,
    execute_actions: bool = True,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    receipts: list[dict[str, Any]] = []
    for candidate in discover_closure_candidates(output_root)[:limit]:
        receipts.append(
            close_agent_repair(
                candidate,
                runner=runner,
                repo_roots=repo_roots,
                execute_actions=execute_actions,
                write_receipt=execute_actions,
            )
        )
    return receipts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Close completed agent repairs with bounded internal follow-up actions.")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--plan-only", action="store_true")
    args = parser.parse_args(argv)
    receipts = close_pending_agent_repairs(
        output_root=args.output_root,
        execute_actions=not args.plan_only,
        limit=args.limit,
    )
    print(json.dumps({"contract_type": "agent_repair_closure_run", "receipt_count": len(receipts), "receipts": receipts}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
