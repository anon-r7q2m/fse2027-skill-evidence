"""Launch one frozen, bounded static-analysis context; never retry it."""

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("actor", choices=("A", "B"))
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, required=True)
    args = parser.parse_args()
    freeze = json.loads(args.freeze.read_text())
    assert freeze["status"] == "FROZEN_READY_FOR_ONCE_ONLY_ACTOR_LAUNCH"
    for entry in freeze["files"]:
        path = Path(entry["path"])
        assert path.is_file() and digest(path) == entry["sha256"], path
    packet = args.workspace / f"actor_{args.actor}"
    logs = args.workspace / "runs" / args.actor
    logs.mkdir(parents=True, exist_ok=False)
    prompt = packet / "ACTOR_TASK.txt"
    assert (packet / "output").is_dir()
    assert not any((packet / "output").iterdir())
    command = [
        "<codex-cli>",
        "--no-daemon", "-a", "never", "exec", "--ignore-user-config",
        "--ephemeral", "--strict-config", "--skip-git-repo-check",
        "-s", "danger-full-access", "-C", str(packet),
        "-c", 'model_provider="openai"',
        "-c", 'forced_login_method="chatgpt"',
        "-c", 'web_search="disabled"',
        "-c", "memories.use_memories=false",
        "-c", "memories.generate_memories=false",
        "-c", "features.memories=false",
        "-c", "project_doc_max_bytes=0",
        "-c", "agents.enabled=false",
        "--json", "-o", str(packet / "output" / "FINAL.txt"), "-",
    ]
    receipt = {
        "actor": args.actor, "started_at": utc_now(),
        "freeze_sha256": digest(args.freeze), "command": command,
        "time_limit_seconds": 1200, "read_search_limit": 40,
        "read_limit_enforcement": "actor instruction; full event-log audit",
        "filesystem_access_enforcement": "instruction and audit, no OS sandbox",
        "backend_model_version": "UNKNOWN", "model_override": False,
        "retry_allowed": False,
    }
    (logs / "LAUNCH.json").write_text(json.dumps(receipt, indent=2) + "\n")
    started = time.monotonic()
    timed_out = False
    with prompt.open("rb") as inp, (logs / "events.jsonl").open("wb") as out, (
        logs / "stderr.txt"
    ).open("wb") as err:
        proc = subprocess.Popen(
            command, cwd=packet, stdin=inp, stdout=out, stderr=err,
            start_new_session=True,
        )
        try:
            return_code = proc.wait(timeout=1200)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                return_code = proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                return_code = proc.wait()
    completion = {
        "actor": args.actor, "completed_at": utc_now(),
        "elapsed_seconds": time.monotonic() - started,
        "return_code": return_code, "timed_out": timed_out,
        "original_parent_wait_recorded": True,
        "output_files": {
            str(p.relative_to(packet)): digest(p)
            for p in sorted((packet / "output").rglob("*")) if p.is_file()
        },
        "events_sha256": digest(logs / "events.jsonl"),
        "adjudication": "PENDING; process exit does not establish a supported answer",
    }
    (logs / "PARENT_WAIT.json").write_text(json.dumps(completion, indent=2) + "\n")
    print(json.dumps(completion), flush=True)


if __name__ == "__main__":
    main()
