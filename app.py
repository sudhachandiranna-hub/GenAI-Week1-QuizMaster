"""
GenAI Training Program — Quiz Dashboard
----------------------------------------
A guided, story-driven quiz experience for the 5-day GenAI training
curriculum. Inspired by Kahoot / Slido: one question at a time, click an
answer to advance, a trophy finale, and a leaderboard right after.

FLOW (linear — no manual topic picking):
    entry -> intro -> [question x10] -> chapter_recap -> ... (x5 chapters)
    -> celebration (trophy + score + leaderboard, all on one screen)

NOTE ON THE EMAIL FIELD: this is not a login. There's no password and no
verification. It exists purely so each participant has a unique ID on the
leaderboard — two people can both enter the display name "Dave" and still
be tracked separately because their emails differ.

Google Sheets is required: this app always saves attempts there, no local
fallback mode. See README.md for one-time setup.
"""

import json
import random
import re
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

# --------------------------------------------------------------------------
# Page config
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="GenAI Training Quiz",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="auto",
)

QUESTIONS_PATH = Path(__file__).parent / "questions.json"
SHEET_TAB_NAME = "Leaderboard"
SHEET_HEADERS = [
    "timestamp", "email", "name", "topic_id", "topic_name", "score", "total", "percentage"
]

OPTION_SWATCHES = ["🟥", "🟦", "🟨", "🟩"]
OPTION_LETTERS = ["A", "B", "C", "D"]

TIERS = [
    (90, "🏆", "AI Grandmaster", "Top-tier mastery — you clearly absorbed all five days."),
    (75, "🥇", "AI Master", "Excellent grasp of the material across the board."),
    (60, "🥈", "AI Practitioner", "Solid foundation — one more pass and you're golden."),
    (40, "🥉", "AI Explorer", "You're on your way — worth revisiting the trickier chapters."),
    (0, "🌱", "AI Beginner", "A start. Spend a bit more time with the material and retake it."),
]

