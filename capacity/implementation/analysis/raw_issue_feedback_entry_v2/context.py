"""Capture-local source delivery and identical native request-budget hints."""

import copy
from pathlib import Path
import shlex

from analysis.automatic_extraction_v1.common import canonical, parse_json, require, write_once
from analysis.editor_import_boundary_v1.host import WorkspaceBroker as PreviousBroker

from .current_source_io import CONTEXT_BYTES, intervals

HELPER = "/opt/a2s/current_source_v2.py"


async def source_context(host, discovery, snapshot, output):
    require(
        host.capture.latest_capture["snapshot_ref"] == snapshot["snapshot_ref"],
        "source must be read from the current captured tree",
    )
    host.budget.check("before_current_source")
    output = Path(output)
    specification = {
        "root": "/testbed",
        "base_commit": host.config["base_commit"],
        "snapshot_ref": snapshot["snapshot_ref"],
        "manifest": copy.deepcopy(snapshot["manifest"]),
        "intervals": intervals(discovery),
    }
    write_once(output / "input.json", specification)
    await host.solver.upload_file(Path(__file__).with_name("current_source_io.py"), HELPER)
    remote = "/opt/a2s/current_source_v2.json"
    await host.solver.upload_file(output / "input.json", remote)
    result = await host.solver.exec(
        shlex.join([host.runtime["executable"], "-B", HELPER, remote]),
        cwd="/testbed",
        timeout_sec=60,
    )
    write_once(
        output / "execution.json",
        {"return_code": result.return_code, "stdout": result.stdout, "stderr": result.stderr},
    )
    require(result.return_code == 0, "current captured source read failed")
    value = parse_json(result.stdout)
    require(
        value["snapshot_ref"] == snapshot["snapshot_ref"]
        and len(value["rendered"].encode("utf-8")) == value["rendered_bytes"] <= CONTEXT_BYTES,
        "current source identity or rendering bound differs",
    )
    host.budget.check("after_current_source")
    write_once(output / "context.json", value)
    return value


def attach(issue, context):
    return (
        issue + "\n\nAlready available source from this candidate follows. Use it to act directly "
        "when it is sufficient; ordinary repository inspection and editing remain available.\n"
        + context["rendered"]
        + "\nSource delivery dispositions:\n"
        + canonical(context["dispositions"]).decode()
    )


class RequestHints:
    def __init__(self, transport, client):
        self.transport, self.client = transport, client

    def __call__(self, base_url, api_key, model, items, effort, system, tools, **kwargs):
        remaining = self.client.policy["calls_per_start"] - len(self.client.records)
        hint = (
            f"This request counts toward your remaining {remaining} model request(s). "
            "Use already supplied source when sufficient and apply the intended repair before "
            "spending the remaining budget on repeated browsing. Keep correct code unchanged."
        )
        if remaining == 1:
            hint += " This is the last model request: no later model response will be available."
        value = copy.deepcopy(items)
        value.append({"role": "user", "content": hint})
        return self.transport(base_url, api_key, model, value, effort, system, tools, **kwargs)


class WorkspaceBroker(PreviousBroker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.transport = RequestHints(self.transport, self.client)
