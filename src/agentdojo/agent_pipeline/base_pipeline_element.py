import abc
from collections.abc import Sequence

from agentdojo.functions_runtime import EmptyEnv, Env, FunctionsRuntime
from agentdojo.types import ChatMessage

defence_params = {
    "tool_policies": "",
    "max_retry_attempts": 12,
    "max_n_turns": 20,
    "n_plans": None,
    "clear_history_every_n_attempts": 4,  # only works in single-step mode
    "retry_on_policy_violation": True,
    "allow_undefined_tools": True,
    "fail_fast": True,
    "enable_multistep_planning": False,
    "reasoning_effort": "low",  # "minimal" #"medium" # low
    "plan_reduction": "best",  # "merge"
    "auto_gen_policies": False,
    "dual_llm_mode": True,
    "strict_mode": False,
    "min_num_tools_for_filtering": 2,
    "pllm_debug_info_level": "normal",  # "minimal", "normal", "extra"
    "reduced_grammar_for_rllm_review": False,
    "rllm_confidence_score_threshold": None,
}

import json


def smart_update_headers(headers, flat_update_json):
    """
    Deserializes header values, searches for keys provided in 'flat_update_json',
    updates them wherever they are found (nested dicts or lists), and reserializes.

    Args:
        headers (dict): The dictionary of headers with JSON-string values.
        flat_update_json (str): A JSON string of keys/values to update.
                                E.g., '{"max_n_turns": 99, "default_allow": false}'
    """

    # 1. Deserialize the update payload
    try:
        updates = json.loads(flat_update_json)
    except json.JSONDecodeError as e:
        print(f"Error parsing update payload: {e}")
        return headers

    for update in updates:
        if update not in headers:
            raise Exception("Unsupported key " + str(update))
        headers[update] = updates[update]

    return headers


class BasePipelineElement(abc.ABC):
    """Base class for agent pipeline elements.

    Subclasses must implement the [`query`][agentdojo.agent_pipeline.BasePipelineElement.query] method.
    """

    name: str | None = None

    @abc.abstractmethod
    def query(
        self,
        query: str,
        runtime: FunctionsRuntime,
        env: Env = EmptyEnv(),
        messages: Sequence[ChatMessage] = [],
        extra_args: dict = {},
    ) -> tuple[str, FunctionsRuntime, Env, Sequence[ChatMessage], dict]:
        """Executes the element of the pipeline on the given query, runtime, environment, and messages.

        Must be implemented by the subclass.

        Args:
            query: the query to execute.
            runtime: the runtime that can be used by the agent to execute tools.
            env: the environment on which the agent is operating.
            messages: the list of chat messages exchanged between the agent, the user, and the tools.
            extra_args: extra arguments that can be used by the agent to execute the query and passed around
                among different pipeline elements.
        """
        pass
