# Research.AI — Multi-Agent Research Assistant

An AI-powered research assistant that automates web research, extracts information from online sources, generates structured research reports, and evaluates report quality using a multi-agent workflow.

🚀 **[Try the Live App](https://research-agent-ixmhsdszjh2we5qqqkdvsq.streamlit.app/)** | 💻 **[View Source Code](https://github.com/chhavikant03/Research-Agent)**

## Overview

Research.AI simplifies the research process by combining web search, webpage content extraction, AI-powered report writing, and automated review. Users enter a research topic, and the application gathers relevant information to generate a structured report.

## Features

- **Web Research:** Finds relevant information using Tavily search.
- **Content Extraction:** Extracts readable content from webpages.
- **AI Report Generation:** Generates reports with introductions, key findings, conclusions, and references.
- **Automated Critic:** Evaluates reports for accuracy, citation use, depth, and clarity.
- **Report Revision:** Improves reports based on critic feedback when required.
- **Interactive Interface:** Provides a user-friendly Streamlit interface.

## Workflow

1. **Search Agent** — searches the web for relevant sources.
2. **Reader Agent** — extracts useful content from selected webpages.
3. **Writer** — generates a structured research report.
4. **Critic** — evaluates the report and provides feedback.
5. **Revision** — improves the report when its score falls below the configured threshold.

## Tech Stack

- **Language:** Python
- **Frontend:** Streamlit
- **LLM Integration:** Groq
- **AI Framework:** LangChain
- **Web Search:** Tavily
- **Web Scraping:** Requests, BeautifulSoup, Trafilatura
- **Configuration:** Environment variables and `.env`

## Project Structure

```text
Research-Agent/
├── app.py
├── agent.py
├── pipeline.py
├── tools.py
├── requirements.txt
├── .gitignore
└── README.md
```

### Prerequisites

- Python
- A Groq API key
- A Tavily API key

### Configure API keys

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
```

Replace the placeholders with your own API keys.

## Report Structure

Generated reports are designed to include:

- Introduction
- Key Findings
- Conclusion
- References

The critic reviews reports against the provided source material and evaluates accuracy, citation use, depth, and structure.

## Limitations

- Results depend on the availability and quality of web sources.
- Some websites may block automated content extraction.
- AI-generated claims and citations should be verified against original sources.
- Groq and Tavily usage is subject to their respective API limits.

## Future Improvements

- Export reports to PDF and DOCX.
- Improve source verification and citation accuracy.
- Add research history and saved reports.
- Enhance API error handling.
