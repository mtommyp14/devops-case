#!/usr/bin/env python3
"""Local canary gate and traffic controls for Case 02."""

import argparse
import json
import os
import sys
import time
from typing import Optional
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROUTER = os.getenv("LAB_ROUTER_URL", "http://127.0.0.1:8082")
PROMETHEUS = os.getenv("LAB_PROMETHEUS_URL", "http://127.0.0.1:9093")
TOKEN = os.getenv("LAB_ADMIN_TOKEN", "local-demo-token")
PROMQL = {
    "samples": 'sum(increase(portfolio_router_requests_total[1m]))',
    "canary_served_samples": 'sum(increase(portfolio_requests_total{release="canary",outcome="served"}[1m]))',
    "errors": '(sum(rate(portfolio_requests_total{release="canary",status=~"5..",outcome="served"}[1m])) / clamp_min(sum(rate(portfolio_requests_total{release="canary",outcome="served"}[1m])), 0.001)) or vector(0)',
    "canary_p95": 'histogram_quantile(0.95, sum by (le) (rate(portfolio_request_duration_seconds_bucket{release="canary"}[1m])))',
    "stable_p95": 'histogram_quantile(0.95, sum by (le) (rate(portfolio_request_duration_seconds_bucket{release="stable"}[1m])))',
}


def get_json(url: str, timeout: int = 5):
    with urlopen(url, timeout=timeout) as response:
        return json.loads(response.read())


def post_json(url: str, payload: dict, token: Optional[str] = None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-Admin-Token"] = token
    request = Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
    with urlopen(request, timeout=5) as response:
        return json.loads(response.read())


def scalar(query: str) -> Optional[float]:
    data = get_json(f"{PROMETHEUS}/api/v1/query?{urlencode({'query': query})}")
    result = data.get("data", {}).get("result", [])
    if not result:
        return None
    return float(result[0]["value"][1])


def set_weight(percent: int):
    print(post_json(f"{ROUTER}/admin/canary", {"percent": percent}, TOKEN))


def read_weight() -> int:
    return int(get_json(f"{ROUTER}/admin/canary")["canary_percent"])


def run_gate(windows: int, min_requests: int, min_canary_requests: int, interval: int) -> bool:
    for window in range(1, windows + 1):
        if window > 1:
            print(f"Waiting {interval}s for the next independent observation window…")
            time.sleep(interval)
        values = {name: scalar(query) for name, query in PROMQL.items()}
        print(f"Window {window}/{windows}: {values}")
        samples = values["samples"] or 0
        canary_samples = values["canary_served_samples"] or 0
        if samples < min_requests or values["canary_p95"] is None or values["stable_p95"] is None:
            print("HOLD: not enough total traffic or Prometheus samples; do not promote.")
            return False
        if canary_samples < min_canary_requests:
            print(
                f"HOLD: only {canary_samples:.0f} served canary requests in the window; "
                f"at least {min_canary_requests} are required to evaluate the canary."
            )
            return False
        if values["errors"] is None:
            print("HOLD: error-rate sample is unavailable.")
            return False
        if values["errors"] > 0.01 or values["canary_p95"] > 1.2 * values["stable_p95"]:
            print("FAIL: canary breached the 1% 5xx or 120% stable p95 gate.")
            return False
    print("PASS: all requested observation windows met the canary gate.")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    weight_parser = commands.add_parser("canary", help="set the canary traffic share")
    weight_parser.add_argument("percent", type=int, choices=range(0, 101))
    commands.add_parser("status", help="show the current traffic share")
    gate_parser = commands.add_parser("gate", help="evaluate Prometheus measurements before promotion")
    gate_parser.add_argument("--windows", type=int, default=2)
    gate_parser.add_argument("--min-requests", type=int, default=1000)
    gate_parser.add_argument("--min-canary-requests", type=int, default=1000)
    gate_parser.add_argument("--interval", type=int, default=60)
    promote_parser = commands.add_parser("promote", help="gate and advance to the next traffic stage")
    promote_parser.add_argument("--windows", type=int, default=2)
    promote_parser.add_argument("--min-requests", type=int, default=1000)
    promote_parser.add_argument("--min-canary-requests", type=int, default=1000)
    promote_parser.add_argument("--interval", type=int, default=60)
    commands.add_parser("rollback", help="route all traffic back to stable")
    args = parser.parse_args()
    try:
        if args.command == "canary":
            set_weight(args.percent)
        elif args.command == "status":
            print(f"canary={read_weight()}% · stable={100-read_weight()}%")
        elif args.command == "rollback":
            set_weight(0)
        elif args.command == "gate":
            return 0 if run_gate(args.windows, args.min_requests, args.min_canary_requests, args.interval) else 2
        elif args.command == "promote":
            if not run_gate(args.windows, args.min_requests, args.min_canary_requests, args.interval):
                print("Traffic was not changed.")
                return 2
            current = read_weight()
            stages = {0: 5, 5: 25, 25: 50, 50: 100}
            if current not in stages:
                print(f"No next stage configured for current canary share {current}%.")
                return 2
            set_weight(stages[current])
    except (URLError, TimeoutError, ValueError, KeyError) as exc:
        print(f"Lab control failed closed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
