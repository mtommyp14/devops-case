"""A deterministic proposal fixture runner; it does not call an AI model."""

import json
import os
import re
from pathlib import Path

scenario = os.environ.get("SCENARIO", "safe")
if not re.fullmatch(r"[a-z0-9-]{1,40}", scenario):
    raise SystemExit("invalid scenario name")
source = Path("/scenarios") / f"{scenario}.json"
if not source.is_file():
    raise SystemExit(f"unknown scenario: {scenario}")
plan = json.loads(source.read_text())
destination = Path(os.environ.get("PLAN_FILE", "/out/plan.json"))
destination.parent.mkdir(parents=True, exist_ok=True)
destination.write_text(json.dumps(plan, sort_keys=True, indent=2) + "\n")
print(json.dumps({"task_id": plan.get("task_id"), "scenario": scenario, "artifact": str(destination)}))
