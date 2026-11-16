import os

import requests
import trafilatura
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langchain.tools import tool
from tavily import TavilyClient

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
if not TAVILY_API_KEY:
    raise ValueError(
        "TAVILY_API_KEY is missing. Add it to your .env file or deployment secrets."
    )

tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


@tool
def web_search(query: str) -> str:
    """Search the web and return titles, URLs and concise snippets."""
    results = tavily_client.search(query=query, max_results=5)
    output = []
    for result in results.get("results", []):
        output.append(
            f"Title: {result.get('title', 'Untitled')}\n"
            f"URL: {result.get('url', '')}\n"
            f"Snippet: {result.get('content', '')[:180]}"
        )
    return "\n\n-----\n\n".join(output) or "No search results returned."


@tool
def scrape_url(url: str) -> str:
    """Download a webpage and extract its main readable text."""
    try:
        response = requests.get(url, timeout=12, headers=HEADERS)
        response.raise_for_status()

        extracted = trafilatura.extract(
            response.text,
            include_comments=False,
            include_tables=False,
        )
        if extracted and len(extracted.strip()) > 200:
            return extracted[:3000]

        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup([
            "script", "style", "nav", "footer", "header",
            "aside", "form", "noscript",
        ]):
            tag.decompose()

        paragraphs = [
            paragraph.get_text(" ", strip=True)
            for paragraph in soup.find_all("p")
        ]
        text = " ".join(p for p in paragraphs if len(p) > 40)
        if text.strip():
            return text[:3000]

        return "Could not scrape URL: no readable page content found."
    except requests.RequestException as exc:
        return f"Could not scrape URL: {exc}"
    except Exception as exc:
        return f"Could not scrape URL: {exc}"
