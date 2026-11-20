"""ResumeIQ - AI Resume Analyzer (Streamlit + Groq free tier). No database."""
import html
import os
import uuid
from datetime import date

import streamlit as st

from analyzer import DEFAULT_MODEL, MAX_JD_CHARS, MAX_UPLOAD_MB, UserError, analyze_with_groq, extract_resume_text
from limiter import UsageLimiter

st.set_page_config(page_title="ResumeIQ · AI Resume Analyzer", page_icon="📄", layout="wide")


# --------------------------------------------------------------------------- #
# Config (Streamlit secrets first, then environment variables)
# --------------------------------------------------------------------------- #
def get_setting(name: str, default: str = "") -> str:
    try:
        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:  # no secrets file configured
        pass
    return os.environ.get(name, default)


API_KEY = get_setting("GROQ_API_KEY")
MODEL = get_setting("GROQ_MODEL", DEFAULT_MODEL)
MAX_ANALYSES = int(get_setting("MAX_ANALYSES", "10"))


@st.cache_resource
def get_limiter(limit: int) -> UsageLimiter:
    """One limiter shared by every session of this app process."""
    return UsageLimiter(limit)


limiter = get_limiter(MAX_ANALYSES)


def client_key() -> str:
    """Identify the visitor by IP (X-Forwarded-For on Streamlit Cloud).

    Falls back to a per-session id when headers aren't available (e.g. local runs).
    """
    try:
        xff = st.context.headers.get("X-Forwarded-For", "")
        if xff:
            return "ip:" + xff.split(",")[0].strip()
    except Exception:
        pass
    if "sid" not in st.session_state:
        st.session_state["sid"] = uuid.uuid4().hex
    return "sid:" + st.session_state["sid"]


KEY = client_key()
remaining = limiter.remaining(KEY)

st.session_state.setdefault("result", None)
st.session_state.setdefault("history", [])