# --------------------------------------------------------------------------
# Styling — premium / elegant, Kahoot energy with Slido restraint
# --------------------------------------------------------------------------
def inject_style():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700;800&family=Inter:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] { font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif; }
        h1, h2, h3 { font-family: 'Poppins', 'Inter', sans-serif !important; }

        .stApp { background: #f7f8fc; }
        .block-container { padding-top: 2.2rem; padding-bottom: 3rem; max-width: 760px; }

        /* ---- Hero banner ---- */
        .hero {
            background: linear-gradient(135deg, #4338CA 0%, #7C3AED 55%, #DB2777 100%);
            border-radius: 20px;
            padding: 2.2rem 2rem;
            color: #fff;
            margin-bottom: 1.6rem;
            box-shadow: 0 12px 28px rgba(79, 70, 229, 0.25);
        }
        .hero h1 { color: #fff !important; margin: 0 0 0.3rem 0; font-size: 1.9rem; }
        .hero p { color: rgba(255,255,255,0.88); margin: 0; font-size: 1rem; }

        /* ---- Cards ---- */
        .card {
            background: #fff;
            border: 1px solid #ECEEF5;
            border-radius: 18px;
            padding: 1.6rem 1.8rem;
            margin-bottom: 1.1rem;
            box-shadow: 0 1px 2px rgba(16,24,40,0.04), 0 8px 20px rgba(16,24,40,0.04);
        }

        /* ---- Chapter roadmap (intro) ---- */
        .roadmap { display: flex; gap: 0.6rem; flex-wrap: wrap; margin: 1rem 0 0.4rem 0; }
        .roadmap-chip {
            flex: 1 1 0;
            min-width: 110px;
            background: #F5F3FF;
            border: 1px solid #E4DEFC;
            border-radius: 14px;
            padding: 0.8rem 0.7rem;
            text-align: center;
        }
        .roadmap-chip .num { font-weight: 800; color: #7C3AED; font-size: 0.78rem; letter-spacing: 0.04em; }
        .roadmap-chip .name { font-size: 0.85rem; font-weight: 600; color: #312E81; margin-top: 0.15rem; }

        /* ---- Chapter progress dots ---- */
        .chapter-dots { display: flex; align-items: center; justify-content: center; gap: 0.5rem; margin-bottom: 1.1rem; }
        .dot {
            width: 34px; height: 34px; border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-size: 0.82rem; font-weight: 700;
            border: 2px solid #E2E0F5; color: #9C9AB8; background: #fff;
            transition: all .2s ease;
        }
        .dot-done { background: #10B981; border-color: #10B981; color: #fff; }
        .dot-current {
            background: linear-gradient(135deg, #4338CA, #7C3AED);
            border-color: transparent; color: #fff;
            transform: scale(1.18);
            box-shadow: 0 4px 10px rgba(124,58,237,0.35);
        }

        /* ---- Progress bar accent ---- */
        div[data-testid="stProgress"] > div > div > div { background: linear-gradient(90deg, #4338CA, #DB2777) !important; }

        /* ---- Difficulty badges ---- */
        .badge { display: inline-block; padding: 0.2rem 0.65rem; border-radius: 999px; font-size: 0.7rem; font-weight: 700; letter-spacing: 0.04em; color: #fff; text-transform: uppercase; margin-bottom: 0.7rem; }
        .badge-easy { background: #10B981; }
        .badge-medium { background: #F59E0B; }
        .badge-hard { background: #EF4444; }

        .question-text { font-size: 1.28rem; font-weight: 700; color: #1E1B3A; line-height: 1.45; margin-bottom: 1.1rem; }

        /* ---- Buttons, globally ---- */
        .stButton > button {
            border-radius: 12px;
            font-weight: 600;
            padding: 0.65rem 1.1rem;
            border: 1.5px solid #E5E3F5;
            transition: all .15s ease;
        }
        .stButton > button:hover { border-color: #7C3AED; color: #7C3AED; transform: translateY(-1px); box-shadow: 0 4px 10px rgba(124,58,237,0.12); }
        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #4338CA, #7C3AED);
            border: none; color: #fff;
        }
        .stButton > button[kind="primary"]:hover { color: #fff; opacity: 0.92; box-shadow: 0 6px 16px rgba(124,58,237,0.32); }

        /* ---- Score displays ---- */
        .score-mega {
            font-size: 3.4rem; font-weight: 800; text-align: center;
            background: linear-gradient(135deg, #4338CA, #DB2777);
            -webkit-background-clip: text; background-clip: text; color: transparent;
            margin: 0.2rem 0;
        }
        .score-big { font-size: 2.2rem; font-weight: 800; color: #312E81; }
        .tier-row { display: flex; align-items: center; justify-content: center; gap: 0.6rem; margin-bottom: 0.3rem; }
        .tier-emoji { font-size: 2.6rem; }
        .tier-label { font-size: 1.3rem; font-weight: 800; color: #312E81; }

        /* ---- Chapter breakdown grid (celebration) ---- */
        .breakdown-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 0.6rem; margin: 1.2rem 0; }
        .breakdown-tile { background: #F8F7FF; border: 1px solid #ECE9FB; border-radius: 12px; padding: 0.7rem 0.4rem; text-align: center; }
        .breakdown-tile .bt-score { font-weight: 800; color: #4338CA; font-size: 1.05rem; }
        .breakdown-tile .bt-name { font-size: 0.68rem; color: #6B7280; margin-top: 0.15rem; line-height: 1.2; }

        /* ---- Confetti (CSS-only) ---- */
        .confetti-box { position: relative; height: 130px; overflow: hidden; }
        .confetti { position: absolute; top: -24px; font-size: 1.5rem; animation-name: fall; animation-timing-function: linear; animation-iteration-count: infinite; }
        @keyframes fall {
            0%   { transform: translateY(-24px) rotate(0deg); opacity: 1; }
            100% { transform: translateY(150px) rotate(360deg); opacity: 0.15; }
        }

        /* ---- Rank styling on leaderboard ---- */
        .rank-1 { color: #B8860B; font-weight: 800; }
        .rank-2 { color: #707070; font-weight: 800; }
        .rank-3 { color: #8C5A2B; font-weight: 800; }
        .you-rank {
            background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 14px;
            padding: 0.9rem 1.2rem; margin-bottom: 1rem; font-weight: 600; color: #166534;
        }

        .muted { color: #6B7280; font-size: 0.92rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def confetti_html(n=22):
    emojis = ["🎉", "✨", "🎊", "⭐", "💫"]
    pieces = []
    for _ in range(n):
        left = random.randint(0, 96)
        duration = round(random.uniform(2.2, 4.2), 2)
        delay = round(random.uniform(0, 2.4), 2)
        emoji = random.choice(emojis)
        pieces.append(
            f'<span class="confetti" style="left:{left}%; '
            f'animation-duration:{duration}s; animation-delay:{delay}s;">{emoji}</span>'
        )
    return '<div class="confetti-box">' + "".join(pieces) + "</div>"


# --------------------------------------------------------------------------
# Question bank
# --------------------------------------------------------------------------
@st.cache_data
def load_topics():
    with open(QUESTIONS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["topics"]


def total_question_count(topics):
    return sum(len(t["questions"]) for t in topics)


# --------------------------------------------------------------------------
# Pure logic (kept Streamlit-free so it's independently testable)
# --------------------------------------------------------------------------
def score_chapter(questions, responses):
    """responses: dict of question_id -> chosen option text."""
    return sum(1 for q in questions if responses.get(q["id"]) == q["answer"])


def get_tier(pct):
    for threshold, emoji, label, blurb in TIERS:
        if pct >= threshold:
            return emoji, label, blurb
    return TIERS[-1][1], TIERS[-1][2], TIERS[-1][3]


def chapter_dots_html(topics, current_idx, completed_count):
    dots = []
    for i, t in enumerate(topics):
        if i < completed_count:
            cls, label = "dot dot-done", "✓"
        elif i == current_idx:
            cls, label = "dot dot-current", str(i + 1)
        else:
            cls, label = "dot", str(i + 1)
        dots.append(f'<div class="{cls}" title="{t["name"]}">{label}</div>')
    return '<div class="chapter-dots">' + "".join(dots) + "</div>"


# --------------------------------------------------------------------------
# Google Sheets backend (required — this app always saves to Sheets)
# --------------------------------------------------------------------------
def _sheets_configured():
    try:
        return "gcp_service_account" in st.secrets and "sheet_id" in st.secrets
    except Exception:
        return False


@st.cache_resource(show_spinner=False)
def _get_worksheet():
    """Connect to the configured Google Sheet and return the worksheet,
    creating the header row if the sheet is empty."""
    import gspread
    from google.oauth2.service_account import Credentials

    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(st.secrets["sheet_id"])

    try:
        ws = spreadsheet.worksheet(SHEET_TAB_NAME)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=SHEET_TAB_NAME, rows=1000, cols=len(SHEET_HEADERS))
        ws.append_row(SHEET_HEADERS)

    if not ws.get_all_values():
        ws.append_row(SHEET_HEADERS)

    return ws


def save_attempt(email, name, topic_id, topic_name, score, total):
    """Append one quiz attempt (one chapter) to the Google Sheet."""
    row = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "email": email,
        "name": name,
        "topic_id": topic_id,
        "topic_name": topic_name,
        "score": score,
        "total": total,
        "percentage": round(100 * score / total, 1),
    }
    ws = _get_worksheet()
    ws.append_row([row[h] for h in SHEET_HEADERS])
    fetch_leaderboard_df.clear()


@st.cache_data(ttl=30, show_spinner=False)
def fetch_leaderboard_df():
    ws = _get_worksheet()
    records = ws.get_all_records()
    df = pd.DataFrame(records)
    if df.empty:
        return pd.DataFrame(columns=SHEET_HEADERS)
    for col in ("score", "total", "percentage"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


# --------------------------------------------------------------------------
# Session state helpers
# --------------------------------------------------------------------------
def init_state():
    defaults = {
        "page": "entry",
        "email": None,
        "name": None,
        "chapter_idx": 0,
        "question_idx": 0,
        "chapter_responses": {},
        "last_chapter_result": None,
        "chapter_results": [],
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)


def reset_journey():
    st.session_state.chapter_idx = 0
    st.session_state.question_idx = 0
    st.session_state.chapter_responses = {}
    st.session_state.last_chapter_result = None
    st.session_state.chapter_results = []


def go(page):
    st.session_state.page = page


def is_valid_email(email):
    return re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email or "") is not None


def render_question_text(question_text):
    """Questions with embedded code keep their line breaks via st.code,
    instead of collapsing onto one line under plain markdown."""
    if "\n" in question_text:
        first, rest = question_text.split("\n", 1)
        st.markdown(f'<div class="question-text">{first}</div>', unsafe_allow_html=True)
        st.code(rest, language="python")
    else:
        st.markdown(f'<div class="question-text">{question_text}</div>', unsafe_allow_html=True)


# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------
def render_entry():
    st.markdown(
        """
        <div class="hero">
            <h1>🧠 GenAI Training Program</h1>
            <p>A 5-chapter quiz quest covering your full week-one curriculum.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not _sheets_configured():
        st.error(
            "Google Sheets isn't configured yet — this app needs it to save "
            "results. Add your service-account credentials to "
            "`.streamlit/secrets.toml` (see README.md), then reload.",
            icon="🚫",
        )
        st.stop()

    st.markdown('<div class="card">', unsafe_allow_html=True)
    with st.form("entry_form"):
        st.markdown("**Enter your details to begin**")
        email = st.text_input("Email address", placeholder="you@example.com")
        name = st.text_input("Display name (optional — shown on the leaderboard)")
        submitted = st.form_submit_button("Begin Your Journey →", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if submitted:
        if not is_valid_email(email):
            st.error("Enter a valid email address to continue.")
        else:
            st.session_state.email = email.strip().lower()
            st.session_state.name = name.strip() if name.strip() else email.split("@")[0]
            reset_journey()
            go("intro")
            st.rerun()

    st.caption(
        "Email just keeps participants unique on the leaderboard (two people "
        "can both type \"Dave\" and still be tracked separately) — there's no "
        "password or verification."
    )


def render_intro():
    topics = load_topics()
    n_questions = total_question_count(topics)

    st.markdown(
        f"""
        <div class="hero">
            <h1>Welcome, {st.session_state.name} 👋</h1>
            <p>Your journey has {len(topics)} chapters and {n_questions} questions.
            Answer one question at a time — pick a tile and you're straight on to the next.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    chips = "".join(
        f'<div class="roadmap-chip"><div class="num">CHAPTER {i + 1}</div>'
        f'<div class="name">{t["name"]}</div></div>'
        for i, t in enumerate(topics)
    )
    st.markdown(f'<div class="card"><div class="roadmap">{chips}</div></div>', unsafe_allow_html=True)

    st.markdown(
        '<p class="muted">No need to pick a chapter — they run in order, '
        'and you\'ll land on a trophy screen with your full results at the end.</p>',
        unsafe_allow_html=True,
    )

    if st.button("Begin Chapter 1 →", type="primary", use_container_width=True):
        go("question")
        st.rerun()


def render_question():
    topics = load_topics()
    chapter_idx = st.session_state.chapter_idx
    question_idx = st.session_state.question_idx
    topic = topics[chapter_idx]
    q = topic["questions"][question_idx]

    n_total = total_question_count(topics)
    overall_done = sum(len(topics[i]["questions"]) for i in range(chapter_idx)) + question_idx
    st.progress(min(int(100 * overall_done / n_total), 100))

    st.markdown(chapter_dots_html(topics, chapter_idx, chapter_idx), unsafe_allow_html=True)
    st.markdown(
        f'<p style="text-align:center;" class="muted">'
        f'Chapter {chapter_idx + 1} of {len(topics)} · {topic["name"]} &nbsp;—&nbsp; '
        f'Question {question_idx + 1} of {len(topic["questions"])}</p>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="card">', unsafe_allow_html=True)
    badge_cls = f"badge badge-{q['difficulty']}"
    st.markdown(f'<span class="{badge_cls}">{q["difficulty"]}</span>', unsafe_allow_html=True)
    render_question_text(q["question"])

    cols = st.columns(2)
    clicked_option = None
    for i, option in enumerate(q["options"]):
        with cols[i % 2]:
            label = f"{OPTION_SWATCHES[i]} {OPTION_LETTERS[i]}.  {option}"
            if st.button(label, key=f"opt_{topic['id']}_{q['id']}_{i}", use_container_width=True):
                clicked_option = option
    st.markdown("</div>", unsafe_allow_html=True)

    if clicked_option is not None:
        st.session_state.chapter_responses[q["id"]] = clicked_option
        is_last_question = question_idx == len(topic["questions"]) - 1

        if not is_last_question:
            st.session_state.question_idx += 1
            st.rerun()
        else:
            score = score_chapter(topic["questions"], st.session_state.chapter_responses)
            total = len(topic["questions"])
            save_attempt(
                email=st.session_state.email,
                name=st.session_state.name,
                topic_id=topic["id"],
                topic_name=topic["name"],
                score=score,
                total=total,
            )
            st.session_state.last_chapter_result = {
                "topic": topic,
                "responses": dict(st.session_state.chapter_responses),
                "score": score,
                "total": total,
            }
            st.session_state.chapter_results.append(
                {"topic_id": topic["id"], "topic_name": topic["name"], "score": score, "total": total}
            )
            st.session_state.chapter_responses = {}
            st.session_state.question_idx = 0

            is_last_chapter = chapter_idx == len(topics) - 1
            if is_last_chapter:
                go("celebration")
            else:
                st.session_state.chapter_idx += 1
                go("chapter_recap")
            st.rerun()


def render_chapter_recap():
    result = st.session_state.last_chapter_result
    if not result:
        go("question")
        st.rerun()
        return

    topic = result["topic"]
    score, total = result["score"], result["total"]
    pct = round(100 * score / total)
    emoji, label, blurb = get_tier(pct)

    topics = load_topics()
    next_idx = st.session_state.chapter_idx
    next_topic = topics[next_idx]

    st.markdown(
        f"""
        <div class="hero">
            <h1>Chapter complete ✅</h1>
            <p>{topic["name"]}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="card" style="text-align:center;">', unsafe_allow_html=True)
    st.markdown(f'<div class="score-big" style="text-align:center;">{score} / {total}</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="tier-row"><span class="tier-emoji">{emoji}</span>'
        f'<span class="tier-label">{label}</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(f'<p class="muted">{blurb}</p>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("Review your answers"):
        for q in topic["questions"]:
            given = result["responses"].get(q["id"])
            correct = q["answer"]
            ok = given == correct
            st.markdown(("✅ " if ok else "❌ ") + f"**{q['question'].splitlines()[0]}**")
            st.caption(f"Your answer: {given}")
            if not ok:
                st.caption(f"Correct answer: {correct}")

    st.markdown(f"Up next — **Chapter {next_idx + 1}: {next_topic['name']}**")
    if st.button(f"Continue to Chapter {next_idx + 1} →", type="primary", use_container_width=True):
        go("question")
        st.rerun()


def render_leaderboard_section():
    df = fetch_leaderboard_df()

    if df.empty:
        st.info("No attempts recorded yet — you're the first through the journey.")
        return

    best = df.groupby(["email", "name", "topic_id"])["score"].max().reset_index()
    overall = (
        best.groupby(["email", "name"])
        .agg(total_score=("score", "sum"), chapters_completed=("topic_id", "nunique"))
        .reset_index()
        .sort_values(["total_score", "chapters_completed"], ascending=False)
        .reset_index(drop=True)
    )
    overall.index += 1
    overall.insert(0, "Rank", overall.index)

    my_row = overall[overall["email"] == st.session_state.get("email")]
    if not my_row.empty:
        my_rank = int(my_row.iloc[0]["Rank"])
        my_score = int(my_row.iloc[0]["total_score"])
        st.markdown(
            f'<div class="you-rank">🎯 You\'re ranked <strong>#{my_rank}</strong> '
            f'out of {len(overall)} with a total score of <strong>{my_score}</strong>.</div>',
            unsafe_allow_html=True,
        )

    topics = load_topics()
    topic_names = {t["id"]: t["name"] for t in topics}

    tab_overall, tab_topic = st.tabs(["🏆 Overall", "📚 By chapter"])

    with tab_overall:
        display = overall.rename(columns={
            "name": "Name", "email": "Email",
            "total_score": "Total score (best per chapter)",
            "chapters_completed": "Chapters completed",
        })
        st.dataframe(display, use_container_width=True, hide_index=True)

    with tab_topic:
        chosen = st.selectbox("Chapter", options=list(topic_names.values()))
        chosen_id = [k for k, v in topic_names.items() if v == chosen][0]
        sub = df[df["topic_id"] == chosen_id]
        if sub.empty:
            st.info("No attempts for this chapter yet.")
        else:
            best_topic = (
                sub.groupby(["email", "name"])["score"]
                .max()
                .reset_index()
                .sort_values("score", ascending=False)
                .reset_index(drop=True)
            )
            best_topic.index += 1
            best_topic.insert(0, "Rank", best_topic.index)
            best_topic = best_topic.rename(columns={"name": "Name", "email": "Email", "score": "Best score"})
            st.dataframe(best_topic, use_container_width=True, hide_index=True)


def render_celebration():
    results = st.session_state.chapter_results
    if not results:
        go("intro")
        st.rerun()
        return

    total_score = sum(r["score"] for r in results)
    total_total = sum(r["total"] for r in results)
    pct = round(100 * total_score / total_total) if total_total else 0
    emoji, label, blurb = get_tier(pct)

    st.markdown(confetti_html(), unsafe_allow_html=True)
    st.markdown(
        f"""
        <div style="text-align:center;">
            <div style="font-size:3.4rem;">🏆</div>
            <h1 style="margin-bottom:0;">Journey complete, {st.session_state.name}!</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="card" style="text-align:center;">', unsafe_allow_html=True)
    st.markdown(f'<div class="score-mega">{total_score} / {total_total}</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="tier-row"><span class="tier-emoji">{emoji}</span>'
        f'<span class="tier-label">{label}</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(f'<p class="muted">{blurb} You scored {pct}% across all chapters.</p>', unsafe_allow_html=True)

    tiles = "".join(
        f'<div class="breakdown-tile"><div class="bt-score">{r["score"]}/{r["total"]}</div>'
        f'<div class="bt-name">{r["topic_name"]}</div></div>'
        for r in results
    )
    st.markdown(f'<div class="breakdown-grid">{tiles}</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("## 🏅 Leaderboard")
    st.caption("Live, straight from the shared Google Sheet — see where you landed.")
    render_leaderboard_section()

    st.divider()
    if st.button("Switch participant — let someone else play", use_container_width=True):
        for k in ("email", "name", "last_chapter_result"):
            st.session_state[k] = None
        reset_journey()
        go("entry")
        st.rerun()


def render_sidebar():
    with st.sidebar:
        st.markdown(f"**{st.session_state.name}**")
        st.caption(st.session_state.email)
        st.divider()
        if st.session_state.page in ("celebration",):
            if st.button("Leaderboard", use_container_width=True):
                go("leaderboard")
                st.rerun()
        st.caption("This is a one-way journey — chapters run in order, no skipping around.")
        st.divider()
        if st.button("Switch participant", use_container_width=True):
            for k in ("email", "name", "last_chapter_result"):
                st.session_state[k] = None
            reset_journey()
            go("entry")
            st.rerun()


def render_leaderboard():
    st.title("🏅 Leaderboard")
    render_leaderboard_section()


# --------------------------------------------------------------------------
# Router
# --------------------------------------------------------------------------
def main():
    init_state()
    inject_style()

    if st.session_state.page == "entry" or not st.session_state.email:
        render_entry()
        return

    render_sidebar()

    page = st.session_state.page
    if page == "intro":
        render_intro()
    elif page == "question":
        render_question()
    elif page == "chapter_recap":
        render_chapter_recap()
    elif page == "celebration":
        render_celebration()
    elif page == "leaderboard":
        render_leaderboard()
    else:
        render_intro()


if __name__ == "__main__":
    main()
