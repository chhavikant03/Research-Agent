import re
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

from agent import build_search_agent, writer_chain, critic_chain, revise_chain
from tools import scrape_url


SCORE_THRESHOLD = 7       # revise if the critic scores below this
MAX_REVISIONS = 1         # keep at 1 to stay within free-tier API limits
MAX_SOURCES = 4           # sources passed to the writer
MAX_CANDIDATES = 8        # URLs to try scraping
MIN_CONTENT_CHARS = 800   # shorter pages are treated as junk

BLOCKED_DOMAINS = ("yahoo.com", "facebook.com", "linkedin.com",
                   "twitter.com", "x.com", "instagram.com", "youtube.com")
JUNK_PHRASES = ("oops, something went wrong", "skip to navigation",
                "enable javascript", "access denied", "are you a robot",
                "verify you are human", "could not scrape url")

URL_RE = re.compile(r'https?://[^\s\)\]\}>"\'\\]+')


def to_text(content) -> str:
    """Normalize LangChain content (str, list of blocks, or other) to a plain string."""
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
        return "\n".join(p for p in parts if p)
    return str(content)


def domain_of(url: str) -> str:
    return urlparse(url).netloc.lower().replace("www.", "")


def extract_urls(text: str, limit: int = MAX_CANDIDATES) -> list:
    """Unique URLs, one per domain, skipping blocked domains."""
    seen_urls, seen_domains, urls = set(), set(), []
    for u in URL_RE.findall(to_text(text)):
        u = u.rstrip(".,;:")
        d = domain_of(u)
        if u in seen_urls or d in seen_domains:
            continue
        if any(d == b or d.endswith("." + b) for b in BLOCKED_DOMAINS):
            continue
        seen_urls.add(u)
        seen_domains.add(d)
        urls.append(u)
    return urls[:limit]


def is_junk(content: str) -> bool:
    c = content.lower()
    return len(c.strip()) < MIN_CONTENT_CHARS or any(p in c for p in JUNK_PHRASES)


def scrape_one(url: str):
    try:
        content = to_text(scrape_url.invoke({"url": url}))
        return url, (None if is_junk(content) else content[:3000])
    except Exception:
        return url, None


def parse_score(feedback: str):
    m = re.search(r"Score:\s*\**\s*(\d+(?:\.\d+)?)\s*/\s*10", to_text(feedback))
    return float(m.group(1)) if m else None


def run_research_pipeline(topic: str, progress_callback=None) -> dict:
    state = {"timings": {}}

    def emit(step, status, message, data=None):
        if progress_callback:
            progress_callback({"step": step, "status": status,
                               "message": message, "data": data})

    # ---------- SEARCH ----------
    t0 = time.time()
    emit("search", "running", "Search Agent is searching for recent and reliable sources.")
    search_agent = build_search_agent()
    search_result = search_agent.invoke({
        "messages": [("user", f"Find recent, reliable and detailed information about: {topic}")]
    })

    # Final summary from the agent (for display and the writer overview)
    state["search_results"] = to_text(search_result["messages"][-1].content)

    # Scan ALL messages (tool outputs included) so URLs are not missed
    all_text = "\n".join(to_text(m.content) for m in search_result["messages"])

    state["timings"]["search"] = round(time.time() - t0, 1)
    emit("search", "completed", "Search Agent found relevant research sources.",
         state["search_results"])

    # ---------- READ (parallel, multi-source) ----------
    t0 = time.time()
    urls = extract_urls(all_text)
    emit("reader", "running", f"Reader is scraping {len(urls)} candidate sources in parallel.")

    sources = []   # list of (url, content)
    if urls:
        with ThreadPoolExecutor(max_workers=len(urls)) as pool:
            for url, content in pool.map(scrape_one, urls):   # keeps search-rank order
                if content:
                    sources.append((url, content))
    sources = sources[:MAX_SOURCES]

    state["sources"] = sources
    state["scraped_content"] = "\n\n".join(f"{u}\n{c[:300]}..." for u, c in sources)
    state["timings"]["reader"] = round(time.time() - t0, 1)
    emit("reader", "completed",
         f"Reader extracted clean content from {len(sources)} of {len(urls)} candidate sources.",
         state["scraped_content"] or "No scrapable sources; falling back to search snippets.")

    # Build the numbered source block for citations
    if sources:
        sources_block = "\n\n".join(
            f"[{i}] {url}\n{content}" for i, (url, content) in enumerate(sources, 1)
        )
    else:
        sources_block = "No scraped content available. Use only the search overview."

    # ---------- WRITE ----------
    t0 = time.time()
    emit("writer", "running", "Writer is synthesizing the research into a cited report.")
    state["report"] = to_text(writer_chain.invoke({
        "topic": topic,
        "sources": sources_block,
        "search_overview": state["search_results"],
    }))
    state["initial_report"] = state["report"]
    state["timings"]["writer"] = round(time.time() - t0, 1)
    emit("writer", "completed", "Writer generated the research report.", state["report"])

    # ---------- CRITIC + REVISION LOOP ----------
    t0 = time.time()
    emit("critic", "running", "Critic is reviewing the report for quality and weaknesses.")
    state["feedback"] = to_text(critic_chain.invoke({
        "report": state["report"],
        "sources": sources_block,
    }))
    state["initial_score"] = parse_score(state["feedback"])
    state["initial_feedback"] = state["feedback"]
    state["revisions"] = 0

    while (state["revisions"] < MAX_REVISIONS
           and parse_score(state["feedback"]) is not None
           and parse_score(state["feedback"]) < SCORE_THRESHOLD):

        state["revisions"] += 1
        emit("writer", "running",
             f"Score {parse_score(state['feedback'])}/10 is below {SCORE_THRESHOLD}. "
             f"Writer is revising (round {state['revisions']}).")
        state["report"] = to_text(revise_chain.invoke({
            "topic": topic,
            "sources": sources_block,
            "report": state["report"],
            "feedback": state["feedback"],
        }))
        emit("writer", "completed", "Writer produced a revised report.", state["report"])

        emit("critic", "running", "Critic is re-reviewing the revised report.")
        state["feedback"] = to_text(critic_chain.invoke({
            "report": state["report"],
            "sources": sources_block,
        }))

    state["final_score"] = parse_score(state["feedback"])
    state["timings"]["critic_and_revision"] = round(time.time() - t0, 1)
    emit("critic", "completed", "Critic completed the report evaluation.", state["feedback"])

    return state


if __name__ == "__main__":
    topic = input("\nEnter a research topic: ")
    result = run_research_pipeline(topic)
    print("\nFinal Report\n")
    print(result["report"])
    print("\nCritic Review\n")
    print(result["feedback"])
    print("\nScores:", result["initial_score"], "->", result["final_score"])
    print("Sources scraped:", len(result["sources"]))
    for u, c in result["sources"]:
        print(" -", u, f"({len(c)} chars)")
    print("Timings:", result["timings"])