# --------------------------------------------------------------------------- #
# Styling
# --------------------------------------------------------------------------- #
CSS = """
<style>
:root{--bg:#0b0b0d;--panel:#111114;--panel2:#17171c;--border:#25252c;--text:#f4f4f6;--muted:#8a8a96;
--purple:#8b5cf6;--purple2:#a78bfa;--green:#34d399;--red:#f87171;--amber:#fbbf24;}
.stApp{background:radial-gradient(1200px 500px at 70% -10%,rgba(139,92,246,.12),transparent 60%),#0b0b0d;color:var(--text);}
[data-testid="stHeader"]{background:transparent;}
#MainMenu,footer{visibility:hidden;}
.block-container{padding-top:2rem;max-width:1200px;}
[data-testid="stSidebar"]{background:#0e0e11;border-right:1px solid var(--border);}
[data-testid="stSidebar"] .block-container{padding-top:1.5rem;}

.brand{display:flex;align-items:center;gap:10px;font-weight:700;font-size:19px;margin-bottom:18px;}
.logo{width:26px;height:26px;border-radius:50%;background:conic-gradient(from 210deg,#8b5cf6,#c4b5fd,#8b5cf6);
box-shadow:0 0 22px rgba(139,92,246,.55);position:relative;display:inline-block;}
.logo:after{content:"";position:absolute;inset:7px;border-radius:50%;background:#0e0e11;}
.usage-card{padding:16px;border-radius:14px;background:linear-gradient(160deg,#1b1233,#141418);border:1px solid #2b2150;margin-bottom:16px;}
.usage-top{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:10px;font-weight:600;}
.usage-top span{color:var(--muted);font-size:12px;font-weight:400;}
.usage-top b{color:var(--purple2);font-size:15px;}
.bar{height:6px;border-radius:99px;background:#26262e;overflow:hidden;}
.bar i{display:block;height:100%;border-radius:inherit;background:linear-gradient(90deg,#8b5cf6,#c4b5fd);}
.bar.low i{background:linear-gradient(90deg,#fbbf24,#f87171);}
.note{color:var(--muted);font-size:12px;margin-top:10px;}
.how{color:#cfcfd8;font-size:13px;line-height:1.7;}
.how b{color:var(--text);}

.page-title{font-size:28px;font-weight:700;letter-spacing:-.02em;margin:0;}
.page-sub{color:var(--muted);margin:4px 0 18px;}

.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:22px;}
.stat{background:var(--panel);border:1px solid var(--border);border-radius:16px;padding:18px;}
.stat.featured{background:linear-gradient(165deg,#8b5cf6 0%,#4c2a9a 45%,#1a1230 100%);border-color:#6d44d9;}
.sicon{width:34px;height:34px;border-radius:10px;display:grid;place-items:center;background:rgba(255,255,255,.1);
color:#fff;margin-bottom:16px;font-weight:700;}
.sicon.g{color:var(--green);background:rgba(52,211,153,.12);}
.sicon.r{color:var(--red);background:rgba(248,113,113,.12);}
.sicon.a{color:var(--amber);background:rgba(251,191,36,.12);}
.slabel{color:var(--muted);font-size:12px;}
.sval{font-size:30px;font-weight:700;letter-spacing:-.02em;margin:2px 0;}
.sval small{font-size:14px;font-weight:500;opacity:.7;margin-left:2px;}
.sfoot{color:var(--muted);font-size:12px;}
.stat.featured .slabel,.stat.featured .sfoot{color:rgba(255,255,255,.78);}

[data-testid="stForm"]{background:var(--panel);border:1px solid var(--border);border-radius:16px;padding:20px;}
[data-testid="stFileUploaderDropzone"]{background:var(--panel2);border:1.5px dashed #34343e;border-radius:14px;min-height:150px;}
[data-testid="stFileUploaderDropzone"]:hover{border-color:#8b5cf6;}
.stTextArea textarea{background:var(--panel2)!important;border:1px solid var(--border)!important;border-radius:14px!important;color:var(--text)!important;}
.stTextArea textarea:focus{border-color:#8b5cf6!important;box-shadow:0 0 0 3px rgba(139,92,246,.15)!important;}
.stFormSubmitButton{width:100%;}
.stFormSubmitButton button{width:100%;border:0;border-radius:12px;padding:.7rem 1rem;font-weight:600;color:#fff;
background:linear-gradient(135deg,#8b5cf6,#6d44d9);box-shadow:0 8px 24px rgba(139,92,246,.35);}
.stFormSubmitButton button:hover{color:#fff;filter:brightness(1.08);}
.stFormSubmitButton button:disabled{opacity:.5;}

.card{background:var(--panel);border:1px solid var(--border);border-radius:16px;padding:20px;margin-bottom:16px;}
.card h3{font-size:14px;font-weight:600;margin:0 0 14px;}
.score-card{display:flex;align-items:center;gap:26px;background:linear-gradient(135deg,#1a1230,#111114 60%);}
.ring{width:120px;height:120px;border-radius:50%;flex:none;display:grid;place-items:center;}
.ring-in{width:98px;height:98px;border-radius:50%;background:#111114;display:flex;flex-direction:column;align-items:center;justify-content:center;}
.ring-in b{font-size:30px;line-height:1;}
.ring-in span{font-size:11px;color:var(--muted);margin-top:2px;}
.score-card p{color:#c9c9d2;margin:6px 0 0;}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px;}
.chips{display:flex;flex-wrap:wrap;gap:8px;}
.chip{padding:5px 11px;border-radius:99px;font-size:12px;font-weight:500;border:1px solid;}
.chips.g .chip{color:var(--green);background:rgba(52,211,153,.09);border-color:rgba(52,211,153,.3);}
.chips.r .chip{color:var(--red);background:rgba(248,113,113,.09);border-color:rgba(248,113,113,.3);}
.none{color:var(--muted);font-size:13px;}
.list{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:10px;}
.list li{position:relative;padding-left:20px;color:#d4d4dc;}
.list li:before{content:"";position:absolute;left:2px;top:8px;width:7px;height:7px;border-radius:50%;background:#8b5cf6;}
table.hist{width:100%;border-collapse:collapse;font-size:13px;}
table.hist th{text-align:left;color:var(--muted);font-weight:500;font-size:12px;padding:10px 12px;border-bottom:1px solid var(--border);}
table.hist td{padding:12px;border-bottom:1px solid #1c1c22;}
.badge{padding:3px 10px;border-radius:99px;font-size:11px;font-weight:600;}
.badge.good{color:var(--green);background:rgba(52,211,153,.12);}
.badge.ok{color:var(--amber);background:rgba(251,191,36,.12);}
.badge.low{color:var(--red);background:rgba(248,113,113,.12);}
@media(max-width:1000px){.stats{grid-template-columns:repeat(2,1fr);}}
@media(max-width:760px){.grid2{grid-template-columns:1fr;}.score-card{flex-direction:column;text-align:center;}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
# HTML helpers (everything from the model/user goes through html.escape)
# --------------------------------------------------------------------------- #
def esc(x) -> str:
    return html.escape(str(x), quote=True)


def verdict(score: int) -> str:
    return "Strong match" if score >= 80 else "Good match" if score >= 60 else "Partial match" if score >= 40 else "Weak match"


def tier(score: int) -> str:
    return "good" if score >= 70 else "ok" if score >= 45 else "low"


def ring_color(score: int) -> str:
    return "#8b5cf6" if score >= 70 else "#fbbf24" if score >= 45 else "#f87171"


def stat_cards_html(r) -> str:
    score = f"{r['match_score']}<small>/100</small>" if r else "—"
    foot = verdict(r["match_score"]) if r else "Run an analysis to see your score"
    matched = len(r["matched_skills"]) if r else "—"
    missing = len(r["missing_skills"]) if r else "—"
    tips = len(r["suggestions"]) if r else "—"
    return (
        '<div class="stats">'
        f'<div class="stat featured"><div class="sicon">★</div><div class="slabel">Match score</div><div class="sval">{score}</div><div class="sfoot">{esc(foot)}</div></div>'
        f'<div class="stat"><div class="sicon g">✓</div><div class="slabel">Matched skills</div><div class="sval">{matched}</div><div class="sfoot">Found in resume &amp; JD</div></div>'
        f'<div class="stat"><div class="sicon r">✕</div><div class="slabel">Missing skills</div><div class="sval">{missing}</div><div class="sfoot">Wanted by the role</div></div>'
        f'<div class="stat"><div class="sicon a">＋</div><div class="slabel">Suggestions</div><div class="sval">{tips}</div><div class="sfoot">Ways to improve</div></div>'
        "</div>"
    )


def chips_html(items, cls) -> str:
    if not items:
        return '<span class="none">Nothing to show.</span>'
    return f'<div class="chips {cls}">' + "".join(f'<span class="chip">{esc(i)}</span>' for i in items) + "</div>"


def list_html(items) -> str:
    if not items:
        return '<span class="none">Nothing to show.</span>'
    return '<ul class="list">' + "".join(f"<li>{esc(i)}</li>" for i in items) + "</ul>"


def results_html(r) -> str:
    s = r["match_score"]
    ring = f'<div class="ring" style="background:conic-gradient({ring_color(s)} {s}%,#26262e 0)"><div class="ring-in"><b>{s}</b><span>match</span></div></div>'
    return (
        f'<div class="card score-card">{ring}<div><h3 style="font-size:16px;margin:0">Overall verdict · {esc(verdict(s))}</h3>'
        f'<p>{esc(r["summary"] or "No summary returned.")}</p></div></div>'
        '<div class="grid2">'
        f'<div class="card"><h3>✅ Matched skills</h3>{chips_html(r["matched_skills"], "g")}</div>'
        f'<div class="card"><h3>❌ Missing skills</h3>{chips_html(r["missing_skills"], "r")}</div>'
        f'<div class="card"><h3>💪 Strengths</h3>{list_html(r["strengths"])}</div>'
        f'<div class="card"><h3>⚠️ Gaps</h3>{list_html(r["gaps"])}</div>'
        "</div>"
        f'<div class="card"><h3>📝 Suggestions to improve your resume</h3>{list_html(r["suggestions"])}</div>'
    )


def history_html(rows) -> str:
    body = "".join(
        f'<tr><td>{esc(h["name"])}</td><td>{esc(h["date"])}</td><td>{h["score"]}/100</td>'
        f'<td><span class="badge {tier(h["score"])}">{esc(verdict(h["score"]))}</span></td></tr>'
        for h in rows
    )
    return (
        '<div class="card"><h3>Recent analyses (this session)</h3><table class="hist"><thead><tr>'
        "<th>Resume</th><th>Date</th><th>Score</th><th>Status</th></tr></thead>"
        f"<tbody>{body}</tbody></table></div>"
    )


# --------------------------------------------------------------------------- #
# Sidebar
# --------------------------------------------------------------------------- #
with st.sidebar:
    pct = remaining / MAX_ANALYSES * 100 if MAX_ANALYSES else 0
    low = " low" if remaining <= 2 else ""
    st.markdown(
        '<div class="brand"><span class="logo"></span>ResumeIQ</div>'
        '<div class="usage-card"><div class="usage-top">Free analyses'
        f"<span><b>{remaining}</b> / {MAX_ANALYSES} left</span></div>"
        f'<div class="bar{low}"><i style="width:{pct:.0f}%"></i></div>'
        f'<div class="note">Each visitor gets {MAX_ANALYSES} free analyses.</div></div>'
        '<div class="how"><b>How it works</b><br>1. Upload a PDF or DOCX resume<br>2. Paste the job description<br>'
        "3. Click Analyze<br>4. Get a score + skill-gap breakdown<br><br>"
        '<span class="note">Files are processed in memory and never stored.</span></div>',
        unsafe_allow_html=True,
    )

# --------------------------------------------------------------------------- #
# Main page
# --------------------------------------------------------------------------- #
st.markdown(
    '<p class="page-title">Resume Analyzer</p>'
    '<p class="page-sub">Match your resume to any job description in seconds.</p>',
    unsafe_allow_html=True,
)
st.markdown(stat_cards_html(st.session_state["result"]), unsafe_allow_html=True)

with st.form("analyze_form", border=False):
    col_a, col_b = st.columns([1, 1.4])
    with col_a:
        resume = st.file_uploader("Resume (PDF or DOCX)", type=["pdf", "docx"], help=f"Up to {MAX_UPLOAD_MB} MB")
    with col_b:
        jd = st.text_area(
            "Job description",
            height=210,
            max_chars=MAX_JD_CHARS,
            placeholder="Paste the full job description here…",
        )
    submitted = st.form_submit_button("🔍  Analyze match", type="primary", disabled=remaining <= 0)

if remaining <= 0:
    st.warning(f"You've used all {MAX_ANALYSES} free analyses. Thanks for trying the app!")

if submitted:
    if not API_KEY:
        st.error("Server is missing GROQ_API_KEY. Add it in the app's Secrets settings.")
    elif resume is None:
        st.error("Please upload your resume (PDF or DOCX).")
    elif len(jd.strip()) < 50:
        st.error("Please paste a fuller job description (at least a few sentences).")
    elif not limiter.reserve(KEY):
        st.error(f"You've used all {MAX_ANALYSES} free analyses.")
    else:
        try:
            with st.spinner("Analyzing with AI… this can take up to 30 seconds"):
                text = extract_resume_text(resume.name, resume.getvalue())
                result = analyze_with_groq(API_KEY, text, jd, MODEL)
        except UserError as exc:
            limiter.refund(KEY)  # failed attempts don't count
            st.error(str(exc))
        except Exception:
            limiter.refund(KEY)
            st.error("Something unexpected went wrong. Please try again.")
        else:
            st.session_state["result"] = result
            st.session_state["history"] = (
                [{"name": resume.name, "date": date.today().strftime("%d %b %Y"), "score": result["match_score"]}]
                + st.session_state["history"]
            )[:8]
            st.rerun()  # refresh sidebar usage meter + stat cards

if st.session_state["result"]:
    st.markdown(results_html(st.session_state["result"]), unsafe_allow_html=True)

if st.session_state["history"]:
    st.markdown(history_html(st.session_state["history"]), unsafe_allow_html=True)

st.caption("Built with Streamlit & Groq.")
