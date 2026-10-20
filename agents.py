import os
from agno.agent import Agent
from agno.models.groq import Groq
from dotenv import load_dotenv
from typing import Iterator
from agno.utils.log import logger
from agno.utils.pprint import pprint_run_response
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.newspaper4k import Newspaper4kTools


class ShortReader(Newspaper4kTools):
    """Newspaper4k reader that trims articles so free-tier token limits are not blown."""

    def read_article(self, url: str) -> str:
        """Read an article from a URL and return its first ~3000 characters."""
        return super().read_article(url)[:3000]
from agno.workflow import RunEvent, RunResponse, Workflow
from pydantic import BaseModel, Field

load_dotenv()

PROVIDER = os.getenv("PROVIDER", "groq")
MODEL_ID = os.getenv("MODEL_ID", "openai/gpt-oss-120b" if PROVIDER == "groq" else "mistral-small-latest")


def make_model():
    if PROVIDER == "groq":
        return Groq(id=MODEL_ID, api_key=os.getenv("GROQ_API_KEY"))
    from agno.models.mistral import MistralChat  # optional: pip install mistralai<2

    return MistralChat(id=MODEL_ID, api_key=os.getenv("MISTRAL_API_KEY"))


class DeepResearcherAgent(Workflow):
    """
    A multi-stage research workflow that:
    1. Gathers information from the web using advanced scraping tools.
    2. Analyzes and synthesizes the findings.
    3. Produces a clear, well-structured report.
    """

    # Searcher: Finds and extracts relevant information from the web
    searcher: Agent = Agent(
        tools=[DuckDuckGoTools(fixed_max_results=5), ShortReader()],
        model=make_model(),
        retries=8,
        delay_between_retries=3,
        exponential_backoff=True,
        show_tool_calls=True,
        markdown=True,
        description=(
            "You are ResearchBot-X, an expert at finding and extracting high-quality, "
            "up-to-date information from the web. Your job is to gather comprehensive, "
            "reliable, and diverse sources on the given topic."
        ),
        instructions=(
            "1. Search for the most recent and authoritative and up-to-date sources (news, blogs, official docs, research papers, forums, etc.) on the topic.\n"
            "2. Extract key facts, statistics, and expert opinions.\n"
            "3. Cover multiple perspectives and highlight any disagreements or controversies.\n"
            "4. Include relevant statistics, data, and expert opinions where possible.\n"
            "5. Organize your findings in a clear, structured format (e.g., markdown table or sections by source type).\n"
            "6. If the topic is ambiguous, clarify with the user before proceeding.\n"
            "7. Use at most 4 tool calls in total, then write your findings and ALWAYS finish with a written answer. Keep it under 600 words.\n"
            "8. Mention the References & Sources of the Content. (It's Must)"
        ),
    )

    # Analyst: Synthesizes and interprets the research findings
    analyst: Agent = Agent(
        model=make_model(),
        retries=8,
        delay_between_retries=3,
        exponential_backoff=True,
        markdown=True,
        description=(
            "You are AnalystBot-X, a critical thinker who synthesizes research findings "
            "into actionable insights. Your job is to analyze, compare, and interpret the "
            "information provided by the researcher."
        ),
        instructions=(
            "1. Identify key themes, trends, and contradictions in the research.\n"
            "2. Highlight the most important findings and their implications.\n"
            "3. Suggest areas for further investigation if gaps are found.\n"
            "4. Present your analysis in a structured, easy-to-read format.\n"
            "5. Extract and list ONLY the reference links or sources that were ACTUALLY found and provided by the researcher in their findings. Do NOT create, invent, or hallucinate any links.\n"
            "6. If no links were provided by the researcher, do not include a References section.\n"
            "7. Don't add hallucinations or make up information. Use ONLY the links that were explicitly passed to you by the researcher.\n"
            "8. Verify that each link you include was actually present in the researcher's findings before listing it.\n"
            "9. If there's no Link found from the previous agent then just say, No reference Found."
        ),
    )

    # Writer: Produces a final, polished report
    writer: Agent = Agent(
        model=make_model(),
        retries=8,
        delay_between_retries=3,
        exponential_backoff=True,
        markdown=True,
        description=(
            "You are WriterBot-X, a professional technical writer. Your job is to craft "
            "a clear, engaging, and well-structured report based on the analyst's summary."
        ),
        instructions=(
            "1. Write an engaging introduction that sets the context.\n"
            "2. Organize the main findings into logical sections with headings.\n"
            "3. Use bullet points, tables, or lists for clarity where appropriate.\n"
            "4. Conclude with a summary and actionable recommendations.\n"
            "5. Include a References & Sources section ONLY if the analyst provided actual links from their analysis.\n"
            "6. Use ONLY the reference links that were explicitly provided by the analyst in their analysis. Do NOT create, invent, or hallucinate any links.\n"
            "7. If the analyst provided links, format them as clickable markdown links in the References section.\n"
            "8. If no links were provided by the analyst, do not include a References section at all.\n"
            "9. Never add fake or made-up links - only use links that were actually found and passed through the research chain."
        ),
    )

    def run(self, topic: str) -> Iterator[RunResponse]:
        """
        Orchestrates the research, analysis, and report writing process for a given topic.
        """
        logger.info(f"Running deep researcher agent for topic: {topic}")

        # Step 1: Research
        research_content = self.searcher.run(topic)
        if not research_content.content:
            raise RuntimeError("Searcher returned nothing")
        # logger.info(f"Searcher content: {research_content.content}")

        logger.info("Analysis started")
        # Step 2: Analysis
        analysis = self.analyst.run(research_content.content)
        if not analysis.content:
            raise RuntimeError("Analyst returned nothing")
        # logger.info(f"Analyst analysis: {analysis.content}")

        logger.info("Report Writing Started")
        # Step 3: Report Writing
        report = self.writer.run(analysis.content, stream=True)
        yield from report


def run_research(query: str) -> str:
    agent = DeepResearcherAgent()
    final_report_iterator = agent.run(
        topic=query,
    )
    logger.info("Report Generated")

    # Collect all streaming content into a single string
    full_report = ""
    for chunk in final_report_iterator:
        if chunk.content:
            full_report += chunk.content

    return full_report


if __name__ == "__main__":
    topic = "Best free AI tools for college students in India in 2026"
    response = run_research(topic)
    print(response)
