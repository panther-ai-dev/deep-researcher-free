import streamlit as st
from agents import DeepResearcherAgent
import time
import re

st.set_page_config(
    page_title="Deep Research Agent",
    page_icon="🔎",
)

title_html = """
<div style="display: flex; justify-content: center; align-items: center; width: 100%; padding: 32px 0 24px 0;">
    <h1 style="margin: 0; padding: 0; font-size: 2.5rem; font-weight: bold;">
        <span style="font-size:2.5rem;">🔎</span> Agentic Deep Searcher with
        <span style="color: #fb542c;">Agno</span> +
        <span style="color: #f55036;">Groq</span> +
        <span style="color: #de5833;">DuckDuckGo</span>
    </h1>
</div>
"""
st.markdown(title_html, unsafe_allow_html=True)

with st.sidebar:
    st.header("Free stack")
    st.markdown(
        """
    - **Model**: Groq (free tier)
    - **Search**: DuckDuckGo (no API key)
    - **Framework**: Agno
    """
    )
    st.divider()

    st.header("About")
    st.markdown(
        """
    This application is powered by a `DeepResearcherAgent` which leverages multiple AI agents for a comprehensive research process:
    - **Searcher**: Finds and extracts information from the web.
    - **Analyst**: Synthesizes and interprets the research findings.
    - **Writer**: Produces a final, polished report.
    """
    )
    st.markdown("---")
    st.markdown(
        "Based on [awesome-ai-apps](https://github.com/Arindam200/awesome-ai-apps) by Arindam Majumder"
    )

# Chat input at the bottom
user_input = st.chat_input("What should I research?")

if user_input:
    try:
        agent = DeepResearcherAgent()
        with st.status("Executing research plan...", expanded=True) as status:
            # PHASE 1: Researching
            phase1_msg = "🧠 **Phase 1: Researching** - Finding and extracting relevant information from the web..."
            status.write(phase1_msg)
            research_content = agent.searcher.run(user_input)

            # PHASE 2: Analyzing
            phase2_msg = "🔬 **Phase 2: Analyzing** - Synthesizing and interpreting the research findings..."
            status.write(phase2_msg)
            analysis = agent.analyst.run(research_content.content)

            # PHASE 3: Writing Report
            phase3_msg = (
                "✍️ **Phase 3: Writing Report** - Producing a final, polished report..."
            )
            status.write(phase3_msg)
            report_iterator = agent.writer.run(analysis.content, stream=True)

        # Move report display outside of status block
        full_report = ""
        report_container = st.empty()
        for chunk in report_iterator:
            if chunk.content:
                full_report += chunk.content
                cleaned_report = re.sub(r"^```(?:[a-zA-Z]*)?\n?", "", full_report)
                cleaned_report = re.sub(r"\n?```$", "", cleaned_report)
                report_container.markdown(cleaned_report, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"An error occurred: {e}")
