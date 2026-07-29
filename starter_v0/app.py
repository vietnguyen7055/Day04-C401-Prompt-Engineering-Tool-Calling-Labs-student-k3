"""Streamlit UI — Research Agent | Day 04 Lab"""
import sys, json, yaml
from pathlib import Path
from datetime import datetime
import streamlit as st

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
from env_loader import load_lab_env
from providers import make_provider
from agent import ResearchAgent

load_lab_env(ROOT)

st.set_page_config(page_title="Research Agent", page_icon="🔍")
st.title("🔍 Research Agent — Day 04 Lab")

with st.sidebar:
    provider_name = st.selectbox("Provider", ["deepseek", "openrouter", "openai"], index=0)
    provider = make_provider(provider_name)
    model = getattr(provider, "default_model", None)
    st.caption(f"Model: {model}")
    tools_src = yaml.safe_load((ROOT / "artifacts/tools.yaml").read_text(encoding="utf-8"))
    tools_list = tools_src if isinstance(tools_src, list) else tools_src.get("tools", [])
    openai_tools = [{"type": "function", "function": t} for t in tools_list]
    st.caption(f"Tools: {len(openai_tools)} loaded")
    system_prompt = (ROOT / "artifacts/system_prompt.md").read_text(encoding="utf-8")
    agent = ResearchAgent(provider, system_prompt=system_prompt, tools=openai_tools, model=model)

if "msgs" not in st.session_state:
    st.session_state.msgs = []

for m in st.session_state.msgs:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

q = st.chat_input("Ask...")
if q:
    st.session_state.msgs.append({"role": "user", "content": q})
    with st.chat_message("user"):
        st.markdown(q)
    with st.chat_message("assistant"):
        with st.spinner("..."):
            run = agent.run(st.session_state.msgs)
        if run.text:
            st.markdown(run.text)
        if run.tool_calls:
            for tc, tr in zip(run.tool_calls, run.tool_results):
                with st.expander(f"🛠️ {tc.name}({json.dumps(tc.args, ensure_ascii=False)})"):
                    st.json(tr.get("result", tr.get("error", "unknown")))
        st.session_state.msgs.append({"role": "assistant", "content": run.text or "(no text)"})
