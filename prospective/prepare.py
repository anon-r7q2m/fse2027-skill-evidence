"""Prepare the pinned native-workflow replay in a new owned workspace."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import venv


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--install", action="store_true", help="Install pinned runtime dependencies from PyPI")
    args = parser.parse_args()
    if sys.version_info[:2] != (3, 12):
        parser.error("Use CPython 3.12, matching the recorded runtime")
    bundle = Path(__file__).resolve().parent
    workspace = args.workspace.resolve()
    workspace.mkdir(parents=True, exist_ok=False)
    targets = json.loads((bundle / "protocol/source_acquisition.json").read_text())["targets"]
    sources = workspace / "sources"
    sources.mkdir()
    for target in targets:
        archive = bundle / "upstream" / (target["family"] + ".tar.gz")
        if hashlib.sha256(archive.read_bytes()).hexdigest() != target["archive_sha256"]:
            raise RuntimeError("Pinned source archive changed: " + target["family"])
        temporary = workspace / ("extract_" + target["family"])
        temporary.mkdir()
        with tarfile.open(archive, "r:gz") as source:
            source.extractall(temporary, filter="data")
        entries = list(temporary.iterdir())
        if len(entries) != 1 or not entries[0].is_dir():
            raise RuntimeError("Unexpected archive root")
        entries[0].rename(sources / target["family"])
        temporary.rmdir()
    shutil.copytree(bundle / "diagnostics", workspace / "diagnostics")
    (workspace / "cache").mkdir()
    if args.install:
        venv.EnvBuilder(with_pip=True).create(workspace / "venv")
        python = str(workspace / "venv/bin/python")
        subprocess.run([python, "-m", "pip", "install", "-r", str(bundle / "requirements.txt")], check=True)
        packages = [sources / "smolagents"] + [
            sources / "autogen/python/packages" / name
            for name in ("autogen-core", "autogen-agentchat", "autogen-ext")
        ]
        for package in packages:
            subprocess.run([python, "-m", "pip", "install", "--no-deps", "-e", str(package)], check=True)
    print(json.dumps({"workspace": str(workspace), "runtime_installed": args.install}))


if __name__ == "__main__":
    main()
