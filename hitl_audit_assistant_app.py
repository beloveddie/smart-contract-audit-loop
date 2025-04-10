
import streamlit as st
from llama_index.llms.openai import OpenAI
from llama_index.core.prompts import PromptTemplate
from llama_index.core.bridge.pydantic import BaseModel, Field
from typing import List

# --------------------
# MODEL DEFINITION
# --------------------
class AuditSegment(BaseModel):
    summary: str = Field(description="A concise explanation of what the function does.")
    risks: List[str] = Field(description="Security or logic risks.")
    suggestions: List[str] = Field(description="Fixes or improvements.")

# --------------------
# PROMPTS
# --------------------
AUDIT_TEMPLATE = """You are a smart contract auditor. Analyze the following Solidity function:

{function_code}

Return your findings in structured format:
1. Summary of what the function does,
2. List of potential vulnerabilities,
3. Suggestions for fixing issues or improving security.

Output must match the AuditSegment schema:
- summary: string
- risks: List of strings
- suggestions: List of strings
"""

FEEDBACK_PROMPT = """You previously audited this Solidity function:

{function_code}

Original Audit Output:
SUMMARY:
{old_summary}

RISKS:
{old_risks}

SUGGESTIONS:
{old_suggestions}

A human reviewer provided the following feedback:
"{human_feedback}"

Using the feedback, revise your audit and return a complete structured object like this:

{
  "summary": "...",
  "risks": ["...", "..."],
  "suggestions": ["...", "..."]
}
"""

# --------------------
# SETUP
# --------------------
st.set_page_config(page_title="Smart Contract Audit Assistant", layout="centered")
st.title("🧠 Human-in-the-Loop Smart Contract Auditing")

llm = OpenAI("gpt-4o-mini")

if "audit_segment" not in st.session_state:
    st.session_state.audit_segment = None
if "function_code" not in st.session_state:
    st.session_state.function_code = ""
if "audit_history" not in st.session_state:
    st.session_state.audit_history = []

# --------------------
# INPUT
# --------------------
st.subheader("🔐 Paste Solidity Function")
code_input = st.text_area("Enter a Solidity function to audit:", height=200)

if st.button("🚀 Run Initial Audit"):
    if not code_input.strip():
        st.warning("Please enter a Solidity function.")
    else:
        segment = llm.structured_predict(
            AuditSegment,
            PromptTemplate(AUDIT_TEMPLATE),
            function_code=code_input.strip()
        )
        st.session_state.function_code = code_input.strip()
        st.session_state.audit_segment = segment

# --------------------
# DISPLAY AUDIT OUTPUT
# --------------------
segment = st.session_state.get("audit_segment", None)
if segment:
    st.subheader("✅ AI Audit Output")
    st.markdown(f"**🧠 Summary:** {segment.summary}")
    st.markdown("**⚠️ Risks:**")
    for r in segment.risks:
        st.markdown(f"- {r}")
    st.markdown("**🔧 Suggestions:**")
    for s in segment.suggestions:
        st.markdown(f"- {s}")

    st.subheader("💬 Feedback")
    feedback = st.text_area("Optional: Give feedback to improve the audit.", key="feedback_box")

    if st.button("🔁 Regenerate with Feedback"):
        if feedback.strip():
            revised = llm.structured_predict(
                AuditSegment,
                PromptTemplate(FEEDBACK_PROMPT),
                function_code=st.session_state.function_code,
                old_summary=segment.summary,
                old_risks="\n".join(segment.risks),
                old_suggestions="\n".join(segment.suggestions),
                human_feedback=feedback.strip()
            )
            st.session_state.audit_segment = revised
            st.success("Audit regenerated with feedback.")
        else:
            st.warning("Please type your feedback before regenerating.")

    if st.button("✅ Finalize This Segment"):
        st.session_state.audit_history.append({
            "function": st.session_state.function_code,
            "summary": segment.summary,
            "risks": segment.risks,
            "suggestions": segment.suggestions
        })
        st.session_state.audit_segment = None
        st.session_state.function_code = ""
        st.success("Segment saved. You can paste another function now.")

# --------------------
# DISPLAY FINAL REPORT
# --------------------
if st.session_state.audit_history:
    st.subheader("📒 Final Audit Report")
    for idx, entry in enumerate(st.session_state.audit_history):
        st.markdown(f"### 🧩 Function {idx+1}")
        st.code(entry['function'], language="solidity")
        st.markdown(f"**🧠 Summary:** {entry['summary']}")
        st.markdown("**⚠️ Risks:**")
        for r in entry["risks"]:
            st.markdown(f"- {r}")
        st.markdown("**🔧 Suggestions:**")
        for s in entry["suggestions"]:
            st.markdown(f"- {s}")
