"""Original SWE templates with explicit capped transport configuration."""

import copy

from analysis.automatic_extraction_v1.common import require
from .runtime import SOURCE, load_runtime


def model_kwargs(policy):
    return {
        "parallel_tool_calls": True,
        "reasoning": {"effort": policy["reasoning_effort"]},
        "max_output_tokens": policy["output_token_limit"],
        "store": False,
        "truncation": "disabled",
        "include": ["reasoning.encrypted_content"],
    }


def capped_configuration(policy):
    load_runtime()
    import yaml

    original = yaml.safe_load((SOURCE / "minisweagent/config/benchmarks/swebench.yaml").read_text())
    result = copy.deepcopy(original)
    result["agent"].update(
        step_limit=policy["calls_per_start"],
        cost_limit=0,
        max_consecutive_format_errors=3,
        wall_time_limit_seconds=1800,
    )
    result["model"].update(
        model_class="litellm_response",
        model_name="openai/" + policy["model"],
        model_kwargs=model_kwargs(policy),
        litellm_model_registry=None,
        set_cache_control=None,
        multimodal_regex="",
        cost_tracking="ignore_errors",
    )
    require(
        all(
            result["agent"][key] == original["agent"][key]
            for key in ("system_template", "instance_template")
        )
        and all(
            result["model"][key] == original["model"][key]
            for key in ("observation_template", "format_error_template")
        ),
        "upstream templates changed",
    )
    return result
