import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from tools import web_search

load_dotenv()

# Shared Groq model for the Search Agent, Writer, Critic and Revision chain.
llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0,
    max_tokens=1400,
    max_retries=2,
    timeout=60,
)


def build_search_agent():
    """Create the web-search agent."""
    return create_agent(model=llm, tools=[web_search])


writer_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are an expert research writer. Write clear, structured reports. "
        "Use only information supported by the supplied source material. "
        "If evidence is insufficient, say so rather than inventing facts."
    ),
    (
        "human",
        """Prepare a research report on this topic:

Topic: {topic}

Source material:
{sources}

Search overview:
{search_overview}

Requirements:
- Cite factual claims inline using [1], [2], etc.
- Do not invent facts, statistics, sources, or URLs.
- Keep the report focused and avoid repetition.
- Include Introduction, Key Findings (at least 3 points), Conclusion,
  and References.
- In References, list the supplied source URLs with matching numbers.
- Be informative but concise."""
    ),
])

writer_chain = writer_prompt | llm | StrOutputParser()


revise_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are an expert research writer revising a report using reviewer "
        "feedback. Stay strictly within the supplied evidence."
    ),
    (
        "human",
        """Topic: {topic}

Source material:
{sources}

Previous report:
{report}

Critic feedback:
{feedback}

Address the important issues in the feedback. Keep the sections Introduction,
Key Findings, Conclusion, and References. Preserve valid inline citations.
Do not add unsupported facts. Keep the revised report concise."""
    ),
])

revise_chain = revise_prompt | llm | StrOutputParser()


critic_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a fair and constructive research reviewer. Evaluate the report "
        "against the supplied source material. Do not claim to verify anything "
        "that is not supported by the supplied text."
    ),
    (
        "human",
        """Evaluate this research report against the source material.

Source material:
{sources}

Report:
{report}

Assess accuracy, citation use, depth, structure and clarity.
Give one overall score out of 10.

Respond in exactly this format:

Score: X/10

Strengths:
- ...
- ...

Areas to Improve:
- ...
- ...

One line verdict:
..."""
    ),
])

critic_chain = critic_prompt | llm | StrOutputParser()
