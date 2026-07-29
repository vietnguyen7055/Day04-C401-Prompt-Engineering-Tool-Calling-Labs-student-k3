from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from providers.base import Provider, ToolCall
from tools import TOOL_FUNCTIONS


@dataclass
class AgentRun:
    text: str | None
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_results: list[dict[str, Any]] = field(default_factory=list)


class ResearchAgent:
    def __init__(
        self,
        provider: Provider,
        *,
        system_prompt: str,
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
    ) -> None:
        self.provider = provider
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.model = model

    def run(self, user_messages: list[dict[str, str]], *, tool_choice: Any | None = None) -> AgentRun:
        messages = [{"role": "system", "content": self.system_prompt}, *user_messages]
        response = self.provider.complete(
            messages,
            self.tools,
            model=self.model,
            temperature=0.0,
            tool_choice=tool_choice,
        )
        results: list[dict[str, Any]] = []
        for call in response.tool_calls:
            func = TOOL_FUNCTIONS.get(call.name)
            if not func:
                results.append({"tool": call.name, "error": "unknown_tool"})
                continue
            try:
                result = func(**call.args)
            except Exception as exc:  # keep eval robust; failures are evidence
                result = {"error": type(exc).__name__, "message": str(exc)}
            results.append({"tool": call.name, "args": call.args, "result": result})

        # Synthesize tool results into a natural language answer
        final_text = response.text
        if response.tool_calls and results:
            messages.append({"role": "assistant", "content": None, "tool_calls": [
                {"id": f"call_{i}", "type": "function", "function": {"name": c.name, "arguments": json.dumps(c.args)}}
                for i, c in enumerate(response.tool_calls)
            ]})
            for i, r in enumerate(results):
                content = str(r.get("result", r.get("error", "")))[:3000]  # cap to avoid token overflow
                messages.append({"role": "tool", "tool_call_id": f"call_{i}", "content": content})
            try:
                synthesis = self.provider.complete(messages, tools=None, model=self.model, temperature=0.0)
                final_text = synthesis.text or final_text
            except Exception:
                pass  # synthesis is best-effort; keep original text on failure

        return AgentRun(text=final_text, tool_calls=response.tool_calls, tool_results=results)
