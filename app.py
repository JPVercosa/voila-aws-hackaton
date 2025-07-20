import os, threading
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from dotenv import load_dotenv
from agents.Orchestrator import OrchestratorAgent
from memory.AgentsMemory import memory
from streamlit.runtime.scriptrunner import add_script_run_ctx   # 👈 silences the warning
import graphviz as gv

# ───────── env / agent init
load_dotenv()
orchestrator_agent = OrchestratorAgent()

# ───────── session defaults
defaults = {
    "messages":      [],
    "runner":        None,        # Thread obj
    "answer":        None,        # str
    "pending":       None,        # str
    "dots":          0            # spinner index
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

# ───────── layout
st.set_page_config(page_title="AWS Hackathon Solution", layout="wide")
st.title("🧠 Orchestrator Agent Chat Interface")
col_chat, col_monitor = st.columns([2, 1])

# ───────── user input
prompt = st.chat_input("Ask a question…")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.pending = prompt
    st.session_state.answer  = None            # clear previous answer

# ───────── background worker
def worker(user_prompt):
    try:
        resp = orchestrator_agent(user_prompt)
        st.session_state.answer = str(resp)
    except Exception as e:
        st.session_state.answer = f"❌ Error: {e}"
    finally:
        st.session_state.runner = None         # mark done

# launch once when pending
if st.session_state.pending and st.session_state.runner is None:
    t = threading.Thread(target=worker, args=(st.session_state.pending,), daemon=True)
    add_script_run_ctx(t)                      # 👈 attach Streamlit ctx
    t.start()
    st.session_state.runner  = t
    st.session_state.pending = None            # consumed

# ───────── LEFT column: chat + placeholder
with col_chat:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    # dedicated slot that will flip from “Thinking…” to answer
    placeholder = st.empty()

    # 1) show dots while thread alive
    if st.session_state.runner and st.session_state.answer is None:
        dots = "." * (st.session_state.dots % 4)
        st.session_state.dots += 1
        with placeholder.container():
            st.chat_message("assistant").markdown(f"Thinking{dots}")

    # 2) once answer ready → render & store in history (just once)
    if st.session_state.answer is not None:
        with placeholder.container():
            st.chat_message("assistant").markdown(st.session_state.answer)

        st.session_state.messages.append(
            {"role": "assistant", "content": st.session_state.answer}
        )

        st.session_state.answer = None         # clear so it won’t re-add

# ───────── RIGHT column: live monitor
with col_monitor:
    import graphviz as gv          # ← add once at the top of the file

    st.subheader("🛠️ Agent Monitor")

    # current status (exactly as before)
    current_agent = memory.get("actual_agent") or "N/A"
    current_tool  = memory.get("actual_tool")  or "N/A"
    st.markdown(f"**Current Tool:** `{current_tool}`")

    # ───── Graphviz diagram (auto-highlights active agent) ─────
    dot = gv.Digraph(engine="dot")

    # helper to style the active node
    def add_node(name: str):
        if name == current_agent:
            dot.node(name,
                     shape="ellipse",
                     style="filled,bold",
                     fillcolor="#4FC3F7")           # light-blue highlight
        else:
            dot.node(name, shape="ellipse")

    # nodes
    add_node("Orchestrator")
    add_node("Ingestion")
    add_node("Validator")
    add_node("Creator")
    for sub in ["Markdown", "Splitter", "Clauses"]:
        add_node(sub)

    # edges (same structure as your sketch)
    dot.edges(
        [
            ("Orchestrator", "Ingestion"),
            ("Orchestrator", "Validator"),
            ("Orchestrator", "Creator"),
            ("Ingestion", "Markdown"),
            ("Ingestion", "Splitter"),
            ("Ingestion", "Clauses"),
        ]
    )

    # render in Streamlit (auto-refresh already handled by st_autorefresh)
    st.graphviz_chart(dot, use_container_width=True)

# ───────── auto-refresh every 700 ms
st_autorefresh(interval=700, limit=None, key="live_refresh")
