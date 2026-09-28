"""Load the pinned public wheel without reading an ambient mini configuration."""

import importlib.metadata
import json
import os
from pathlib import Path
import sys
import tempfile

from analysis.automatic_extraction_v1.common import file_sha, require
from analysis.history_host_effect_v1.harbor_entry import load_harbor

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "experiments/mini_swe_capped_v1"
SOURCE = PACKAGE / "source/wheel"
DEPENDENCIES = PACKAGE / "dependencies/site"
_configuration = None


def load_runtime():
    global _configuration
    if _configuration is not None:
        return
    require("minisweagent" not in sys.modules, "mini runtime was imported before config isolation")
    load_harbor()
    for manifest_path, directory in (
        (PACKAGE / "source/manifest.json", SOURCE),
        (PACKAGE / "dependencies/manifest.json", DEPENDENCIES),
    ):
        manifest = json.loads(manifest_path.read_bytes())
        for name, sha in manifest["files"].items():
            path = directory / name
            require(not path.is_symlink() and file_sha(path) == sha, "pinned wheel file changed")
    # The upstream package reads .env under this explicit, new empty directory.
    # It is never allowed to discover a user configuration or credential path.
    _configuration = tempfile.TemporaryDirectory(prefix="a2s-mini-empty-config-")
    os.environ["MSWEA_GLOBAL_CONFIG_DIR"] = _configuration.name
    os.environ["MSWEA_SILENT_STARTUP"] = "1"
    os.environ["MSWEA_MODEL_RETRY_STOP_AFTER_ATTEMPT"] = "1"
    os.environ["MSWEA_GLOBAL_COST_LIMIT"] = "0"
    os.environ["MSWEA_GLOBAL_CALL_LIMIT"] = "0"
    os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"
    os.environ["LITELLM_TELEMETRY"] = "False"
    sys.path[:0] = [str(SOURCE), str(DEPENDENCIES)]
    import minisweagent

    require(
        minisweagent.__version__ == "2.4.6"
        and Path(minisweagent.__file__).resolve() == SOURCE / "minisweagent/__init__.py"
        and not (Path(_configuration.name) / ".env").exists(),
        "mini runtime/config identity differs",
    )


def runtime_identity():
    load_runtime()
    return {
        "mini_version": "2.4.6",
        "source_manifest_sha256": file_sha(PACKAGE / "source/manifest.json"),
        "dependency_manifest_sha256": file_sha(PACKAGE / "dependencies/manifest.json"),
        "python": list(sys.version_info[:3]),
        "dependencies": {
            name: importlib.metadata.version(name)
            for name in (
                "harbor",
                "litellm",
                "openai",
                "pydantic",
                "jinja2",
                "tenacity",
                "rich",
                "python-dotenv",
                "platformdirs",
                "PyYAML",
                "tiktoken",
            )
        },
        "imports": {
            name: str(Path(__import__(name, fromlist=["__file__"]).__file__).resolve())
            for name in (
                "minisweagent.agents.default",
                "minisweagent.models.litellm_response_model",
                "minisweagent.environments.local",
                "platformdirs",
            )
        },
        "configuration": "NEW_EMPTY_DIRECTORY_WITHOUT_DOTENV",
    }
