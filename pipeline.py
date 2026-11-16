import re
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

from agent import build_search_agent, writer_chain, critic_chain, revise_chain
from tools import scrape_url


# Conservative limits to reduce Groq tokens-per-minute consumption.
SCORE_THRESHOLD = 7
MAX_REVISIONS = 1
MAX_SOURCES = 3
MAX_CANDIDATES = 5
MIN_CONTENT_CHARS = 500

MAX_CHARS_PER_SOURCE = 1200
MAX_SEARCH_OVERVIEW_CHARS = 1000
MAX_CRITIC_REPORT_CHARS = 4500
MAX_FEEDBACK_CHARS = 1200

BLOCKED_DOMAINS = (
    "yahoo.com", "facebook.com", "linkedin.com", "twitter.com",
    "x.com", "instagram.com", "youtube.com",
)

JUNK_PHRASES = (
    "oops, something went wrong", "skip to navigation",
    "enable javascript", "access denied", "are you a robot",
    "verify you are human", "could not scrape url",
)

URL_RE = re.compile(r'https?://[^\s\)\]\}>"\'\\]+')


def to_text(content) -> str:
    """Convert LangChain message content to plain text."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                parts.append(str(block.get("text", "") or ""))
            else:
                parts.append(str(getattr(block, "text", block)))
        return "\n".join(part for part in parts if part)
    return str(content)


def domain_of(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def extract_urls(text: str, limit: int = MAX_CANDIDATES) -> list:
    """Return unique URLs, one per domain, excluding blocked domains."""
    seen_urls, seen_domains, urls = set(), set(), []
    for url in URL_RE.findall(to_text(text)):
        url = url.rstrip(".,;:")
        domain = domain_of(url)
        if not domain or url in seen_urls or domain in seen_domains:
            continue
        if any(domain == blocked or domain.endswith("." + blocked)
               for blocked in BLOCKED_DOMAINS):
            continue
        seen_urls.add(url)
        seen_domains.add(domain)
        urls.append(url)
        if len(urls) >= limit:
            break
    return urls


def is_junk(content: str) -> bool:
    lowered = content.lower()
    return (
        len(content.strip()) < MIN_CONTENT_CHARS
        or any(phrase in lowered for phrase in JUNK_PHRASES)
    )


def scrape_one(url: str):
    """Scrape one URL and return shortened content."""
    try:
        content = to_text(scrape_url.invoke({"url": url}))
        if is_junk(content):
            return url, None
        return url, content[:MAX_CHARS_PER_SOURCE]
    except Exception:
        return url, None


def parse_score(feedback: str):
    match = re.search(
        r"Score:\s*\**\s*(\d+(?:\.\d+)?)\s*/\s*10",
        to_text(feedback),
        re.IGNORECASE,
    )
    return float(match.group(1)) if match else None


def run_research_pipeline(topic: str, progress_callback=None) -> dict:
    """Run search, extraction, writing and critic/revision stages."""
    if not topic or not topic.strip():
        raise ValueError("Please enter a research topic.")

    state = {"timings": {}}

    def emit(step, status, message, data=None):
        if progress_callback:
            progress_callback({
                "step": step,
                "status": status,
                "message": message,
                "data": data,
            })

    # SEARCH
    start = time.time()
    emit("search", "running", "Search Agent is searching for relevant sources.")

    search_agent = build_search_agent()
    search_result = search_agent.invoke({
        "messages": [
            ("user", f"Find reliable and relevant webpages about: {topic}. "
                     "Return titles, URLs and concise descriptions.")
        ]
    })

    messages = search_result.get("messages", [])
    state["search_results"] = (
        to_text(messages[-1].content) if messages else ""
    )
    all_search_text = "\n".join(
        to_text(message.content) for message in messages
    )

    state["timings"]["search"] = round(time.time() - start, 1)
    emit("search", "completed", "Search Agent found candidate sources.",
         state["search_results"])

    # READ: scrape candidate webpages concurrently.
    start = time.time()
    urls = extract_urls(all_search_text)
    emit("reader", "running",
         f"Reader is extracting content from {len(urls)} candidate sources.")

    sources = []
    if urls:
        with ThreadPoolExecutor(max_workers=min(3, len(urls))) as pool:
            for url, content in pool.map(scrape_one, urls):
                if content:
                    sources.append((url, content))

    sources = sources[:MAX_SOURCES]
    state["sources"] = sources
    state["scraped_content"] = "\n\n".join(
        f"{url}\n{content[:220]}..." for url, content in sources
    )
    state["timings"]["reader"] = round(time.time() - start, 1)
    emit(
        "reader", "completed",
        f"Reader extracted content from {len(sources)} of {len(urls)} sources.",
        state["scraped_content"] or
        "No pages could be extracted; search snippets will be used.",
    )

    if sources:
        sources_block = "\n\n".join(
            f"[{index}] {url}\n{content}"
            for index, (url, content) in enumerate(sources, start=1)
        )
    else:
        sources_block = (
            "No webpage content could be extracted. Use only the search "
            "overview and acknowledge the limited evidence."
        )

    search_overview = state["search_results"][:MAX_SEARCH_OVERVIEW_CHARS]

    # WRITE
    start = time.time()
    emit("writer", "running", "Writer is preparing the research report.")
    state["report"] = to_text(writer_chain.invoke({
        "topic": topic[:250],
        "sources": sources_block,
        "search_overview": search_overview,
    }))
    state["initial_report"] = state["report"]
    state["timings"]["writer"] = round(time.time() - start, 1)
    emit("writer", "completed", "Writer generated the research report.",
         state["report"])

    # CRITIC
    start = time.time()
    emit("critic", "running", "Critic is evaluating the report.")
    state["feedback"] = to_text(critic_chain.invoke({
        "report": state["report"][:MAX_CRITIC_REPORT_CHARS],
        "sources": sources_block,
    }))
    state["initial_score"] = parse_score(state["feedback"])
    state["initial_feedback"] = state["feedback"]
    state["revisions"] = 0

    score = parse_score(state["feedback"])
    if score is not None and score < SCORE_THRESHOLD and MAX_REVISIONS:
        state["revisions"] = 1
        emit("writer", "running",
             f"Score {score}/10 is below {SCORE_THRESHOLD}. Revising once.")

        state["report"] = to_text(revise_chain.invoke({
            "topic": topic[:250],
            "sources": sources_block,
            "report": state["report"][:MAX_CRITIC_REPORT_CHARS],
            "feedback": state["feedback"][:MAX_FEEDBACK_CHARS],
        }))
        emit("writer", "completed", "Writer produced a revised report.",
             state["report"])

        emit("critic", "running", "Critic is reviewing the revised report.")
        state["feedback"] = to_text(critic_chain.invoke({
            "report": state["report"][:MAX_CRITIC_REPORT_CHARS],
            "sources": sources_block,
        }))

    state["final_score"] = parse_score(state["feedback"])
    state["timings"]["critic_and_revision"] = round(time.time() - start, 1)
    emit("critic", "completed", "Critic completed the report evaluation.",
         state["feedback"])

    return state


if __name__ == "__main__":
    topic = input("\nEnter a research topic: ").strip()
    result = run_research_pipeline(topic)
    print("\nFinal Report\n")
    print(result["report"])
    print("\nCritic Review\n")
    print(result["feedback"])
    print("\nScores:", result["initial_score"], "->", result["final_score"])
    print("Sources scraped:", len(result["sources"]))
    for url, content in result["sources"]:
        print(" -", url, f"({len(content)} characters)")
    print("Timings:", result["timings"])
