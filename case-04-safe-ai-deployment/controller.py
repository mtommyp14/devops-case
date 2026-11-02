"""Fail-closed policy, approval, and mock deployment controller."""

import argparse
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

import requests

PLAN = Path(os.environ.get("PLAN_FILE", "/plans/plan.json"))
AUDIT = Path(os.environ.get("AUDIT_FILE", "/audit/events.jsonl"))
OPA = os.environ.get("OPA_URL", "http://opa:8181")
TARGET = os.environ.get("TARGET_URL", "http://target:8080")
TOKEN = os.environ.get("DUMMY_DEPLOY_TOKEN", "local-only-demo-token")
SECRET_PATTERNS = {
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "cloud_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "token_assignment": re.compile(r"(?i)(?:api[_-]?key|password|access[_-]?token)\s*[:=]\s*[\"'][^\"']{8,}[\"']"),
}


def load_plan():
    plan = json.loads(PLAN.read_text())
    canonical = json.dumps(plan, sort_keys=True, separators=(",", ":")).encode()
    return plan, hashlib.sha256(canonical).hexdigest()


def audit(event: dict):
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    record = {"time": int(time.time()), **event}
    with AUDIT.open("a") as stream:
        stream.write(json.dumps(record, sort_keys=True) + "\n")


def evaluate(plan: dict):
    response = requests.post(f"{OPA}/v1/data/deployment/decision", json={"input": plan}, timeout=2)
    response.raise_for_status()
    result = response.json().get("result")
    if not isinstance(result, dict):
        raise RuntimeError("policy returned no decision")
    return result


def scan_secrets(plan: dict):
    serialized = json.dumps(plan, sort_keys=True)
    return [name for name, pattern in SECRET_PATTERNS.items() if pattern.search(serialized)]


def target_request(path: str, payload=None):
    headers = {"Authorization": f"Bearer {TOKEN}"}
    if payload is None:
        response = requests.get(f"{TARGET}{path}", headers=headers, timeout=3)
    else:
        response = requests.post(f"{TARGET}{path}", json=payload, headers=headers, timeout=3)
    response.raise_for_status()
    return response.json()


def command_hash():
    plan, digest = load_plan()
    print(json.dumps({"task_id": plan.get("task_id"), "artifact_sha256": digest, "target": plan.get("target")}))


def command_inspect():
    plan, digest = load_plan()
    findings = scan_secrets(plan)
    if findings:
        print(json.dumps({"artifact_sha256": digest, "secret_findings": findings, "decision": "denied"}, indent=2))
        return
    decision = evaluate(plan)
    print(json.dumps({"task_id": plan.get("task_id"), "artifact_sha256": digest, "decision": decision}, indent=2))


def command_audit():
    if not AUDIT.exists():
        print("[]")
        return
    records = [json.loads(line) for line in AUDIT.read_text().splitlines() if line.strip()]
    print(json.dumps(records, indent=2))


def command_apply(approval_hash: str | None):
    plan, digest = load_plan()
    findings = scan_secrets(plan)
    if findings:
        audit({"task_id": plan.get("task_id"), "artifact_sha256": digest, "decision": "secret_scan_denied", "findings": findings})
        raise RuntimeError(f"secret scan blocked the plan: {findings}")
    try:
        decision = evaluate(plan)
    except Exception as exc:
        audit({"task_id": plan.get("task_id"), "artifact_sha256": digest, "decision": "policy_unavailable", "error": type(exc).__name__})
        raise RuntimeError("policy service unavailable or invalid; deployment stopped") from exc
    if decision.get("allowed") is not True:
        audit({"task_id": plan.get("task_id"), "artifact_sha256": digest, "decision": "denied", "reasons": decision.get("reasons", [])})
        raise RuntimeError(f"policy denied artifact: {decision.get('reasons', [])}")
    risk = decision.get("risk")
    if risk == "high" and approval_hash != digest:
        audit({"task_id": plan.get("task_id"), "artifact_sha256": digest, "decision": "approval_required", "risk": risk})
        raise RuntimeError(f"human approval required; approve this exact artifact hash: {digest}")
    if risk not in {"low", "high"}:
        raise RuntimeError("policy returned an unknown risk classification; deployment stopped")

    previous = target_request("/state")["release"]
    audit({"task_id": plan.get("task_id"), "artifact_sha256": digest, "decision": "approved", "risk": risk, "target": plan.get("target")})
    target_request("/deploy", {"release": plan["deploy"]["release"], "artifact_sha256": digest})
    health = requests.get(f"{TARGET}/health", timeout=3)
    if health.status_code == 200:
        audit({"task_id": plan.get("task_id"), "artifact_sha256": digest, "decision": "deployed", "release": plan["deploy"]["release"]})
        print(json.dumps({"result": "deployed", "release": plan["deploy"]["release"], "health": health.json()}))
        return

    target_request("/deploy", {"release": previous, "artifact_sha256": "rollback"})
    rollback_health = requests.get(f"{TARGET}/health", timeout=3)
    audit({"task_id": plan.get("task_id"), "artifact_sha256": digest, "decision": "rolled_back", "restored_release": previous, "rollback_healthy": rollback_health.status_code == 200})
    print(json.dumps({"result": "rolled_back", "failed_release": plan["deploy"]["release"], "restored_release": previous, "rollback_healthy": rollback_health.status_code == 200}))
    raise RuntimeError("deployment health check failed; previous release restored")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("hash", help="print the canonical plan hash to bind an approval")
    sub.add_parser("inspect", help="evaluate the current plan without deploying")
    sub.add_parser("audit", help="print the append-only local audit records")
    apply = sub.add_parser("apply", help="validate, approve if needed, and deploy to the local mock")
    apply.add_argument("--approval-hash")
    args = parser.parse_args()
    try:
        if args.command == "hash":
            command_hash()
        elif args.command == "inspect":
            command_inspect()
        elif args.command == "audit":
            command_audit()
        else:
            command_apply(args.approval_hash)
    except Exception as exc:
        print(f"deployment stopped: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
