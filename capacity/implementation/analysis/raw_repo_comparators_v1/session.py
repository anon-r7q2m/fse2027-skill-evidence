"""Run source-free packages; only I/O, identity and resource limits live here."""

import copy
from pathlib import Path

from analysis.automatic_extraction_v1.common import digest, parse_json, write_once
from analysis.candidate_admission_v1.contracts import _content, _manifest
from analysis.gr_generated_effect_v1.capture import validate_bundle

from .contracts import (
    IDENTITY,
    check_candidate,
    check_handoff,
    require,
    validate_begin,
    validate_envelope,
    validate_event,
)


class Session:
    def __init__(self, program, *, logs, clock_check):
        self.program, self.logs, self.clock = program, Path(logs), clock_check
        self.role = program.role
        self.state, self.events, self.used_ids = {}, [], set()
        self.begin, self.pending = None, None
        self.status = "NOT_STARTED"

    def start(self, begin):
        require(self.status == "NOT_STARTED", "a naive session is single-use")
        validate_begin(begin, self.role)
        self.begin, self.status = copy.deepcopy(begin), "RUNNING"

    def callback(self, event):
        require(self.status == "RUNNING", "no callback outside active session")
        self.clock("before_naive_callback")
        require(
            len(self.events) < (24 if self.role == "Ln" else 3),
            "callback bound",
            "PACKAGE_RESOURCE_LIMIT",
        )
        validate_event(event, self.role)
        require(
            all(event[k] == self.begin[k] for k in IDENTITY),
            "callback run/base differs",
            "RECEIPT_IDENTITY_MISMATCH",
        )
        if self.pending is None:
            require(not self.events and event == self.begin, "only first callback may begin")
        else:
            receipts = {
                "model_request": "model_result",
                "read_files": "files_ready",
                "sample_batch": "samples_ready",
                "candidates": "captures_ready",
            }
            require(
                event["kind"] == receipts.get(self.pending["kind"])
                and event["request_id"] == self.pending["request_id"],
                "receipt must match the pending effect",
                "RECEIPT_IDENTITY_MISMATCH",
            )
        target = self.logs / f"{len(self.events) + 1:02d}_{event['kind']}"
        inputs = {"event": copy.deepcopy(event), "state": copy.deepcopy(self.state)}
        write_once(target / "input.json", inputs)
        record = {
            "event": inputs["event"],
            "input_sha256": digest(inputs),
            "package_sha256": self.program.identity,
            "worker_start": len(self.program.records),
            "completed": False,
        }
        self.events.append(record)
        try:
            result = self.program.invoke(inputs["event"], inputs["state"])
            validate_envelope(result, event, self.role)
            effect = result["effects"][0]
            require(
                effect["request_id"] not in self.used_ids,
                "effect identity reused",
                "RECEIPT_IDENTITY_MISMATCH",
            )
            self.used_ids.add(effect["request_id"])
            self.state, self.pending = copy.deepcopy(result["state"]), copy.deepcopy(effect)
            record.update(completed=True, value=copy.deepcopy(result))
            write_once(target / "output.json", result)
            self.completed_effect(effect)
            self.clock("after_naive_callback")
            return copy.deepcopy(effect)
        except BaseException as exc:
            record.update(
                exception_type=type(exc).__name__, exception_category=getattr(exc, "category", None)
            )
            raise
        finally:
            record["worker_stop"] = len(self.program.records)
            write_once(target / "invocation.json", record)

    def receipt(self, kind, effect, **fields):
        value = {
            "kind": kind,
            **{k: self.begin[k] for k in IDENTITY},
            "request_id": effect["request_id"],
            **copy.deepcopy(fields),
        }
        validate_event(value, self.role)
        return value

    def completed_effect(self, effect):
        pass

    def snapshot(self):
        return {
            "status": self.status,
            "package_sha256": self.program.identity,
            "begin": self.begin,
            "events": self.events,
            "worker_records": self.program.records,
        }


