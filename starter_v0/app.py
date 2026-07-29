"""Streamlit UI — Research Agent Demo | Day 04 Lab"""
import os
import sys
import json
import yaml
import streamlit as st
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from env_loader import load_lab_env
from providers import make_provider
from agent import ResearchAgent
from tools import TOOL_FUNCTIONS
from versioning import file_hash

load_lab_env(Path.cwd())

st.set_page_config(page_title="Research Agent", page_icon="🔍", layout="wide")
st.title("🔍 Research Agent — Day 04 Lab")
st.caption("Prompt Engineering & Tool Calling | VinUni K3")

# Sidebar — Provider + Version
with st.sidebar:
    st.header("⚙️ Settings")
    provider_name = st.selectbox("Provider", ["deepseek", "openrouter", "openai", "anthropic", "gemini"], index=0)
    version = st.text_input("Version", "v3")
    model_override = st.text_input("Model (optional)", "", placeholder="Leave empty for default")
    temperature = st.slider("Temperature", 0.0, 1.0, 0.0, 0.1)

    st.divider()
    st.header("📊 Tools")
    st.markdown("\n".join(f"- `{t}`" for t in sorted(TOOL_FUNCTIONS.keys())))

    st.divider()
    st.header("📋 Transcripts")
    transcript_dir = Path("transcripts")
    transcript_dir.mkdir(exist_ok=True)
    existing = sorted(transcript_dir.glob("*.json"), reverse=True)
    for f in existing[:5]:
        if st.button(f"📄 {f.name}", key=f.name):
            with open(f) as fp:
                data = json.load(fp)
                st.json(data)

# Load artifacts
import yaml
artifacts = Path("artifacts")
sp_path = artifacts / "system_prompt.md"
tools_path = artifacts / "tools.yaml"
system_prompt = sp_path.read_text(encoding="utf-8")
with open(tools_path, encoding="utf-8") as f:
    tools_data = yaml.safe_load(f)
tools_list = tools_data.get("tools", []) if isinstance(tools_data, dict) else tools_data
prompt_ver = file_hash(sp_path)[:8]
tools_ver = file_hash(tools_path)[:8]

# Init provider + agent
try:
    provider = make_provider(provider_name)
    model = model_override or getattr(provider, "default_model", None)
    agent = ResearchAgent(provider, system_prompt=system_prompt, tools=tools_list, model=model)
except Exception as e:
    st.error(f"Provider error: {e}")
    st.stop()

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
if "run_count" not in st.session_state:
    st.session_state.run_count = 0

# Display chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("tool_calls"):
            with st.expander("🔧 Tool Calls", expanded=False):
                for tc in msg["tool_calls"]:
                    st.json(tc)

# Input
query = st.chat_input("Ask the research agent...")
if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            user_msgs = [{"role": m["role"], "content": m["content"]}
                         for m in st.session_state.messages if m["role"] in ("user", "assistant")]
            run = agent.run(user_msgs)

        if run.text:
            st.markdown(run.text)

        if run.tool_calls:
            st.divider()
            st.caption(f"🔧 {len(run.tool_calls)} tool call(s) — v{version} | prompt={prompt_ver[:8]} | tools={tools_ver[:8]}")
            for tc in run.tool_calls:
                with st.expander(f"🛠️ {tc.name}({json.dumps(tc.args, ensure_ascii=False)})"):
                    result = next((r for r in run.tool_results if r.get("tool") == tc.name), {})
                    col1, col2 = st.columns(2)
                    with col1:
                        st.caption("Arguments")
                        st.json(tc.args)
                    with col2:
                        st.caption("Result")
                        if result.get("error"):
                            st.error(f"{result['error']}: {result.get('message', '')}")
                        else:
                            st.json(result.get("result", {}))

        assistant_msg = {"role": "assistant", "content": run.text or ""}
        if run.tool_calls:
            assistant_msg["tool_calls"] = [
                {"name": tc.name, "args": tc.args} for tc in run.tool_calls
            ]
        st.session_state.messages.append(assistant_msg)

        # Save transcript
        st.session_state.run_count += 1
        transcript = {
            "version": version,
            "provider": provider_name,
            "model": model,
            "prompt_hash": prompt_ver,
            "tools_hash": tools_ver,
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "text": run.text,
            "tool_calls": [{"name": tc.name, "args": tc.args} for tc in run.tool_calls],
            "tool_results": run.tool_results,
        }
        ts_file = transcript_dir / f"{datetime.now():%Y%m%d_%H%M%S}_{st.session_state.run_count:03d}.json"
        with open(ts_file, "w", encoding="utf-8") as fp:
            json.dump(transcript, fp, ensure_ascii=False, indent=2, default=str)
