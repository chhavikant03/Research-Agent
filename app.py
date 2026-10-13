import re
import streamlit as st
from pipeline import run_research_pipeline

st.set_page_config(
    page_title="RESEARCH.AI",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
:root{
  --bg:#090811;
  --surface:#12101b;
  --surface2:#191526;
  --surface3:#211b31;
  --line:#302746;
  --text:#f3effa;
  --muted:#958aa9;
  --accent:#9b6bff;
  --accent2:#c084fc;
  --success:#65d69b;
  --danger:#e0607e;
}

.stApp{
  background:
    radial-gradient(circle at 50% -10%, rgba(155,107,255,.16), transparent 32rem),
    var(--bg);
  color:var(--text);
}

#MainMenu, header, footer { visibility:hidden; }
.block-container{max-width:1180px;padding:1rem 1.25rem 0;}

*{box-sizing:border-box;}
h1,h2,h3,.mono{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;}
p,div,span,label,textarea,input,button{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;}

.topbar{
  height:64px;
  display:flex;
  align-items:center;
  justify-content:space-between;
  padding:0 1.15rem;
  border:1px solid var(--line);
  border-radius:14px;
  background:rgba(18,16,27,.88);
  backdrop-filter:blur(14px);
  margin-bottom:4.5rem;
}
.brand{font:700 1rem ui-monospace,SFMono-Regular,monospace;color:var(--text);}
.brand span{color:var(--accent);}
.nav{display:flex;gap:1.5rem;color:var(--muted);font-size:.82rem;}
.nav span:hover{color:var(--text);}
.badge{
  color:var(--accent2);
  border:1px solid var(--line);
  background:rgba(155,107,255,.08);
  border-radius:999px;
  padding:.35rem .7rem;
  font:700 .68rem ui-monospace,SFMono-Regular,monospace;
  letter-spacing:.08em;
}

.hero{text-align:center;margin-bottom:2.4rem;}
.eyebrow{
  display:inline-block;
  color:var(--accent2);
  font:700 .7rem ui-monospace,SFMono-Regular,monospace;
  letter-spacing:.16em;
  text-transform:uppercase;
  margin-bottom:1rem;
}
.hero h1{
  font-size:3.15rem;
  line-height:1.08;
  margin:0;
  letter-spacing:-.06em;
  background:linear-gradient(135deg,#fff 25%,var(--accent2) 80%);
  -webkit-background-clip:text;
  background-clip:text;
  color:transparent;
}
.hero p{
  max-width:650px;
  margin:1rem auto 0;
  color:var(--muted);
  font-size:1rem;
  line-height:1.7;
}

.stForm{
  border:1px solid var(--line)!important;
  background:linear-gradient(145deg,var(--surface2),var(--surface))!important;
  border-radius:16px!important;
  padding:1.2rem!important;
  box-shadow:0 20px 70px rgba(0,0,0,.28);
  margin-bottom:2.5rem;
}
.stTextArea textarea{
  background:var(--surface)!important;
  color:var(--text)!important;
  border:1px solid var(--line)!important;
  border-radius:11px!important;
  font-size:.95rem!important;
}
.stTextArea textarea:focus{
  border-color:var(--accent)!important;
  box-shadow:0 0 0 1px var(--accent)!important;
}
.stFormSubmitButton>button{
  background:linear-gradient(135deg,var(--accent),var(--accent2))!important;
  color:#0b0910!important;
  border:0!important;
  border-radius:9px!important;
  font-weight:800!important;
  padding:.55rem 1.4rem!important;
}

.section-title{
  color:var(--accent2);
  font:700 .72rem ui-monospace,SFMono-Regular,monospace;
  letter-spacing:.13em;
  text-transform:uppercase;
  padding-bottom:.65rem;
  border-bottom:1px solid var(--line);
  margin-bottom:.8rem;
}

.pipeline{
  border:1px solid var(--line);
  background:var(--surface);
  border-radius:15px;
  padding:.75rem 1rem;
}
.node{
  position:relative;
  display:flex;
  gap:.8rem;
  padding:1rem .35rem;
  border-bottom:1px solid var(--line);
}
.node:last-child{border-bottom:0;}
.node:not(:last-child):after{
  content:"";
  position:absolute;
  left:8px;
  bottom:-13px;
  height:25px;
  border-left:1px dashed #493d62;
}
.dot{
  width:10px;height:10px;border-radius:50%;
  margin-top:.3rem;flex:none;background:#493d62;
}
.dot.running{
  background:var(--accent);
  box-shadow:0 0 0 5px rgba(155,107,255,.13),0 0 15px var(--accent);
  animation:pulse 1.3s infinite;
}
.dot.done{background:var(--success);}
.dot.error{background:var(--danger);}
@keyframes pulse{50%{opacity:.35;transform:scale(.8)}}
.node-label{font:700 .86rem ui-monospace,SFMono-Regular,monospace;color:var(--text);}
.node-sub{font-size:.72rem;color:var(--muted);margin-top:.2rem;}
.node-msg{font-size:.72rem;color:var(--accent2);margin-top:.35rem;line-height:1.4;}
.node-msg.error{color:var(--danger);}

.report{
  border:1px solid var(--line);
  background:var(--surface);
  border-radius:15px;
  min-height:390px;
  padding:1.45rem;
}
.report-head{
  display:flex;justify-content:space-between;align-items:center;
  border-bottom:1px solid var(--line);padding-bottom:1rem;margin-bottom:1rem;
}
.report-title{font:700 .8rem ui-monospace,SFMono-Regular,monospace;color:var(--text);}
.tag{
  color:var(--accent2);
  border:1px solid var(--line);
  background:rgba(155,107,255,.08);
  border-radius:999px;
  padding:.25rem .55rem;
  font:700 .62rem ui-monospace,SFMono-Regular,monospace;
  text-transform:uppercase;
}
.empty{text-align:center;color:var(--muted);padding:7rem 1rem 4rem;font-size:.9rem;}
.report-body{line-height:1.75;color:#e8e1f1;font-size:.92rem;}
.report-body h1,.report-body h2,.report-body h3{color:var(--text);}

.stTabs [data-baseweb="tab-list"]{
  background:var(--surface);
  border:1px solid var(--line);
  border-radius:12px;
  padding:.3rem;
  gap:.2rem;
}
.stTabs [data-baseweb="tab"]{
  color:var(--muted);
  border-radius:8px;
  font:700 .72rem ui-monospace,SFMono-Regular,monospace;
}
.stTabs [aria-selected="true"]{background:var(--surface2);color:var(--accent2)!important;}
.stTabs [data-baseweb="tab-panel"]{
  background:var(--surface);
  border:1px solid var(--line);
  border-top:0;
  border-radius:0 0 12px 12px;
  padding:1rem;
}

.stDownloadButton>button{
  background:var(--surface2)!important;
  color:var(--accent2)!important;
  border:1px solid var(--line)!important;
  border-radius:8px!important;
}

.source{
  padding:.75rem 0;
  border-bottom:1px solid var(--line);
  color:var(--accent2);
  word-break:break-all;
  font-size:.82rem;
}
.source a{color:var(--accent2);text-decoration:none;}

.footer{
  margin-top:5rem;
  padding:2rem 0 1rem;
  border-top:1px solid var(--line);
  display:flex;
  justify-content:space-between;
  color:var(--muted);
  font-size:.72rem;
}
.footer strong{color:var(--text);}
.footer-right{font-family:ui-monospace,SFMono-Regular,monospace;}

@media(max-width:800px){
  .nav{display:none;}
  .hero h1{font-size:2.25rem;}
  .topbar{margin-bottom:3rem;}
}
</style>
""", unsafe_allow_html=True)

STAGES = ["search", "reader", "writer", "critic"]
STAGE_META = {
    "search": ("Search Agent", "Tavily", "Scanning the web"),
    "reader": ("Reader Agent", "BeautifulSoup", "Reading the source"),
    "writer": ("Writer", "Mistral + LCEL", "Drafting the report"),
    "critic": ("Critic", "Mistral + LCEL", "Reviewing the draft"),
}

defaults = {
    "stage_status": {s: "pending" for s in STAGES},
    "stage_message": {s: "" for s in STAGES},
    "results": {},
    "sources": [],
    "error": None,
    "_tab_render_count": 0,
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value.copy() if isinstance(value, dict) else value

st.markdown("""
<div class="topbar">
  <div class="brand">◈ RESEARCH<span>.AI</span></div>
  <div class="nav">
    <span>Research</span><span>How it works</span><span>Multi-Agent</span>
  </div>
  <div class="badge">AI RESEARCH</div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <div class="eyebrow">Autonomous Research Workspace</div>
  <h1>Turn questions into<br>research reports.</h1>
  <p>
    A multi-agent research workflow that searches the web, reads relevant
    sources, synthesizes findings, and critically reviews the final report.
  </p>
</div>
""", unsafe_allow_html=True)

with st.form("research_form"):
    st.markdown(
        '<div class="mono" style="font-size:.72rem;color:#958aa9;margin-bottom:.5rem;">'
        'RESEARCH QUERY</div>',
        unsafe_allow_html=True,
    )
    topic = st.text_area(
        "topic",
        placeholder="e.g. Impact of generative AI on software development in 2026",
        label_visibility="collapsed",
        height=85,
    )
    run_clicked = st.form_submit_button("Start Research →", use_container_width=False)

def extract_sources(*texts):
    """Best-effort URL extraction from agent output text, in case the
    search/reader agents don't return structured source data.

    Handles: plain URLs, markdown links [title](url), and URLs wrapped in
    angle brackets or trailing punctuation from sentence context.
    """
    urls, seen = [], set()
    for text in texts:
        if not text:
            continue
        s = str(text)

        for match in re.findall(r"\]\((https?://[^\)\s]+)\)", s):
            cleaned = match.rstrip(".,;:")
            if cleaned not in seen:
                seen.add(cleaned)
                urls.append(cleaned)

        for match in re.findall(r"https?://[^\s\)\]\'\"<>,]+", s):
            cleaned = match.rstrip(".,;:)")
            if cleaned not in seen:
                seen.add(cleaned)
                urls.append(cleaned)

    return urls[:10]


def render_stage(stage, placeholder):
    label, sub, _ = STAGE_META[stage]
    status = st.session_state.stage_status[stage]
    msg = st.session_state.stage_message[stage]
    css = "done" if status == "completed" else status
    show_msg = msg if status in ("running", "error") else ""
    msg_cls = "node-msg error" if status == "error" else "node-msg"

    placeholder.markdown(
        f"""
        <div class="node">
          <div class="dot {css}"></div>
          <div>
            <div class="node-label">{label}</div>
            <div class="node-sub">{sub}</div>
            {f'<div class="{msg_cls}">{show_msg}</div>' if show_msg else ''}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_report(placeholder):
    report = st.session_state.results.get("report")
    if not report:
        placeholder.markdown(
            """
            <div class="report">
              <div class="empty">
                <div style="font-size:2rem;margin-bottom:1rem;">◈</div>
                Your research report will appear here.
                <br>Start a research run to begin.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    status = "REVIEWED" if st.session_state.stage_status["critic"] == "completed" else "UNDER REVIEW"

    with placeholder.container():
        st.markdown(
            f"""
            <div class="report">
              <div class="report-head">
                <div class="report-title">RESEARCH REPORT</div>
                <div class="tag">{status}</div>
              </div>
              <div class="report-body">
            """,
            unsafe_allow_html=True,
        )
        st.markdown(report)
        st.markdown("</div></div>", unsafe_allow_html=True)


def render_tabs(placeholders):
    ph_search, ph_scraped, ph_critic, ph_sources = placeholders

    ph_search.write(st.session_state.results.get("search_results") or "No search results yet.")
    ph_scraped.write(st.session_state.results.get("scraped_content") or "No scraped evidence yet.")
    ph_critic.markdown(st.session_state.results.get("feedback") or "No critic review yet.")

    if st.session_state.sources:
        links_html = "".join(
            f'<div class="source"><a href="{u}" target="_blank">{u}</a></div>'
            for u in st.session_state.sources
        )
        ph_sources.markdown(links_html, unsafe_allow_html=True)
    else:
        raw = " ".join(
            str(v) for v in [
                st.session_state.results.get("search_results"),
                st.session_state.results.get("scraped_content"),
            ] if v
        )
        if raw:
            st.session_state._tab_render_count += 1
            with ph_sources.container():
                st.write(
                    "No `http(s)://` URLs matched in the agent output. Raw text below — "
                    "share this if the format needs a different pattern:"
                )
                st.text_area(
                    "raw_output_debug", raw, height=220,
                    label_visibility="collapsed",
                    key=f"raw_output_debug_{st.session_state._tab_render_count}",
                )
        else:
            ph_sources.write("No source URLs detected yet.")

left, right = st.columns([.85, 1.65], gap="large")

with left:
    st.markdown('<div class="section-title">01 / Pipeline</div>', unsafe_allow_html=True)
    st.markdown('<div class="pipeline">', unsafe_allow_html=True)

    node_placeholders = {}
    for stage in STAGES:
        node_placeholders[stage] = st.empty()
        render_stage(stage, node_placeholders[stage])

    st.markdown("</div>", unsafe_allow_html=True)

with right:
    title_col, action_col = st.columns([3, 1])

    with title_col:
        st.markdown('<div class="section-title">02 / Research Report</div>', unsafe_allow_html=True)

    with action_col:
        download_placeholder = st.empty()

    output_placeholder = st.empty()

    def render_download(placeholder):
        report = st.session_state.results.get("report")
        with placeholder.container():
            if report:
                st.download_button(
                    "↓ Download",
                    report,
                    "research_report.md",
                    "text/markdown",
                    use_container_width=True,
                    key=f"download_{len(report)}",
                )

    render_download(download_placeholder)
    render_report(output_placeholder)

st.markdown("<br>", unsafe_allow_html=True)
tab1, tab2, tab3, tab4 = st.tabs(
    ["Search Results", "Scraped Evidence", "Critic Review", "Sources"]
)

with tab1:
    tab1_ph = st.empty()
with tab2:
    tab2_ph = st.empty()
with tab3:
    tab3_ph = st.empty()
with tab4:
    tab4_ph = st.empty()

tab_placeholders = (tab1_ph, tab2_ph, tab3_ph, tab4_ph)
render_tabs(tab_placeholders)

if st.session_state.error:
    st.error(f"Pipeline failed: {st.session_state.error}")

if run_clicked:
    if not topic.strip():
        st.warning("Enter a research topic before starting.")
        st.stop()

    st.session_state.stage_status = {s: "pending" for s in STAGES}
    st.session_state.stage_message = {s: "" for s in STAGES}
    st.session_state.results = {}
    st.session_state.sources = []
    st.session_state.error = None

    for stage in STAGES:
        render_stage(stage, node_placeholders[stage])
    render_report(output_placeholder)
    render_download(download_placeholder)
    render_tabs(tab_placeholders)

    last_stage = {"value": None}

    def progress_callback(event):
        stage = event["step"]
        status = event["status"]

        st.session_state.stage_status[stage] = status
        st.session_state.stage_message[stage] = event.get("message", "")
        last_stage["value"] = stage

        render_stage(stage, node_placeholders[stage])

        if status == "completed":
            data = event.get("data")

            if stage == "search":
                st.session_state.results["search_results"] = data
                st.session_state.sources = extract_sources(data)

            elif stage == "reader":
                st.session_state.results["scraped_content"] = data
                st.session_state.sources = extract_sources(
                    st.session_state.results.get("search_results"), data
                )

            elif stage == "writer":
                st.session_state.results["report"] = data
                render_report(output_placeholder)
                render_download(download_placeholder)

            elif stage == "critic":
                st.session_state.results["feedback"] = data
                render_report(output_placeholder)  
            render_tabs(tab_placeholders)

    try:
        run_research_pipeline(topic.strip(), progress_callback=progress_callback)

    except Exception as e:
        stage = last_stage["value"]
        if stage:
            st.session_state.stage_status[stage] = "error"
            st.session_state.stage_message[stage] = str(e)
            render_stage(stage, node_placeholders[stage])

        st.session_state.error = str(e)
        st.error(f"Pipeline failed: {e}")

st.markdown("""
<div class="footer">
  <div>
    <strong>◈ RESEARCH.AI</strong><br>
    Multi-agent research workspace
  </div>
  <div class="footer-right">
    Search · Read · Write · Critic<br>
    © 2026 RESEARCH.AI
  </div>
</div>
""", unsafe_allow_html=True)