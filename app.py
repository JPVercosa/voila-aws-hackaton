import os
import streamlit as st
from agents.Orchestrator import OrchestratorAgent
from dotenv import load_dotenv
from strands.telemetry import StrandsTelemetry

# Load environment variables
load_dotenv()

class StrandsTelemetryExtension(StrandsTelemetry):
    def __init__(self):
        super().__init__()
        self.actual_tool = None

    def set_actual_tool(self, tool_name: str):
        """Set the current tool being used for telemetry."""
        self.actual_tool = tool_name

    


# Retrieve environment variables
KNOWLEDGE_BASE_ID = os.getenv("KNOWLEDGE_BASE_ID", "default_kb_id")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Initialize the OrchestratorAgent
orchestrator_agent = OrchestratorAgent()

# Streamlit app layout
st.set_page_config(page_title="AWS Hackaton Solution", layout="centered")
st.title("🧠 Orchestrator Agent Chat Interface")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("Ask a question..."):
    # Display user message
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Call the OrchestratorAgent
    with st.spinner("Thinking..."):
        try:
            response = orchestrator_agent(prompt, KNOWLEDGE_BASE_ID, AWS_REGION)
            print(response)
            response_text = str(response)
        except Exception as e:
            response_text = f"❌ Error: {str(e)}"

    # Display assistant response
    st.chat_message("assistant").markdown(response_text)
    st.session_state.messages.append({"role": "assistant", "content": response_text})

