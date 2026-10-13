
from langchain.agents import create_agent
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from tools import web_search, scrape_url
from dotenv import load_dotenv
import os

load_dotenv()

# Groq LLM
llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0,
    max_retries=2,
)


def build_search_agent():
    return create_agent(model=llm, tools=[web_search])


def build_reader_agent():
    return create_agent(model=llm, tools=[scrape_url])


writer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research writer. Write clear, structured and insightful reports. "
               "Only use facts supported by the numbered sources provided."),
    ("human", """Write a detailed research report on the topic below.

Topic: {topic}

Numbered Sources:
{sources}

Search Overview:
{search_overview}

Rules:
- Cite sources inline using [1], [2], etc. after every factual claim.
- Do not invent sources or facts that are not in the material above.

Structure the report as:
- Introduction
- Key Findings (minimum 3 well-explained points, each with citations)
- Conclusion
- References (list each source as: [n] URL)

Be detailed, factual and professional."""),
])

writer_chain = writer_prompt | llm | StrOutputParser()


revise_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research writer revising a report based on reviewer feedback."),
    ("human", """Topic: {topic}

Numbered Sources:
{sources}

Previous Report:
{report}

Critic Feedback:
{feedback}

Rewrite the report so it fixes every point under 'Areas to Improve'.
Keep inline citations [n] and the same structure
(Introduction, Key Findings, Conclusion, References).
Do not add facts that are not in the sources."""),
])

revise_chain = revise_prompt | llm | StrOutputParser()


critic_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a sharp, fair and constructive research critic. "
               "Judge the report against the provided sources."),
    ("human", """Evaluate the research report below using the source material.

Sources:
{sources}

Report:
{report}

Score each criterion from 1 to 10 (5 = acceptable, 7 = good, 9 = excellent):
- Accuracy: are claims supported by the sources?
- Citation use: are [n] citations present and correct?
- Depth: are the findings explained, not just listed?
- Structure and clarity

Respond in this exact format:

Score: X/10

Strengths:
- ...
- ...

Areas to Improve:
- ...
- ...

One line verdict:
..."""),
])

critic_chain = critic_prompt | llm | StrOutputParser()
