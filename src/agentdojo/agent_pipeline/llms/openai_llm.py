import json
import os
from collections.abc import Sequence
from typing import overload

import openai
import requests
import yaml
from openai._types import NOT_GIVEN
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionAssistantMessageParam,
    ChatCompletionContentPartTextParam,
    ChatCompletionDeveloperMessageParam,
    ChatCompletionMessage,
    ChatCompletionMessageParam,
    ChatCompletionMessageToolCall,
    ChatCompletionMessageToolCallParam,
    ChatCompletionReasoningEffort,
    ChatCompletionToolMessageParam,
    ChatCompletionToolParam,
    ChatCompletionUserMessageParam,
)
from openai.types.shared_params import FunctionDefinition
from tenacity import retry, retry_if_not_exception_type, stop_after_attempt, wait_random_exponential

from agentdojo.agent_pipeline.base_pipeline_element import BasePipelineElement, defence_params
from agentdojo.functions_runtime import EmptyEnv, Env, Function, FunctionCall, FunctionsRuntime
from agentdojo.types import (
    ChatAssistantMessage,
    ChatMessage,
    ChatSystemMessage,
    ChatToolResultMessage,
    ChatUserMessage,
    MessageContentBlock,
    get_text_content_as_str,
    text_content_block_from_string,
)


def _tool_call_to_openai(tool_call: FunctionCall) -> ChatCompletionMessageToolCallParam:
    if tool_call.id is None:
        raise ValueError("`tool_call.id` is required for OpenAI")
    return ChatCompletionMessageToolCallParam(
        id=tool_call.id,
        type="function",
        function={
            "name": tool_call.function,
            "arguments": json.dumps(tool_call.args),
        },
    )


_REASONING_MODELS = {"o1", "o3"}


def _is_reasoning_model(model_name: str) -> bool:
    return any(model in model_name for model in _REASONING_MODELS)


@overload
def _content_blocks_to_openai_content_blocks(
    message: ChatUserMessage | ChatSystemMessage,
) -> list[ChatCompletionContentPartTextParam]: ...


@overload
def _content_blocks_to_openai_content_blocks(
    message: ChatAssistantMessage | ChatToolResultMessage,
) -> list[ChatCompletionContentPartTextParam] | None: ...


def _content_blocks_to_openai_content_blocks(
    message: ChatUserMessage | ChatAssistantMessage | ChatSystemMessage | ChatToolResultMessage,
) -> list[ChatCompletionContentPartTextParam] | None:
    if message["content"] is None:
        return None
    return [ChatCompletionContentPartTextParam(type="text", text=el["content"] or "") for el in message["content"]]


def _message_to_openai(message: ChatMessage, model_name: str) -> ChatCompletionMessageParam:
    match message["role"]:
        case "system":
            return ChatCompletionDeveloperMessageParam(
                role="developer", content=_content_blocks_to_openai_content_blocks(message)
            )
        case "user":
            return ChatCompletionUserMessageParam(
                role="user", content=_content_blocks_to_openai_content_blocks(message)
            )
        case "assistant":
            if message["tool_calls"] is not None and len(message["tool_calls"]) > 0:
                tool_calls = [_tool_call_to_openai(tool_call) for tool_call in message["tool_calls"]]
                return ChatCompletionAssistantMessageParam(
                    role="assistant",
                    content=_content_blocks_to_openai_content_blocks(message),
                    tool_calls=tool_calls,
                )
            return ChatCompletionAssistantMessageParam(
                role="assistant",
                content=_content_blocks_to_openai_content_blocks(message),
            )
        case "tool":
            if message["tool_call_id"] is None:
                raise ValueError("`tool_call_id` should be specified for OpenAI.")
            res = ChatCompletionToolMessageParam(
                # content=message["error"] or _content_blocks_to_openai_content_blocks(message),
                content=message["error"] or message["content"][0]["content"],
                tool_call_id=message["tool_call_id"],
                role="tool",
                name=message["tool_call"].function,  # type: ignore -- this is actually used, and is important!
            )
            return res
        case _:
            raise ValueError(f"Invalid message type: {message}")