class LocatorSession(Session):
    def __init__(self, program, **kwargs):
        super().__init__(program, **kwargs)
        require(self.role == "Ln", "locator package required")
        self.files, self.query_ids = {}, set()
        self.read_paths, self.read_done, self.handoff = [], False, None
        self.output_failed = False

    @property
    def progress(self):
        if self.handoff is not None:
            return {
                key: copy.deepcopy(self.handoff[key])
                for key in ("selected_files", "localized_files", "locations")
            }
        return {
            "selected_files": copy.deepcopy(self.read_paths),
            "localized_files": [],
            "locations": [],
        }

    def completed_effect(self, effect):
        require(
            not self.output_failed or effect["kind"] == "localization_handoff",
            "charged output failure must hand off",
            "PROTOCOL_REJECTED",
        )
        if effect["kind"] == "localization_handoff":
            require(
                not self.output_failed or effect["status"] == "NO_LOCALIZATION",
                "charged output failure cannot claim localization",
                "PROTOCOL_REJECTED",
            )
            check_handoff(effect, self.begin, self.files)
            self.handoff = copy.deepcopy(effect)

    def run(self, begin, *, read_files, model_request):
        self.start(begin)
        try:
            event = self.begin
            while True:
                effect = self.callback(event)
                if effect["kind"] == "read_files":
                    require(not self.read_done, "one file read batch", "PACKAGE_RESOURCE_LIMIT")
                    require(
                        set(effect["paths"]) <= set(begin["tracked_paths"]),
                        "read only tracked files",
                        "RECEIPT_IDENTITY_MISMATCH",
                    )
                    self.read_done, self.read_paths = True, copy.deepcopy(effect["paths"])
                    rows = read_files(copy.deepcopy(self.read_paths))
                    event = self.receipt("files_ready", effect, files=rows)
                    require(
                        [row["path"] for row in rows] == self.read_paths,
                        "read receipt cannot reorder or substitute files",
                        "RECEIPT_IDENTITY_MISMATCH",
                    )
                    self.files = {row["path"]: copy.deepcopy(row) for row in rows}
                elif effect["kind"] == "model_request":
                    require(
                        len(self.query_ids) < 5,
                        "five actual locator queries",
                        "PACKAGE_RESOURCE_LIMIT",
                    )
                    result = model_request(copy.deepcopy(effect))
                    event = self.receipt("model_result", effect, **result)
                    require(
                        result["purpose"] == effect["purpose"],
                        "model receipt purpose",
                        "RECEIPT_IDENTITY_MISMATCH",
                    )
                    if result["query_id"] is not None:
                        require(
                            result["query_id"] == len(self.query_ids) + 1,
                            "fresh ordered actual query",
                            "RECEIPT_IDENTITY_MISMATCH",
                        )
                        self.query_ids.add(result["query_id"])
                    self.output_failed = result["status"] == "output_failed"
                else:
                    self.handoff, self.status = copy.deepcopy(effect), "HANDOFF_READY"
                    return copy.deepcopy(effect)
        except BaseException as exc:
            self.status = "STOPPED_" + getattr(exc, "category", type(exc).__name__)
            raise
        finally:
            write_once(self.logs / "session.json", self.snapshot())

    def snapshot(self):
        return {
            **super().snapshot(),
            "read_paths": self.read_paths,
            "delivered_model_queries": len(self.query_ids),
            "handoff": self.handoff,
        }


def check_capture(snapshot, content, sample, begin):
    """Check the captured bytes, without deciding whether an edit is good."""
    folder = Path(snapshot["directory"])
    manifest = snapshot["manifest"]
    # These are byte/manifest validators only; no admission or parser is invoked.
    _manifest(manifest)
    _content(content, manifest)
    require(
        snapshot["run_id"] == begin["run_id"]
        and manifest["base_commit"] == begin["base_commit"]
        and manifest["base_tree"] == begin["base_snapshot_ref"]
        and manifest["final_tree"] == snapshot["snapshot_ref"]
        and snapshot["bundle"]["final_tree"] == snapshot["snapshot_ref"]
        and parse_json((folder / "capture_manifest.json").read_bytes()) == manifest
        and validate_bundle(folder, begin["base_commit"]) == snapshot["bundle"],
        "capture belongs to the original run/base/files",
        "RECEIPT_IDENTITY_MISMATCH",
    )
    edits = {row["path"]: row for row in sample["files"]}
    changed = {p for p, row in edits.items() if row["before"] != row["after"]}
    require(
        {row["path"] for row in manifest["files"]} == changed,
        "capture omitted or added a workspace change",
        "RECEIPT_IDENTITY_MISMATCH",
    )
    require(
        content["status"] == "available"
        and [row["path"] for row in content["files"]] == sorted(changed),
        "complete materialized text receipt required",
        "RECEIPT_IDENTITY_MISMATCH",
    )
    modes = {row["path"]: row["mode"] for row in begin["files"]}
    for row, captured in zip(content["files"], manifest["files"], strict=True):
        declared = edits[row["path"]]
        require(
            {k: row[k] for k in captured} == captured
            and row["change"] == "M"
            and row["before_text"] == declared["before"]
            and row["after_text"] == declared["after"]
            and row["before"]["git_mode"] == row["after"]["git_mode"] == modes[row["path"]],
            "captured full text or mode differs from package effect",
            "RECEIPT_IDENTITY_MISMATCH",
        )


