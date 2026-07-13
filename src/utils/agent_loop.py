import logging
from typing import Any, Dict, List

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)


def message_content_to_text(content: Any) -> str:
    """
    Normalize LLM message content to a plain string.

    Gemini (and some other providers) return content as a list of blocks, e.g.
    [{'type': 'text', 'text': '...', 'extras': {'signature': '...'}}].
    Stringifying that list breaks JSON extraction and prints noise in the CLI.
    """
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: List[str] = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict):
                if part.get("type") == "tool_use":
                    continue
                if "text" in part:
                    parts.append(str(part["text"]))
            else:
                text = getattr(part, "text", None)
                if text is not None:
                    parts.append(str(text))
        if parts:
            return "\n".join(parts)
    return str(content)


def extract_gemini_calls(response: Any) -> List[Dict[str, Any]]:
    """
    Normalize Gemini tool calls from either response.tool_calls or
    response.content parts with type == "tool_use".

    Standard LangChain expects tool_calls; Gemini sometimes puts them only
    in content as raw JSON parts — if we only check tool_calls, tools fail silently.
    """
    if getattr(response, "tool_calls", None):
        return [
            {
                "id": tc.get("id") if isinstance(tc, dict) else getattr(tc, "id", ""),
                "name": tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", ""),
                "args": tc.get("args") if isinstance(tc, dict) else getattr(tc, "args", {}),
            }
            for tc in response.tool_calls
        ]

    content = getattr(response, "content", None)
    if isinstance(content, list):
        return [
            {
                "id": part.get("id", ""),
                "name": part.get("name", ""),
                "args": part.get("input") or part.get("args") or {},
            }
            for part in content
            if isinstance(part, dict) and part.get("type") == "tool_use" and part.get("name")
        ]

    return []


async def run_agent_loop(
    model: BaseChatModel,
    tools: List[BaseTool],
    messages: List[BaseMessage],
    max_iter: int = 6,
    agent_name: str = "agent",
) -> str:
    """
    Think → Act → Observe ReAct loop.
    Looks up each tool by name (not tools[0]) and uses each call's own id
    for ToolMessage, whether the call came from tool_calls or content.

    agent_name identifies the caller in logs when debugging the loop.
    """
    tools_by_name = {t.name: t for t in tools}
    model_with_tools = model.bind_tools(tools)

    for iteration in range(1, max_iter + 1):
        response = await model_with_tools.ainvoke(messages)
        tool_calls = extract_gemini_calls(response)
        messages.append(response)

        if not tool_calls:
            return message_content_to_text(response.content)

        for call in tool_calls:
            tool = tools_by_name.get(call["name"])
            if tool is None:
                result = f"Unknown tool: {call['name']}"
                logger.warning("Unknown tool requested: %s", call["name"])
            else:
                result = await tool.ainvoke(call["args"])
            messages.append(
                ToolMessage(content=str(result), tool_call_id=call["id"] or call["name"])
            )

    messages.append(
        HumanMessage(
            "Maximum iterations reached. Provide your best final answer "
            "based on the information gathered so far. Do not call any tools."
        )
    )
    final_response = await model_with_tools.ainvoke(messages)
    return message_content_to_text(final_response.content)
