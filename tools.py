from langchain.tools import tool
import requests
from bs4 import BeautifulSoup
from tavily import TavilyClient
import trafilatura
import os
from dotenv import load_dotenv
load_dotenv()

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
    "Accept-Language": "en-US,en;q=0.9",
}


@tool
def web_search(query: str) -> str:
    """
    Search the web for recent reliable information on a topic. Return Titles, URLs and snippets.
    """
    # More results gives the pipeline more candidate domains to choose from
    results = tavily_client.search(query=query, max_results=8)
    out = []
    for r in results["results"]:
        out.append(f"Title: {r['title']}\nURL: {r['url']}\nSnippet: {r['content'][:300]}\n")
    return "\n-------\n".join(out)


@tool
def scrape_url(url: str) -> str:
    """Scrape and return the main readable article text from a given URL for deeper reading."""
    try:
        resp = requests.get(url, timeout=10, headers=HEADERS)
        resp.raise_for_status()

        # 1) Best option: extract only the main article body
        text = trafilatura.extract(resp.text, include_comments=False, include_tables=False)
        if text and len(text.strip()) > 200:
            return text[:4000]

        # 2) Fallback: BeautifulSoup, paragraphs only, with page chrome removed
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form", "noscript"]):
            tag.decompose()
        paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
        text = " ".join(p for p in paragraphs if len(p) > 40)
        return text[:4000]
    except Exception as e:
        return f"Could not scrape URL: {str(e)}"