class PoolSession(Session):
    def __init__(self, program, **kwargs):
        super().__init__(program, **kwargs)
        require(self.role == "Pn", "editor package required")
        self.requests, self.sample_records, self.captures = [], [], {}
        self.selection = None

    async def run(self, begin, *, sample_request, materialize_capture):
        self.start(begin)
        try:
            batch = self.callback(self.begin)
            require(batch["kind"] == "sample_batch", "begin must propose the sample batch")
            self.requests = [
                {
                    "sample_index": index,
                    "request_id": f"sample{index}",
                    "items": [{"role": "user", "content": batch["prompt"]}],
                    "instructions": batch["instructions"],
                    "tools": [],
                    "limits": copy.deepcopy(begin["limits"]),
                }
                for index in range(1, 5)
            ]
            write_once(
                self.logs / "sample_batch.json", {"effect": batch, "requests": self.requests}
            )
            for request in self.requests:
                self.clock("before_naive_sample")
                response = await sample_request(copy.deepcopy(request))
                require(
                    type(response) is dict
                    and response.get("sample_index") == request["sample_index"]
                    and response.get("request_id") == request["request_id"],
                    "actual sample account identity differs",
                    "RECEIPT_IDENTITY_MISMATCH",
                )
                self.sample_records.append(copy.deepcopy(response))
                write_once(self.logs / "samples" / f"{request['sample_index']}.json", response)
                self.clock("after_naive_sample")
            samples = [
                {k: row[k] for k in ("sample_index", "status", "text")}
                for row in self.sample_records
            ]
            parsed = self.callback(self.receipt("samples_ready", batch, samples=samples))
            require(parsed["kind"] == "candidates", "sample results require candidate decisions")
            captured = []
            for sample, response in zip(parsed["samples"], self.sample_records, strict=True):
                check_candidate(sample, begin, response)
                ref = None
                if sample["status"] == "accepted":
                    self.clock("before_naive_materialization")
                    snapshot, content = await materialize_capture(copy.deepcopy(sample))
                    check_capture(snapshot, content, sample, begin)
                    self.captures[sample["sample_index"]] = copy.deepcopy(snapshot)
                    ref = snapshot["snapshot_ref"]
                    self.clock("after_naive_materialization")
                captured.append(
                    {
                        "sample_index": sample["sample_index"],
                        "status": sample["status"],
                        "snapshot_ref": ref,
                    }
                )
            choice = self.callback(self.receipt("captures_ready", parsed, samples=captured))
            require(choice["kind"] == "selection", "captured batch requires a selection")
            index = choice["sample_index"]
            require(
                index is None or index in self.captures,
                "selection must name an actual candidate",
                "RECEIPT_IDENTITY_MISMATCH",
            )
            self.selection = {
                "mode": "empty_base" if index is None else "candidate",
                "sample_index": index,
                "snapshot_ref": begin["base_snapshot_ref"]
                if index is None
                else self.captures[index]["snapshot_ref"],
                "reason": choice["reason"],
            }
            self.status = "SELECTION_COMPLETE"
            return copy.deepcopy(self.selection)
        except BaseException as exc:
            self.status = "STOPPED_" + getattr(exc, "category", type(exc).__name__)
            raise
        finally:
            write_once(self.logs / "session.json", self.snapshot())

    def snapshot(self):
        return {
            **super().snapshot(),
            "samples": self.sample_records,
            "captures": self.captures,
            "selection": self.selection,
        }
