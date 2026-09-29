"""Execute the frozen, finite native-workflow matrix; do not adjudicate it."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time


FAMILIES = {"smolagents": ("s11", "s12"), "autogen": ("a21", "a22")}


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def verify_freeze(study, protocol):
    initial = json.loads((protocol / "diagnostic_input_freeze.json").read_text())
    for name, expected in initial["files"].items():
        if digest(protocol / name) != expected:
            raise RuntimeError(f"Diagnostic input changed: {name}")
    records = {}
    for slots in FAMILIES.values():
        for slot in slots:
            seal = json.loads((protocol / f"{slot}_prediction_seal.json").read_text())
            for name, expected in seal["files"].items():
                if digest(study / "diagnostics" / slot / name) != expected:
                    raise RuntimeError(f"Frozen diagnostic changed: {slot}/{name}")
            records[slot] = seal
    return records


def native_path(source, family):
    if family == "smolagents":
        return str(source / "src")
    return os.pathsep.join(
        str(source / "python" / "packages" / name / "src")
        for name in ("autogen-core", "autogen-agentchat", "autogen-ext")
    )


def explicit_environment(study, source, family, temporary):
    return {
        "PATH": f"{study / 'venv' / 'bin'}:/usr/bin:/bin",
        "LANG": "C.UTF-8",
        "PYTHONPATH": native_path(source, family),
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHON_DOTENV_DISABLED": "1",
        "HF_HUB_OFFLINE": "1",
        "HF_HUB_DISABLE_TELEMETRY": "1",
        "OTEL_SDK_DISABLED": "true",
        "DO_NOT_TRACK": "1",
        "XDG_CACHE_HOME": str(study / "cache"),
        "TMPDIR": str(temporary),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study-root", required=True, type=Path)
    parser.add_argument("--protocol-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    args = parser.parse_args()
    study, protocol, output = (
        path.resolve() for path in (args.study_root, args.protocol_root, args.output_root)
    )
    seals = verify_freeze(study, protocol)
    output.mkdir(parents=True, exist_ok=False)
    save(output / "STARTED.json", {"started_at": now(), "seals": seals})
    variants = {}
    patch_records = []
    for family, slots in FAMILIES.items():
        original = study / "sources" / family
        variants[family] = {"original": original}
        for slot in slots:
            destination = output / "variants" / slot
            shutil.copytree(
                original, destination, ignore=shutil.ignore_patterns("__pycache__", ".git")
            )
            patch = study / "diagnostics" / slot / "intervention.patch"
            commands = []
            for operation in (["apply", "--check"], ["apply"]):
                completed = subprocess.run(
                    ["git", *operation, str(patch)],
                    cwd=destination,
                    env={"PATH": "/usr/bin:/bin", "GIT_CONFIG_NOSYSTEM": "1"},
                    capture_output=True,
                    text=True,
                    timeout=20,
                    check=False,
                )
                commands.append(
                    {
                        "operation": operation,
                        "return_code": completed.returncode,
                        "stdout": completed.stdout,
                        "stderr": completed.stderr,
                    }
                )
                if completed.returncode:
                    break
            applicable = all(item["return_code"] == 0 for item in commands) and len(commands) == 2
            patch_records.append({"slot": slot, "applicable": applicable, "commands": commands})
            if applicable:
                variants[family][slot] = destination
    save(output / "patch_application.json", patch_records)
    jobs = []
    for family, slots in FAMILIES.items():
        for slot in slots:
            prediction = json.loads((study / "diagnostics" / slot / "prediction.json").read_text())
            for case in prediction["cases"]:
                for variant in ("original", *slots):
                    jobs.append(
                        {
                            "family": family,
                            "input_origin": slot,
                            "case_id": case["id"],
                            "variant": variant,
                        }
                    )
    save(
        output / "execution_plan.json", {"created_at": now(), "jobs": jobs, "timeout_seconds": 120}
    )
    rows = []
    for number, job in enumerate(jobs, 1):
        run_name = f"{number:03d}_{job['input_origin']}_{job['case_id']}_{job['variant']}"
        run_dir = output / "runs" / run_name
        run_dir.mkdir(parents=True)
        row = {**job, "run_name": run_name, "started_at": now()}
        source = variants[job["family"]].get(job["variant"])
        if source is None:
            row.update(
                collection_status="NOT_EVALUATED", reason="Frozen intervention did not apply"
            )
        else:
            temporary = run_dir / "tmp"
            temporary.mkdir()
            command = [
                str(study / "venv" / "bin" / "python"),
                "-B",
                str(study / "diagnostics" / job["input_origin"] / "fixture.py"),
                "--case",
                job["case_id"],
                "--workdir",
                str(run_dir / "work"),
                "--output",
                str(run_dir / "observation.json"),
            ]
            environment = explicit_environment(study, source, job["family"], temporary)
            save(
                run_dir / "launch.json",
                {
                    "command": command,
                    "environment": environment,
                    "selected_source": str(source),
                    "started_at": row["started_at"],
                },
            )
            started = time.monotonic()
            with (
                (run_dir / "stdout.txt").open("w") as stdout,
                (run_dir / "stderr.txt").open("w") as stderr,
            ):
                child = subprocess.Popen(
                    command,
                    cwd=run_dir,
                    env=environment,
                    stdout=stdout,
                    stderr=stderr,
                    start_new_session=True,
                )
                row["process_id"] = child.pid
                try:
                    row["return_code"] = child.wait(timeout=120)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL)
                    row["return_code"] = child.wait()
                    row["timed_out"] = True
            row["elapsed_seconds"] = time.monotonic() - started
            observation = run_dir / "observation.json"
            if observation.exists():
                facts = json.loads(observation.read_text())
                row["collection_status"] = next(
                    (
                        facts[key]
                        for key in (
                            "observation_status",
                            "harness_status",
                            "collection_status",
                            "run_status",
                        )
                        if key in facts
                    ),
                    "UNKNOWN",
                )
                row["fixture_collection_status"] = row["collection_status"]
                if row["collection_status"] == "COMPLETED":
                    row["collection_status"] = "OBSERVED"
                row["observation_sha256"] = digest(observation)
            else:
                row["collection_status"] = "INCONCLUSIVE"
                row["reason"] = "No observation record"
            if row["return_code"] != 0 or row.get("timed_out"):
                row["collection_status"] = "INCONCLUSIVE"
        row["finished_at"] = now()
        save(run_dir / "receipt.json", row)
        rows.append(row)
        print(
            json.dumps(
                {
                    "finished": number,
                    "total": len(jobs),
                    "run": run_name,
                    "collection_status": row["collection_status"],
                }
            ),
            flush=True,
        )
    verify_freeze(study, protocol)
    save(
        output / "execution_summary.json",
        {"finished_at": now(), "rows": rows, "adjudication_status": "PENDING"},
    )


if __name__ == "__main__":
    main()