def _openai_to_tool_call(tool_call: ChatCompletionMessageToolCall) -> FunctionCall:
    return FunctionCall(
        function=tool_call.function.name,
        args=json.loads(tool_call.function.arguments),
        id=tool_call.id,
    )


def _assistant_message_to_content(message: ChatCompletionMessage) -> list[MessageContentBlock] | None:
    if message.content is None:
        return None
    return [text_content_block_from_string(message.content)]


def _openai_to_assistant_message(message: ChatCompletionMessage) -> ChatAssistantMessage:
    if message.tool_calls is not None:
        tool_calls = [_openai_to_tool_call(tool_call) for tool_call in message.tool_calls]
    else:
        tool_calls = None
    return ChatAssistantMessage(role="assistant", content=_assistant_message_to_content(message), tool_calls=tool_calls)


def _function_to_openai(f: Function) -> ChatCompletionToolParam:
    function_definition = FunctionDefinition(
        name=f.name,
        description=f.description,
        parameters=f.parameters.model_json_schema(),
    )
    return ChatCompletionToolParam(type="function", function=function_definition)


@retry(
    wait=wait_random_exponential(multiplier=1, max=40),
    stop=stop_after_attempt(3),
    reraise=True,
    retry=retry_if_not_exception_type((openai.BadRequestError, openai.UnprocessableEntityError)),
)
def chat_completion_request(
    client: openai.OpenAI,
    model: str,
    messages: Sequence[ChatCompletionMessageParam],
    tools: Sequence[ChatCompletionToolParam],
    reasoning_effort: ChatCompletionReasoningEffort | None,
    temperature: float | None = 1.0,
    session_id: str = None,
    params: dict = None,
):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.environ['X_Sequrity_Api_Key']}",
        "X-Api-Key": os.environ["X_Api_Key"],
        "X-Security-Features": json.dumps(
            [
                {
                    "feature_name": "Dual LLM" if params["dual_llm_mode"] else "Single LLM",
                    "config_json": json.dumps({"mode": "strict" if params["strict_mode"] else "standard"}),
                },  # or strict
                {"feature_name": "Long Program Support", "config_json": json.dumps({"mode": "base"})},
            ]
        ),
        "X-Security-Config": json.dumps(
            {
                "cache_tool_result": "all",  # "none"
                "force_to_cache": [],  # you can tell what tool calls can be cached
                "min_num_tools_for_filtering": params["min_num_tools_for_filtering"],
                "max_pllm_attempts": params["max_retry_attempts"],
                "max_n_turns": params["max_n_turns"],
                "n_plans": params["n_plans"],
                "plan_reduction": params["plan_reduction"],
                "enable_multi_step_planning": params["enable_multistep_planning"],
                "clear_history_every_n_attempts": params["clear_history_every_n_attempts"],
                "retry_on_policy_violation": params["retry_on_policy_violation"],
                "pllm_debug_info_level": params["pllm_debug_info_level"],
                "reduced_grammar_for_rllm_review": params["reduced_grammar_for_rllm_review"],
                "rllm_confidence_score_threshold": params["rllm_confidence_score_threshold"],
            }
        ),
        "X-Security-Policy": json.dumps(
            {
                "language": "sqrt",
                "fail_fast": params["fail_fast"],
                "auto_gen": params["auto_gen_policies"],
                "codes": params["tool_policies"],
                "internal_policy_preset": {
                    "default_allow": params["allow_undefined_tools"],
                    "enable_non_executable_memory": True,
                    "non_executable_memory_enforcement_level": "hard",
                },
            }
        ),
    }

    if session_id:
        headers["X-Session-ID"] = session_id

    print("--- setting session id:", session_id)

    values = {
        "model": os.environ["X_Model_Type"],
        "messages": messages,
        "tools": tools,
        "reasoning_effort": params["reasoning_effort"],
        "temperature": temperature,
    }

    url = os.environ["ENDPOINT_ADDRESS"]
    api_response = requests.post(
        url,
        json=values,
        headers=headers,
        timeout=3000,
    )

    print("Got unparsed:", api_response, ":", api_response.text)
    response = api_response.json()
    session_id = api_response.headers.get("X-Session-Id", None)

    if (response is not None) and ("usage" in response) and (response["usage"] is not None):
        session_usage = response["usage"]
        response["usage"] = {
            "prompt_tokens": session_usage["prompt_tokens"],
            "completion_tokens": session_usage["completion_tokens"],
            "total_tokens": session_usage["total_tokens"],
        }
    else:
        response["usage"] = {"prompt_tokens": -1, "completion_tokens": -1, "total_tokens": -1}
    return (ChatCompletion(**response), session_id)
    # return reponse
    # return client.chat.completions.create(
    #     model=model,
    #     messages=messages,
    #     tools=tools or NOT_GIVEN,
    #     tool_choice="auto" if tools else NOT_GIVEN,
    #     temperature=temperature or NOT_GIVEN,
    #     reasoning_effort=reasoning_effort or NOT_GIVEN,
    # )


