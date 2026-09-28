"""Meter the naive locator without imposing the source mechanism's stages."""

import asyncio
import copy
from pathlib import Path

from analysis.automatic_extraction_v1.common import require, write_once
from analysis.hint_host_effect_v1.native import NativeStop
from analysis.raw_repo_localization_v1.budget import BudgetStop
from analysis.search_replace_effect_v1.sampling import LOCAL_STOPS, known_output_stop, sample_text

from .session import LocatorSession


class Locator:
    def __init__(self, program, logs):
        self.program, self.logs = program, Path(logs)
        self.session = self.client = None
        self.previews, self.model_rows = [], []

    async def __call__(self, repository, issue, budget, client, run_id):
        require(
            self.client is None and not client.records and client.pending is None,
            "fresh locator account",
        )
        require(client.policy["calls_per_start"] == 5, "five-query locator ceiling")
        self.client = client
        budget.bind("localization", client, "discovery")
        return await asyncio.to_thread(self.run, repository, issue, budget, run_id)

    def run(self, repository, issue, budget, run_id):
        session = self.session = LocatorSession(
            self.program, logs=self.logs / "session", clock_check=budget.check
        )
        begin = {
            "kind": "begin",
            "run_id": run_id,
            "base_commit": repository.base_commit,
            "base_snapshot_ref": repository.base_tree,
            "issue": issue,
            "tracked_paths": sorted(repository.rows),
        }

        def query(effect):
            budget.check("before_naive_locator_preview")
            items = [{"role": "user", "content": effect["prompt"]}]
            preview = self.client.preview(items, "", [])
            self.previews.append(
                {"request_id": effect["request_id"], "purpose": effect["purpose"], **preview}
            )
            receipt = {
                "purpose": effect["purpose"],
                "status": "context_limit",
                "text": None,
                "input_tokens": preview["estimated_input_tokens"],
                "query_id": None,
            }
            if preview["stop"]:
                require(
                    preview["stop"] in {"LOCAL_CONTEXT_LIMIT", "LOCAL_BODY_LIMIT"},
                    "known unsent preview stop",
                )
                return receipt
            before = len(self.client.records)
            status, text = "completed", None
            try:
                result = self.client.request(items, "", [], "solve")
            except NativeStop:
                if not known_output_stop(self.client):
                    raise
                status = "output_failed"
            else:
                text, failure = sample_text(result.response)
                if failure:
                    status = "output_failed"
            finally:
                self.model_rows.append(
                    {
                        "request_id": effect["request_id"],
                        "purpose": effect["purpose"],
                        "records": copy.deepcopy(self.client.records[before:]),
                    }
                )
            budget.require_known()
            require(len(self.client.records) == before + 1, "one actual request per query effect")
            row = self.client.records[-1]
            budget.check("after_naive_locator_commit")
            return {
                **receipt,
                "status": status,
                "text": text if status == "completed" else None,
                "query_id": row["number"],
                "input_tokens": row["usage"]["input_tokens"],
            }

        result = None
        try:
            result = session.run(begin, read_files=repository.files, model_request=query)
        except BudgetStop as exc:
            result = {"status": "LOCALIZATION_BUDGET_STOP", "reason": str(exc), **session.progress}
        except NativeStop:
            budget.require_known()
            require(
                self.client.stop in LOCAL_STOPS or known_output_stop(self.client),
                "exogenous locator failure is unresolved",
            )
            result = {
                "status": "LOCALIZATION_NATIVE_STOP",
                "reason": self.client.stop,
                **session.progress,
            }
        finally:
            write_once(
                self.logs / "adapter.json",
                {
                    "package_sha256": self.program.identity,
                    "previews": self.previews,
                    "model_rows": self.model_rows,
                    "client": self.client.snapshot(),
                    "progress": session.progress,
                    "result": result,
                },
            )
        budget.require_known()
        return {
            **result,
            "package_sha256": self.program.identity,
            "requests": len(self.client.records),
        }
