import streamlit as st
import fitz
from google import genai
import time
import os
import re

# ============================================================
# APP CONFIG
# ============================================================
st.set_page_config(
    page_title="ResearchLens AI",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# RESUME-WORTHY UI
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

.stApp {
    background: #f5f7fb;
    font-family: 'Inter', sans-serif;
}

.block-container {
    max-width: 1250px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

.hero {
    padding: 42px 44px;
    border-radius: 26px;
    margin-bottom: 26px;
    background: linear-gradient(135deg, #111827 0%, #312e81 55%, #6d28d9 100%);
    color: white;
    box-shadow: 0 18px 50px rgba(49,46,129,.20);
}

.badge {
    display: inline-block;
    padding: 7px 12px;
    border: 1px solid rgba(255,255,255,.22);
    border-radius: 999px;
    background: rgba(255,255,255,.10);
    font-size: 12px;
    font-weight: 700;
    letter-spacing: .4px;
}

.hero h1 {
    margin: 16px 0 8px;
    font-size: 43px;
    line-height: 1.08;
    font-weight: 800;
    letter-spacing: -1.5px;
}

.hero p {
    margin: 0;
    max-width: 850px;
    color: rgba(255,255,255,.86);
    line-height: 1.7;
    font-size: 16px;
}

.section {
    font-size: 22px;
    font-weight: 800;
    color: #111827;
    margin: 28px 0 14px;
}

.card {
    background: white;
    border: 1px solid #e7eaf0;
    border-radius: 18px;
    padding: 22px;
    box-shadow: 0 8px 28px rgba(15,23,42,.055);
    height: 100%;
}

.card h3 {
    margin: 0 0 8px;
    color: #111827;
    font-size: 17px;
}

.card p {
    color: #64748b;
    line-height: 1.6;
    font-size: 14px;
}

.metric {
    background: white;
    border: 1px solid #e7eaf0;
    border-radius: 17px;
    padding: 20px 12px;
    text-align: center;
    box-shadow: 0 7px 24px rgba(15,23,42,.05);
}

.metric-value {
    font-size: 29px;
    font-weight: 800;
    color: #4f46e5;
}

.metric-label {
    margin-top: 4px;
    color: #64748b;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.file-chip {
    padding: 13px 16px;
    border-radius: 13px;
    background: #eef2ff;
    border: 1px solid #c7d2fe;
    color: #3730a3;
    font-weight: 650;
    margin: 10px 0 18px;
}

.footer {
    text-align: center;
    margin-top: 45px;
    padding-top: 25px;
    border-top: 1px solid #e5e7eb;
    color: #64748b;
    font-size: 13px;
}

div[data-testid="stFileUploader"] {
    background: white;
    border: 1.5px dashed #a5b4fc;
    border-radius: 18px;
    padding: 12px;
}

.stButton > button, .stDownloadButton > button {
    border-radius: 12px;
    min-height: 45px;
    font-weight: 700;
}

[data-testid="stSidebar"] {
    background: white;
}

[data-testid="stSidebar"] h2 {
    color: #111827;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# SESSION STATE
# ============================================================
defaults = {
    "paper_text": None,
    "summary": None,
    "file_name": None,
    "page_count": 0,
    "analysis_time": 0,
    "history": [],
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ============================================================
# HELPERS
# ============================================================
def extract_text(uploaded_file):
    pdf = None
    try:
        pdf_bytes = uploaded_file.getvalue()
        pdf = fitz.open(stream=pdf_bytes, filetype="pdf")

        pages = []
        for page in pdf:
            text = page.get_text("text")
            if text:
                pages.append(text)

        return "\n".join(pages).strip(), pdf.page_count
    except Exception as exc:
        raise RuntimeError(f"Unable to read PDF: {exc}")
    finally:
        if pdf is not None:
            pdf.close()


def create_client(api_key):
    if not api_key:
        return None
    try:
        return genai.Client(api_key=api_key.strip())
    except Exception as exc:
        st.error(f"Gemini connection failed: {exc}")
        return None


def generate_summary(client, text, model_name, mode):
    if mode == "Quick Overview":
        focus = """
Create a concise overview emphasizing the problem, approach, major findings,
and conclusion. Keep it highly readable for a student or recruiter.
"""
    elif mode == "Technical Deep Dive":
        focus = """
Give extra attention to algorithms, architecture, datasets, experimental setup,
evaluation metrics, technical decisions, limitations, and results.
"""
    else:
        focus = """
Create a balanced academic summary suitable for understanding the paper quickly,
with enough technical detail to be useful in an interview or project discussion.
"""

    prompt = f"""
You are an expert academic research assistant.

Analyze ONLY the research paper supplied below.
{focus}

Return the answer using this exact Markdown structure:

# Paper Title
# Executive Summary
# Research Objective
# Methodology
# Key Findings
# Conclusion
# Limitations
# Five Important Keywords
# Interview Takeaways

Rules:
- Do not invent information.
- If something is unavailable, write: "Not specified in the paper."
- Preserve important technical terminology.
- Use simple, professional language.
- Keep findings tied to the paper.
- Provide exactly five keywords.
- For Interview Takeaways, give 3-5 concise points a student could discuss.
- Do not discuss information outside the paper.

Research Paper:
{text[:50000]}
"""

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    if not getattr(response, "text", None):
        raise RuntimeError("Gemini returned an empty response.")

    return response.text


def make_text_download(summary, file_name):
    header = f"AI Research Analysis\nDocument: {file_name}\n\n"
    return header + summary


# ============================================================
# HERO
# ============================================================
st.markdown("""
<div class="hero">
    <span class="badge">AI • NLP • DOCUMENT INTELLIGENCE</span>
    <h1>🔬 ResearchLens AI</h1>
    <p>
        Turn lengthy research papers into structured, interview-ready insights.
        Upload a PDF, extract its content with PyMuPDF, and generate an
        academically grounded analysis using Google Gemini.
    </p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("## ⚙️ Analysis Settings")
    st.caption("Configure the AI pipeline before generating your analysis.")

    api_key = st.text_input(
        "Gemini API Key",
        value=os.getenv("GEMINI_API_KEY", ""),
        type="password",
        placeholder="Paste your API key",
        help="You can also set GEMINI_API_KEY as an environment variable.",
    )

    model_choice = st.selectbox(
        "AI Model",
        ["gemini-3.7-flash", "gemini-3.6-flash"],
        index=0,
    )

    analysis_mode = st.radio(
        "Analysis Mode",
        ["Balanced Analysis", "Quick Overview", "Technical Deep Dive"],
        index=0,
    )

    st.divider()
    st.markdown("### 🧠 Pipeline")
    st.markdown("""
**01 — Upload**  
PDF research paper

**02 — Extract**  
PyMuPDF text extraction

**03 — Analyze**  
Gemini-powered reasoning

**04 — Present**  
Structured academic insights
""")

    st.divider()
    st.markdown("### 🛠 Tech Stack")
    st.caption("Python • Streamlit • PyMuPDF • Google Gemini API")

    if st.button("🗑️ Clear Current Analysis", use_container_width=True):
        st.session_state.summary = None
        st.session_state.paper_text = None
        st.session_state.file_name = None
        st.session_state.page_count = 0
        st.rerun()

# ============================================================
# UPLOAD
# ============================================================
st.markdown('<div class="section">📤 Upload Research Paper</div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Drop a PDF here or click Browse",
    type=["pdf"],
    help="Text-based research PDFs work best.",
)

if uploaded_file is not None:
    if st.session_state.file_name != uploaded_file.name:
        with st.spinner("📖 Extracting document content..."):
            try:
                text, pages = extract_text(uploaded_file)

                if not text:
                    st.error(
                        "No readable text was detected. This app currently works "
                        "best with text-based PDFs rather than scanned image PDFs."
                    )
                    st.stop()

                st.session_state.paper_text = text
                st.session_state.page_count = pages
                st.session_state.file_name = uploaded_file.name
                st.session_state.summary = None
            except Exception as exc:
                st.error(str(exc))
                st.stop()

    paper_text = st.session_state.paper_text
    word_count = len(paper_text.split())
    estimated_read = max(1, round(word_count / 200))

    st.markdown(
        f'<div class="file-chip">📄 {st.session_state.file_name} &nbsp; • &nbsp; '
        f'{st.session_state.page_count} pages detected</div>',
        unsafe_allow_html=True,
    )

    # ========================================================
    # DOCUMENT METRICS
    # ========================================================
    st.markdown('<div class="section">📊 Document Intelligence</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)

    metrics = [
        (st.session_state.page_count, "Pages"),
        (f"{word_count:,}", "Words"),
        (estimated_read, "Min Read"),
        (analysis_mode.replace(" Analysis", ""), "Mode"),
    ]

    for col, (value, label) in zip([c1, c2, c3, c4], metrics):
        with col:
            st.markdown(
                f'<div class="metric"><div class="metric-value">{value}</div>'
                f'<div class="metric-label">{label}</div></div>',
                unsafe_allow_html=True,
            )

    # ========================================================
    # FEATURE CARDS
    # ========================================================
    st.markdown('<div class="section">✨ AI Capabilities</div>', unsafe_allow_html=True)

    f1, f2, f3 = st.columns(3)
    cards = [
        ("🎯", "Research Objective",
         "Identify the research problem, goals, questions, and motivation."),
        ("🧪", "Methodology",
         "Extract datasets, algorithms, tools, experiments, and evaluation methods."),
        ("💡", "Research Insights",
         "Surface findings, limitations, keywords, conclusions, and interview takeaways."),
    ]

    for col, (icon, title, description) in zip([f1, f2, f3], cards):
        with col:
            st.markdown(
                f'<div class="card"><h3>{icon} {title}</h3>'
                f'<p>{description}</p></div>',
                unsafe_allow_html=True,
            )

    # ========================================================
    # INTERACTIVE WORKSPACE
    # ========================================================
    st.markdown('<div class="section">🧩 Analysis Workspace</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs([
        "📃 Document Preview",
        "🤖 AI Analysis",
        "🔎 Search Paper",
    ])

    with tab1:
        st.caption("Preview the extracted text before sending it to Gemini.")
        preview_limit = st.slider(
            "Preview length",
            min_value=1000,
            max_value=min(15000, max(1000, len(paper_text))),
            value=min(5000, max(1000, len(paper_text))),
            step=1000,
        )
        st.text_area(
            "Extracted content",
            paper_text[:preview_limit],
            height=420,
            label_visibility="collapsed",
        )

    with tab2:
        st.markdown("### 🤖 Generate AI Research Analysis")
        st.caption(
            f"Mode: **{analysis_mode}** • Model: **{model_choice}**"
        )

        if st.button(
            "✨ Generate AI Summary",
            type="primary",
            use_container_width=True,
        ):
            if not api_key:
                st.warning(
                    "Please add your Gemini API key in the sidebar or set "
                    "GEMINI_API_KEY in your environment."
                )
            else:
                client = create_client(api_key)

                if client:
                    progress = st.progress(0, text="Preparing analysis...")
                    start = time.time()

                    try:
                        progress.progress(20, text="Reading research content...")
                        time.sleep(0.2)

                        progress.progress(45, text="Analyzing with Gemini AI...")
                        summary = generate_summary(
                            client,
                            paper_text,
                            model_choice,
                            analysis_mode,
                        )

                        progress.progress(80, text="Formatting insights...")
                        time.sleep(0.2)

                        elapsed = time.time() - start
                        st.session_state.summary = summary
                        st.session_state.analysis_time = elapsed

                        st.session_state.history.append({
                            "file": st.session_state.file_name,
                            "mode": analysis_mode,
                            "time": round(elapsed, 2),
                        })

                        progress.progress(100, text="Analysis complete!")
                        time.sleep(0.3)
                        progress.empty()
                        st.rerun()

                    except Exception as exc:
                        progress.empty()
                        st.error(f"AI analysis failed: {exc}")

        if st.session_state.summary:
            st.success(
                f"Analysis generated in {st.session_state.analysis_time:.1f} seconds."
            )

            st.markdown("---")
            st.markdown(st.session_state.summary)

            st.markdown("### 📥 Export")
            d1, d2 = st.columns(2)

            base = re.sub(
                r"[^A-Za-z0-9_-]+",
                "_",
                st.session_state.file_name.rsplit(".", 1)[0],
            )

            with d1:
                st.download_button(
                    "⬇️ Download TXT",
                    make_text_download(
                        st.session_state.summary,
                        st.session_state.file_name,
                    ),
                    file_name=f"{base}_AI_Analysis.txt",
                    mime="text/plain",
                    use_container_width=True,
                )

            with d2:
                st.download_button(
                    "⬇️ Download Markdown",
                    st.session_state.summary,
                    file_name=f"{base}_AI_Analysis.md",
                    mime="text/markdown",
                    use_container_width=True,
                )

    with tab3:
        st.caption("Search for a word or phrase inside the extracted paper.")
        query = st.text_input(
            "Search",
            placeholder="e.g. transformer, dataset, accuracy, methodology...",
        )

        if query:
            lower_text = paper_text.lower()
            matches = [m.start() for m in re.finditer(re.escape(query.lower()), lower_text)]

            if matches:
                st.success(f"Found {len(matches)} match(es).")
                for i, pos in enumerate(matches[:10], 1):
                    start = max(0, pos - 180)
                    end = min(len(paper_text), pos + len(query) + 260)
                    snippet = paper_text[start:end].replace("\n", " ")
                    st.markdown(f"**Match {i}:** …{snippet}…")
            else:
                st.info("No matches found in the extracted text.")

    # ========================================================
    # HISTORY
    # ========================================================
    if st.session_state.history:
        st.markdown('<div class="section">🕘 Session History</div>', unsafe_allow_html=True)
        history_rows = []
        for item in st.session_state.history[-5:][::-1]:
            history_rows.append(
                f"**{item['file']}** — {item['mode']} — {item['time']}s"
            )
        for row in history_rows:
            st.markdown(f"- {row}")

else:
    st.info("👆 Upload a research paper PDF to start the AI analysis.")

    st.markdown('<div class="section">🚀 Why ResearchLens AI?</div>', unsafe_allow_html=True)
    a, b, c = st.columns(3)

    landing = [
        ("⚡ Faster Research", "Convert long papers into structured insights in seconds."),
        ("🎓 Academic Friendly", "Keep the original technical terminology while simplifying explanations."),
        ("💼 Resume Ready", "Demonstrates document processing, LLM integration, UI design, and Python development."),
    ]

    for col, (title, text) in zip([a, b, c], landing):
        with col:
            st.markdown(
                f'<div class="card"><h3>{title}</h3><p>{text}</p></div>',
                unsafe_allow_html=True,
            )

# ============================================================
# FOOTER
# ============================================================
st.markdown("""
<div class="footer">
    <strong>ResearchLens AI</strong> · Built with Python, Streamlit,
    PyMuPDF & Google Gemini AI<br>
    Developed by <strong>Manasi Dewalkar</strong>
</div>
""", unsafe_allow_html=True)
