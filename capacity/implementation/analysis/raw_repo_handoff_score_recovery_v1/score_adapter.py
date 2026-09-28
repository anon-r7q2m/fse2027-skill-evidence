"""Unchanged original bundle transport with the explicit successor grader identity."""

import asyncio
import json
import sys

from analysis.raw_repo_comparator_scored_v1.score_adapter import configuration
from analysis.sweagent_chooser_pool_v1 import score_adapter as original

from .scorer import GRADER_ID


def install():
    original.configuration = configuration


def __getattr__(name):
    if name in {"OriginalBundleAgent", "ScoreEnvironment"}:
        install()
        return getattr(original, name)
    raise AttributeError(name)


def consume(scope_path, process):
    from analysis.sweagent_chooser_pool_v1 import scoring

    previous, previous_id = scoring.configuration, scoring.GRADER_ID
    scoring.configuration, scoring.GRADER_ID = configuration, GRADER_ID
    try:
        return scoring.consume(scope_path, process)
    finally:
        scoring.configuration, scoring.GRADER_ID = previous, previous_id


if __name__ == "__main__":
    install()
    try:
        asyncio.run(original.child(sys.argv[1]))
    except Exception as exc:
        print(json.dumps({"status": "SCORE_CHILD_STOPPED", "error_type": type(exc).__name__}))
        raise SystemExit(1) from None