class OpenAILLM(BasePipelineElement):
    """LLM pipeline element that uses OpenAI's API.

    Args:
        client: The OpenAI client.
        model: The model name.
        temperature: The temperature to use for generation.
    """

    def __init__(
        self,
        client: openai.OpenAI,
        model: str,
        reasoning_effort: ChatCompletionReasoningEffort | None = None,
        temperature: float | None = 1.0,
    ) -> None:
        self.client = client
        self.model = model
        self.temperature = temperature
        self.reasoning_effort: ChatCompletionReasoningEffort | None = reasoning_effort
        self.session_id = None

    def reset_session(self) -> None:
        """Reset the session ID to start a new conversation with the endpoint."""
        self.session_id = None

    def query(
        self,
        query: str,
        runtime: FunctionsRuntime,
        env: Env = EmptyEnv(),
        messages: Sequence[ChatMessage] = [],
        extra_args: dict = {},
    ) -> tuple[str, FunctionsRuntime, Env, Sequence[ChatMessage], dict]:
        openai_messages = [_message_to_openai(message, self.model) for message in messages]
        openai_tools = [_function_to_openai(tool) for tool in runtime.functions.values()]
        completion, session_id = chat_completion_request(
            self.client,
            self.model,
            openai_messages,
            openai_tools,
            self.reasoning_effort,
            self.temperature,
            self.session_id,
            defence_params,
        )
        self.session_id = session_id

        output = _openai_to_assistant_message(completion.choices[0].message)
        messages = [*messages, output]

        extra_args["usage"] = completion.usage.to_dict()

        # Reset session when conversation is complete (finish_reason = "stop")
        if completion.choices[0].finish_reason == "stop":
            self.reset_session()

        return query, runtime, env, messages, extra_args


class OpenAILLMToolFilter(BasePipelineElement):
    def __init__(self, prompt: str, client: openai.OpenAI, model: str, temperature: float | None = 0.0) -> None:
        self.prompt = prompt
        self.client = client
        self.model = model
        self.temperature = temperature

    def query(
        self,
        query: str,
        runtime: FunctionsRuntime,
        env: Env = EmptyEnv(),
        messages: Sequence[ChatMessage] = [],
        extra_args: dict = {},
    ) -> tuple[str, FunctionsRuntime, Env, Sequence[ChatMessage], dict]:
        messages = [*messages, ChatUserMessage(role="user", content=[text_content_block_from_string(self.prompt)])]
        openai_messages = [_message_to_openai(message, self.model) for message in messages]
        openai_tools = [_function_to_openai(tool) for tool in runtime.functions.values()]
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=openai_messages,
            tools=openai_tools or NOT_GIVEN,
            tool_choice="none",
            temperature=self.temperature,
        )
        output = _openai_to_assistant_message(completion.choices[0].message)

        new_tools = {}
        for tool_name, tool in runtime.functions.items():
            if output["content"] is not None and tool_name in get_text_content_as_str(output["content"]):
                new_tools[tool_name] = tool

        runtime.update_functions(new_tools)

        messages = [*messages, output]
        return query, runtime, env, messages, extra_args
