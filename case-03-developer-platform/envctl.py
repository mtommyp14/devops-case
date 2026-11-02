#!/usr/bin/env python3
"""Provision and clean exact, local PR Compose projects for Case 03."""

import argparse
import fcntl
import json
import os
import re
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Optional
from urllib.error import URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent
STATE = ROOT / ".lab-state"
PROJECT_RE = re.compile(r"pr-([1-9][0-9]*)-g([1-9][0-9]*)\Z")


@contextmanager
def pr_lock(pr: int):
    locks = STATE / "locks"
    locks.mkdir(parents=True, exist_ok=True)
    with (locks / f"pr-{pr}.lock").open("w") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield


def run_compose(project: str, args: list[str], env: Optional[dict[str, str]] = None, check: bool = True):
    if not PROJECT_RE.fullmatch(project):
        raise ValueError("refusing a project name outside the exact PR/generation format")
    child_env = os.environ.copy()
    if env:
        child_env.update(env)
    command = ["docker", "compose", "-f", str(ROOT / "compose.yaml"), "-p", project, *args]
    return subprocess.run(command, cwd=ROOT, env=child_env, check=check)


def state_path(project: str) -> Path:
    if not PROJECT_RE.fullmatch(project):
        raise ValueError("invalid project name in state")
    return STATE / f"{project}.json"


def pointer_path(pr: int) -> Path:
    return STATE / f"pr-{pr}.json"


def atomic_write(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, indent=2) + "\n")
    temp.replace(path)


def probe(port: int, attempts: int = 60):
    url = f"http://127.0.0.1:{port}/health"
    for _ in range(attempts):
        try:
            with urlopen(url, timeout=2) as response:
                if response.status == 200:
                    health = json.loads(response.read())
                    with urlopen(f"http://127.0.0.1:{port}/items", timeout=2) as items_response:
                        items = json.loads(items_response.read()).get("items", [])
                    if health.get("status") == "ready" and len(items) == 3:
                        print(json.dumps({"health": health, "smoke_items": len(items)}))
                        return
        except (URLError, TimeoutError, OSError):
            time.sleep(2)
    raise RuntimeError(f"preview did not become ready at {url}")


def cleanup_project(project: str):
    record = state_path(project)
    result = run_compose(project, ["down", "--volumes", "--remove-orphans"], check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Compose could not confirm cleanup for {project}; state record retained")
    if record.exists():
        record.unlink()


def provision(args):
    if args.pr < 1 or args.generation < 1 or not 1024 <= args.port <= 65535:
        raise ValueError("PR and generation must be positive; preview port must be 1024–65535")
    project = f"pr-{args.pr}-g{args.generation}"
    pointer = pointer_path(args.pr)
    with pr_lock(args.pr):
        previous = read_current(args.pr) if pointer.exists() else None
        if previous and args.generation < int(previous["generation"]):
            raise ValueError(f"stale generation {args.generation}; current generation is {previous['generation']}")
        if previous and args.generation == int(previous["generation"]) and previous["project"] != project:
            raise ValueError("generation metadata is inconsistent")
        if previous and previous["project"] == project and int(previous["port"]) != args.port:
            raise ValueError("repeating the current generation must reuse its recorded preview port")
        if args.ttl_hours < 1:
            raise ValueError("TTL must be at least one hour")
        now = int(time.time())
        expires = now + args.ttl_hours * 3600
        env = {"PR_NUMBER": str(args.pr), "GENERATION": str(args.generation), "PREVIEW_PORT": str(args.port)}
        pending = {"pr": args.pr, "generation": args.generation, "project": project, "port": args.port, "status": "provisioning", "expires_at": now + 900}
        same_project_record = None
        if previous and previous["project"] == project:
            current_state = state_path(project)
            same_project_record = json.loads(current_state.read_text()) if current_state.exists() else previous
        atomic_write(state_path(project), pending)
        try:
            run_compose(project, ["up", "-d", "db"], env)
            run_compose(project, ["run", "--rm", "seed"], env)
            run_compose(project, ["up", "-d", "app"], env)
            probe(args.port)
        except Exception:
            if previous and previous["project"] == project:
                atomic_write(state_path(project), same_project_record)
            else:
                cleanup_project(project)
            raise
        record = {**pending, "status": "ready", "expires_at": expires, "url": f"http://127.0.0.1:{args.port}"}
        atomic_write(state_path(project), record)
        atomic_write(pointer, record)
        if previous and previous["project"] != project:
            cleanup_project(previous["project"])
        print(json.dumps(record, indent=2))


def read_current(pr: int):
    pointer = pointer_path(pr)
    if not pointer.exists():
        raise ValueError(f"no tracked preview for PR {pr}")
    record = json.loads(pointer.read_text())
    project = record.get("project")
    match = PROJECT_RE.fullmatch(project) if isinstance(project, str) else None
    if (
        record.get("pr") != pr
        or not match
        or int(match.group(1)) != pr
        or int(match.group(2)) != int(record.get("generation", -1))
    ):
        raise ValueError("invalid preview state; refusing cleanup")
    return record


def cleanup_pr(pr: int):
    with pr_lock(pr):
        record = read_current(pr)
        cleanup_project(record["project"])
        pointer_path(pr).unlink(missing_ok=True)
        print(f"cleaned {record['project']}")


def sweep():
    now = int(time.time())
    for record_file in sorted(STATE.glob("pr-*-g*.json")):
        try:
            record = json.loads(record_file.read_text())
            project = record.get("project")
            match = PROJECT_RE.fullmatch(project) if isinstance(project, str) else None
            if (
                not match
                or record_file != state_path(project)
                or int(match.group(1)) != int(record.get("pr", -1))
                or int(match.group(2)) != int(record.get("generation", -1))
                or int(record.get("expires_at", 0)) > now
            ):
                continue
            pr = int(match.group(1))
            with pr_lock(pr):
                current = json.loads(record_file.read_text()) if record_file.exists() else None
                if not current or int(current.get("expires_at", 0)) > now:
                    continue
                cleanup_project(current["project"])
                pointer = pointer_path(pr)
                if pointer.exists() and json.loads(pointer.read_text()).get("project") == current["project"]:
                    pointer.unlink()
                print(f"expired {current['project']}")
        except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
            print(f"skip invalid state {record_file.name}: {exc}", file=sys.stderr)
        except RuntimeError as exc:
            print(f"cleanup pending for {record_file.name}: {exc}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("provision")
    create.add_argument("--pr", type=int, required=True)
    create.add_argument("--generation", type=int, required=True)
    create.add_argument("--port", type=int, required=True)
    create.add_argument("--ttl-hours", type=int, default=24)
    remove = commands.add_parser("cleanup")
    remove.add_argument("--pr", type=int, required=True)
    commands.add_parser("sweep")
    listing = commands.add_parser("status")
    listing.add_argument("--pr", type=int)
    args = parser.parse_args()
    try:
        if args.command == "provision":
            provision(args)
        elif args.command == "cleanup":
            cleanup_pr(args.pr)
        elif args.command == "sweep":
            sweep()
        elif args.command == "status":
            records = [read_current(args.pr)] if args.pr else [json.loads(p.read_text()) for p in sorted(STATE.glob("pr-[0-9]*.json")) if "-g" not in p.name]
            print(json.dumps(records, indent=2))
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"environment operation failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
