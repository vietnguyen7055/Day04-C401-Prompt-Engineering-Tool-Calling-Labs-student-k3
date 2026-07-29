"""Streamlit UI for the Day 04 Research Agent."""
from __future__ import annotations

import html
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
TRANSCRIPTS_DIR = ROOT / "transcripts"
PROVIDERS = ["deepseek", "openrouter", "openai", "anthropic", "gemini"]

sys.path.insert(0, str(ROOT))

from chat import run_model_tool_loop, safe_slug, trim_history, write_transcript
from env_loader import load_lab_env
from providers import make_provider
from tools import TOOL_FUNCTIONS, load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version


load_lab_env(ROOT)


def apply_codex_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #101113;
            --panel: #17191d;
            --panel-strong: #1e2126;
            --line: #2b2f36;
            --line-soft: #23262c;
            --text: #f3f4f6;
            --muted: #a1a7b3;
            --subtle: #737985;
            --accent: #71e2a3;
            --warn: #f4b86a;
            --danger: #ff7b7b;
        }

        .stApp {
            background: var(--bg);
            color: var(--text);
        }

        header[data-testid="stHeader"] {
            background: rgba(16, 17, 19, 0.86);
            backdrop-filter: blur(18px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.04);
        }

        [data-testid="stSidebar"] {
            background: #131417;
            border-right: 1px solid var(--line-soft);
        }

        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            letter-spacing: 0;
        }

        .block-container {
            max-width: 1120px;
            padding-top: 1.35rem;
            padding-bottom: 7rem;
        }

        .codex-top {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 24px;
            padding: 14px 0 18px;
            border-bottom: 1px solid var(--line-soft);
            margin-bottom: 18px;
        }

        .codex-title {
            margin: 0;
            color: var(--text);
            font-size: 1.35rem;
            font-weight: 650;
            letter-spacing: 0;
        }

        .codex-subtitle {
            margin: 4px 0 0;
            color: var(--muted);
            font-size: 0.92rem;
        }

        .run-pills {
            display: flex;
            flex-wrap: wrap;
            justify-content: flex-end;
            gap: 8px;
            max-width: 620px;
        }

        .run-pill {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            min-height: 30px;
            padding: 5px 10px;
            border: 1px solid var(--line);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.025);
            color: var(--text);
            font-size: 0.8rem;
            white-space: nowrap;
        }

        .run-pill span {
            color: var(--subtle);
        }

        .empty-panel {
            display: grid;
            gap: 14px;
            margin: 72px auto 48px;
            max-width: 720px;
            text-align: center;
        }

        .empty-title {
            font-size: 1.3rem;
            font-weight: 650;
            color: var(--text);
        }

        .empty-copy {
            color: var(--muted);
            font-size: 0.96rem;
        }

        .trace-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin: 12px 0 2px;
        }

        .trace-chip {
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 4px 8px;
            color: var(--muted);
            background: rgba(255, 255, 255, 0.018);
            font-size: 0.78rem;
        }

        .trace-chip strong {
            color: var(--text);
            font-weight: 600;
        }

        .tool-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 7px;
            margin: 6px 0 2px;
        }

        .tool-token {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            border: 1px solid var(--line-soft);
            border-radius: 8px;
            padding: 6px 8px;
            background: rgba(255, 255, 255, 0.02);
            color: var(--muted);
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            font-size: 0.78rem;
        }

        div[data-testid="stChatMessage"] {
            border: 1px solid var(--line-soft);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.018);
            padding: 0.85rem 1rem;
            margin-bottom: 0.75rem;
        }

        div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
            background: rgba(255, 255, 255, 0.035);
        }

        [data-testid="stChatMessageContent"] p,
        [data-testid="stChatMessageContent"] li {
            line-height: 1.58;
        }

        div[data-testid="stExpander"] {
            border-color: var(--line-soft);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.012);
        }

        .stButton > button,
        .stDownloadButton > button {
            border-radius: 8px;
            border: 1px solid var(--line);
            background: var(--panel);
            color: var(--text);
            min-height: 38px;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover {
            border-color: var(--accent);
            color: var(--text);
        }

        .stTextInput input,
        .stNumberInput input,
        .stSelectbox [data-baseweb="select"] > div {
            background: var(--panel);
            border-color: var(--line);
            color: var(--text);
            border-radius: 8px;
        }

        .stSlider [data-baseweb="slider"] div {
            border-radius: 999px;
        }

        code {
            color: #d7f8e3;
            background: rgba(113, 226, 163, 0.08);
            border: 1px solid rgba(113, 226, 163, 0.18);
            border-radius: 6px;
            padding: 0.1rem 0.25rem;
        }

        @media (max-width: 760px) {
            .codex-top {
                display: block;
            }

            .run-pills {
                justify-content: flex-start;
                margin-top: 14px;
            }

            .tool-grid {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def escape(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def init_session_state() -> None:
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("run_count", 0)
    st.session_state.setdefault("last_transcript", None)
    st.session_state.setdefault("pending_prompt", None)


def load_artifacts(version: str) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]], Any]:
    system_prompt_path = ARTIFACTS_DIR / "system_prompt.md"
    tools_path = ARTIFACTS_DIR / "tools.yaml"
    system_prompt = system_prompt_path.read_text(encoding="utf-8")
    declarations = load_tool_declarations(tools_path)
    openai_tools = to_openai_tools(declarations)
    artifact_version = build_artifact_version(version, system_prompt_path, tools_path)
    return system_prompt, declarations, openai_tools, artifact_version


def render_header(*, provider_name: str, model: str | None, artifact_version: Any, tool_count: int) -> None:
    artifact = artifact_version.artifact_version
    pills = [
        ("provider", provider_name),
        ("model", model or "default"),
        ("version", artifact_version.version),
        ("tools", tool_count),
        ("artifact", artifact if len(artifact) <= 42 else f"{artifact[:39]}..."),
    ]
    pill_html = "".join(
        f'<div class="run-pill"><span>{escape(label)}</span>{escape(value)}</div>'
        for label, value in pills
    )
    st.markdown(
        f"""
        <div class="codex-top">
            <div>
                <h1 class="codex-title">Research Agent</h1>
                <p class="codex-subtitle">Codex-style chat with transparent tool execution.</p>
            </div>
            <div class="run-pills">{pill_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state() -> None:
    st.markdown(
        """
        <div class="empty-panel">
            <div class="empty-title">Start a research run</div>
            <div class="empty-copy">Ask a direct question, request a source digest, or test a tool boundary.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_tool_catalog() -> None:
    tokens = "".join(
        f'<div class="tool-token">{escape(name)}</div>' for name in sorted(TOOL_FUNCTIONS)
    )
    st.markdown(f'<div class="tool-grid">{tokens}</div>', unsafe_allow_html=True)


def render_trace_summary(result: dict[str, Any], artifact: str | None = None) -> None:
    tool_events = result.get("tool_events", [])
    rounds = result.get("rounds", [])
    chips = [
        ("status", result.get("status", "unknown")),
        ("rounds", len(rounds)),
        ("tool calls", len(tool_events)),
    ]
    if artifact:
        chips.append(("artifact", artifact))

    chip_html = "".join(
        f'<span class="trace-chip">{escape(label)} <strong>{escape(value)}</strong></span>'
        for label, value in chips
    )
    st.markdown(f'<div class="trace-meta">{chip_html}</div>', unsafe_allow_html=True)

    if not tool_events and not rounds:
        return

    with st.expander("Execution trace", expanded=False):
        if rounds:
            for round_item in rounds:
                round_number = round_item.get("round", "?")
                status = "tool calls" if round_item.get("tool_calls") else "answer"
                st.markdown(f"**Round {round_number} - {status}**")
                assistant_text = round_item.get("assistant_text")
                if assistant_text:
                    st.markdown(assistant_text)
                for call in round_item.get("tool_calls", []):
                    st.code(
                        f"{call.get('name', 'tool')}({json.dumps(call.get('args', {}), ensure_ascii=False)})",
                        language="text",
                    )

        if tool_events:
            st.divider()
            for index, event in enumerate(tool_events, start=1):
                tool_name = event.get("tool", "tool")
                result_body = event.get("result", {})
                is_error = isinstance(result_body, dict) and result_body.get("error")
                label = f"{index}. {tool_name} - {'error' if is_error else 'ok'}"
                with st.expander(label, expanded=False):
                    args_col, result_col = st.columns(2)
                    with args_col:
                        st.caption("Arguments")
                        st.json(event.get("args", {}))
                    with result_col:
                        st.caption("Result")
                        if is_error:
                            st.error(f"{result_body.get('error')}: {result_body.get('message', '')}")
                        else:
                            st.json(result_body)


def render_chat_messages() -> None:
    for message in st.session_state.messages:
        role = message.get("role", "assistant")
        with st.chat_message(role):
            st.markdown(message.get("content") or "")
            if role == "assistant" and message.get("run"):
                render_trace_summary(
                    message["run"],
                    artifact=message.get("artifact_version"),
                )


def build_messages_for_agent(system_prompt: str, history_window: int) -> list[dict[str, str]]:
    history = [
        {"role": message["role"], "content": message.get("content", "")}
        for message in st.session_state.messages
        if message.get("role") in {"user", "assistant"}
    ]
    return [
        {"role": "system", "content": system_prompt},
        *trim_history(history, history_window),
    ]


def save_transcript(
    *,
    version: Any,
    provider_name: str,
    model: str | None,
    history_window: int,
    max_tool_rounds: int,
    query: str,
    result: dict[str, Any],
) -> Path:
    st.session_state.run_count += 1
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = "_".join(
        [
            safe_slug(version.version),
            safe_slug(provider_name),
            timestamp,
        ]
    )
    transcript_path = TRANSCRIPTS_DIR / f"{transcript_id}.transcript.json"
    chat_history = [
        {"role": message.get("role"), "content": message.get("content")}
        for message in st.session_state.messages
    ]
    transcript = {
        "transcript_id": transcript_id,
        **artifact_version_dict(version),
        "provider": provider_name,
        "model": model,
        "system_prompt": str(ARTIFACTS_DIR / "system_prompt.md"),
        "tools": str(ARTIFACTS_DIR / "tools.yaml"),
        "history_window": history_window,
        "max_tool_rounds": max_tool_rounds,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "query": query,
        "assistant_text": result.get("assistant_text", ""),
        "status": result.get("status"),
        "rounds": result.get("rounds", []),
        "tool_events": result.get("tool_events", []),
        "chat_history": chat_history,
    }
    write_transcript(transcript_path, transcript)
    return transcript_path


def render_transcripts_panel() -> None:
    TRANSCRIPTS_DIR.mkdir(exist_ok=True)
    transcript_paths = sorted(
        TRANSCRIPTS_DIR.glob("*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    if not transcript_paths:
        st.caption("No transcripts yet.")
        return

    selected_name = st.selectbox(
        "Open transcript",
        ["None", *[path.name for path in transcript_paths[:12]]],
        label_visibility="collapsed",
    )
    if selected_name == "None":
        return

    selected_path = next(path for path in transcript_paths if path.name == selected_name)
    transcript_text = selected_path.read_text(encoding="utf-8")
    st.download_button(
        "Download JSON",
        data=transcript_text,
        file_name=selected_path.name,
        mime="application/json",
        use_container_width=True,
    )
    with st.expander("Preview", expanded=False):
        st.json(json.loads(transcript_text))


def render_sidebar() -> tuple[str, str, str | None, int, int]:
    with st.sidebar:
        st.markdown("## Agent")
        provider_name = st.selectbox("Provider", PROVIDERS, index=0)
        version = st.text_input("Version", value="v3")
        model_override = st.text_input(
            "Model",
            value="",
            placeholder="Provider default",
        ).strip()

        st.markdown("## Run")
        history_window = st.slider("History pairs", min_value=1, max_value=10, value=5)
        max_tool_rounds = st.slider("Tool rounds", min_value=1, max_value=8, value=4)

        clear_col, sample_col = st.columns(2)
        with clear_col:
            if st.button("Clear", use_container_width=True):
                st.session_state.messages = []
                st.session_state.run_count = 0
                st.session_state.last_transcript = None
                st.rerun()
        with sample_col:
            if st.button("Sample", use_container_width=True):
                st.session_state.pending_prompt = (
                    "Find today's AI policy news, cite sources, and format a short briefing."
                )
                st.rerun()

        st.divider()
        st.markdown("## Tools")
        st.caption(f"{len(TOOL_FUNCTIONS)} local tools")
        render_tool_catalog()

        st.divider()
        st.markdown("## Transcripts")
        last_transcript = st.session_state.get("last_transcript")
        if last_transcript:
            st.caption(f"Latest: {Path(last_transcript).name}")
        render_transcripts_panel()

    return provider_name, version.strip() or "v3", model_override or None, history_window, max_tool_rounds


def main() -> None:
    st.set_page_config(page_title="Research Agent", page_icon="R", layout="wide")
    apply_codex_theme()
    init_session_state()

    provider_name, version, model_override, history_window, max_tool_rounds = render_sidebar()

    try:
        system_prompt, tool_declarations, openai_tools, artifact_version = load_artifacts(version)
        provider = make_provider(provider_name)
        model = model_override or getattr(provider, "default_model", None)
    except Exception as exc:
        st.error(f"Configuration error: {type(exc).__name__}: {exc}")
        st.stop()

    render_header(
        provider_name=provider_name,
        model=model,
        artifact_version=artifact_version,
        tool_count=len(tool_declarations),
    )

    if not st.session_state.messages:
        render_empty_state()

    render_chat_messages()

    prompt = st.session_state.pop("pending_prompt", None) or st.chat_input("Message Research Agent")
    if not prompt:
        return

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Running agent..."):
            try:
                result = run_model_tool_loop(
                    provider=provider,
                    messages=build_messages_for_agent(system_prompt, history_window),
                    tools=openai_tools,
                    model=model,
                    max_tool_rounds=max_tool_rounds,
                )
            except Exception as exc:
                error_text = f"Provider error: {type(exc).__name__}: {exc}"
                result = {
                    "status": "provider_error",
                    "assistant_text": error_text,
                    "rounds": [],
                    "tool_events": [],
                }

        assistant_text = result.get("assistant_text") or ""
        if result.get("status") == "provider_error":
            st.error(assistant_text)
        else:
            st.markdown(assistant_text)
        render_trace_summary(result, artifact=artifact_version.artifact_version)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": assistant_text,
            "run": result,
            "artifact_version": artifact_version.artifact_version,
        }
    )
    transcript_path = save_transcript(
        version=artifact_version,
        provider_name=provider_name,
        model=model,
        history_window=history_window,
        max_tool_rounds=max_tool_rounds,
        query=prompt,
        result=result,
    )
    st.session_state.last_transcript = str(transcript_path)


if __name__ == "__main__":
    main()
