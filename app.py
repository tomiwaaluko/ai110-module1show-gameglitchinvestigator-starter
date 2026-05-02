import random

import streamlit as st

from ai_coach import get_coaching
from guardrails import validate_game_state, validate_guess
from logger import log_game_end, log_game_start, log_guess, read_recent_events
from logic_utils import check_guess, get_range_for_difficulty, update_score


st.set_page_config(page_title="AI Game Intelligence System", page_icon="AI", layout="wide")


st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700;800&family=Geist+Mono:wght@400;500;600&display=swap');

    :root {
        --surface: #151a18;
        --surface-2: #1b211f;
        --background: #0d1110;
        --ink: #f4f7f5;
        --muted: #a5b0aa;
        --line: rgba(244, 247, 245, 0.13);
        --accent: #42b883;
        --accent-strong: #2d9c6f;
        --accent-soft: rgba(66, 184, 131, 0.14);
        --warn: #e0b15d;
        --danger: #ef766d;
    }

    .stApp {
        background:
            radial-gradient(circle at 84% 5%, rgba(66, 184, 131, 0.18), transparent 26rem),
            radial-gradient(circle at 18% 78%, rgba(66, 184, 131, 0.08), transparent 28rem),
            linear-gradient(135deg, #101513 0%, var(--background) 56%, #121816 100%);
        color: var(--ink);
        font-family: "Geist", "Satoshi", "Segoe UI", sans-serif;
    }

    .stApp,
    .stApp * {
        color-scheme: dark;
    }

    header[data-testid="stHeader"] {
        background: rgba(13, 17, 16, 0.92) !important;
        box-shadow: none;
    }

    header[data-testid="stHeader"]::before,
    header[data-testid="stHeader"]::after {
        background: transparent !important;
    }

    div[data-testid="stToolbar"],
    div[data-testid="stDecoration"],
    div[data-testid="stStatusWidget"],
    #MainMenu,
    footer {
        display: none;
    }

    .block-container {
        max-width: 1400px;
        padding: 3rem 2rem 4rem;
    }

    h1, h2, h3, p, label, div {
        letter-spacing: 0;
    }

    [data-testid="stSidebar"] {
        background: #111614;
        border-right: 1px solid var(--line);
    }

    [data-testid="stSidebar"] * {
        color: var(--ink);
    }

    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p {
        color: var(--ink);
    }

    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
        color: var(--muted);
        opacity: 1;
    }

    [data-testid="stSidebar"] hr {
        border-color: var(--line);
        opacity: 1;
    }

    .app-shell {
        display: grid;
        grid-template-columns: minmax(0, 1.55fr) minmax(360px, 0.95fr);
        gap: 2rem;
        align-items: start;
    }

    .eyebrow {
        color: var(--accent);
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 0.75rem;
    }

    .hero-title {
        max-width: 840px;
        color: var(--ink);
        font-size: clamp(2.4rem, 6vw, 5.8rem);
        line-height: 0.92;
        font-weight: 800;
        letter-spacing: -0.055em;
        margin: 0;
    }

    .hero-copy {
        max-width: 62ch;
        margin: 1.2rem 0 2rem;
        color: var(--muted);
        font-size: 1.02rem;
        line-height: 1.75;
    }

    .metric-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.75rem;
        margin: 1.6rem 0 2rem;
    }

    .metric {
        border-top: 1px solid var(--line);
        padding-top: 0.9rem;
    }

    .metric span {
        display: block;
        color: var(--muted);
        font-size: 0.74rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .metric strong {
        display: block;
        margin-top: 0.28rem;
        color: var(--ink);
        font-family: "Geist Mono", "JetBrains Mono", monospace;
        font-size: 1.65rem;
        font-weight: 600;
    }

    .panel {
        background: linear-gradient(180deg, rgba(27, 33, 31, 0.96), rgba(21, 26, 24, 0.94));
        border: 1px solid var(--line);
        border-radius: 24px;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.06), 0 24px 52px -32px rgba(0, 0, 0, 0.65);
        padding: 1.35rem;
    }

    .panel-intro {
        margin-top: 1rem;
        margin-bottom: 1rem;
    }

    .panel-title {
        color: var(--ink);
        font-size: 0.92rem;
        font-weight: 750;
        margin: 0 0 0.3rem;
    }

    .panel-copy {
        color: var(--muted);
        font-size: 0.92rem;
        line-height: 1.55;
        margin: 0;
    }

    .status-line {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        color: var(--muted);
        font-size: 0.88rem;
        margin-top: 1rem;
    }

    .status-dot {
        width: 0.65rem;
        height: 0.65rem;
        border-radius: 999px;
        background: var(--accent);
        box-shadow: 0 0 0 0 rgba(31, 143, 104, 0.35);
        animation: breathe 2.4s cubic-bezier(0.16, 1, 0.3, 1) infinite;
    }

    .range-track {
        position: relative;
        height: 12px;
        overflow: hidden;
        border-radius: 999px;
        background: #242b28;
        margin-top: 1.1rem;
    }

    .range-track::after {
        content: "";
        position: absolute;
        inset: 0;
        transform-origin: left center;
        transform: scaleX(var(--progress));
        background: linear-gradient(90deg, var(--accent-strong), var(--accent));
        border-radius: inherit;
    }

    .coach-tip {
        margin-top: 1rem;
        padding: 1rem 1.05rem;
        border-left: 4px solid var(--accent);
        background: var(--accent-soft);
        border-radius: 16px;
        color: #dff8ed;
        line-height: 1.65;
    }

    .empty-state {
        border: 1px dashed rgba(244, 247, 245, 0.22);
        border-radius: 18px;
        padding: 1.2rem;
        color: var(--muted);
        background: rgba(21, 26, 24, 0.64);
    }

    .history-row {
        display: grid;
        grid-template-columns: 56px 1fr;
        gap: 0.8rem;
        align-items: center;
        padding: 0.72rem 0;
        border-top: 1px solid var(--line);
    }

    .history-number {
        font-family: "Geist Mono", "JetBrains Mono", monospace;
        color: var(--ink);
        font-weight: 650;
    }

    .history-meta {
        color: var(--muted);
        font-size: 0.84rem;
    }

    .skeleton {
        position: relative;
        overflow: hidden;
        height: 92px;
        border-radius: 18px;
        background: #1d2421;
        border: 1px solid var(--line);
    }

    .skeleton::after {
        content: "";
        position: absolute;
        inset: 0;
        transform: translateX(-100%);
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.10), transparent);
        animation: shimmer 1.2s cubic-bezier(0.16, 1, 0.3, 1) infinite;
    }

    .stButton > button,
    .stFormSubmitButton > button {
        border-radius: 999px;
        border: 1px solid rgba(244, 247, 245, 0.13);
        background: var(--accent-strong);
        color: #f8fffb;
        font-weight: 700;
        transition: transform 0.22s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.22s cubic-bezier(0.16, 1, 0.3, 1), background 0.22s cubic-bezier(0.16, 1, 0.3, 1);
        box-shadow: 0 16px 34px -22px rgba(66, 184, 131, 0.8);
    }

    .stButton > button:hover,
    .stFormSubmitButton > button:hover {
        background: var(--accent);
        border-color: rgba(244, 247, 245, 0.22);
        color: #0d1110;
        transform: translateY(-1px);
    }

    .stButton > button:active,
    .stFormSubmitButton > button:active {
        transform: translateY(1px) scale(0.99);
    }

    [data-testid="stTextInput"] label,
    [data-testid="stSelectbox"] label {
        font-weight: 700;
        color: var(--ink);
    }

    [data-testid="stTextInput"] small,
    [data-testid="stTextInput"] p {
        color: var(--muted);
        opacity: 1;
    }

    [data-baseweb="input"] {
        border-radius: 18px;
        border-color: rgba(244, 247, 245, 0.15) !important;
        background: #151a18 !important;
        color: var(--ink) !important;
    }

    [data-baseweb="input"] input {
        background: #151a18 !important;
        color: var(--ink) !important;
        -webkit-text-fill-color: var(--ink);
        caret-color: var(--accent);
    }

    [data-baseweb="input"] input::placeholder {
        color: #8d9993;
        opacity: 1;
        -webkit-text-fill-color: #8d9993;
    }

    [data-baseweb="select"] > div {
        background: #151a18 !important;
        border-color: rgba(244, 247, 245, 0.15) !important;
        color: var(--ink) !important;
    }

    [data-baseweb="select"] span,
    [data-baseweb="select"] svg {
        color: var(--ink) !important;
        fill: var(--ink) !important;
    }

    [data-baseweb="popover"],
    [data-baseweb="menu"] {
        background: #151a18;
        color: var(--ink);
    }

    [data-baseweb="menu"] li,
    [role="option"] {
        background: #151a18;
        color: var(--ink);
    }

    [data-baseweb="menu"] li:hover,
    [role="option"]:hover {
        background: var(--accent-soft);
        color: var(--ink);
    }

    [data-testid="stToggle"] label,
    [data-testid="stToggle"] p {
        color: var(--ink);
        opacity: 1;
    }

    [data-testid="stToggle"] [role="switch"] {
        background: #2a322f;
    }

    [data-testid="stToggle"] [aria-checked="true"] {
        background: var(--accent);
    }

    div[data-testid="stAlert"] {
        border-radius: 18px;
        border: 1px solid var(--line);
    }

    @keyframes shimmer {
        100% { transform: translateX(100%); }
    }

    @keyframes breathe {
        70% { box-shadow: 0 0 0 12px rgba(31, 143, 104, 0); }
        100% { box-shadow: 0 0 0 0 rgba(31, 143, 104, 0); }
    }

    @media (max-width: 900px) {
        .block-container {
            padding: 1.25rem 1rem 2.5rem;
        }

        .app-shell {
            grid-template-columns: 1fr;
        }

        .metric-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


st.sidebar.markdown("## Control")

difficulty = st.sidebar.selectbox(
    "Difficulty",
    ["Easy", "Normal", "Hard"],
    index=1,
)

attempt_limit_map = {"Easy": 6, "Normal": 8, "Hard": 5}
attempt_limit = attempt_limit_map[difficulty]
low, high = get_range_for_difficulty(difficulty)

st.sidebar.caption(f"Range: {low} to {high}")
st.sidebar.caption(f"Attempt limit: {attempt_limit}")
st.sidebar.divider()
ai_coaching_enabled = st.sidebar.toggle("AI coaching", value=True)
show_reasoning = st.sidebar.toggle("Reasoning trace", value=False)
show_hint = st.sidebar.toggle("Direction hint", value=True)


def start_new_game() -> None:
    st.session_state.attempts = 0
    st.session_state.score = 0
    st.session_state.status = "playing"
    st.session_state.history = []
    st.session_state.last_coaching = None
    st.session_state.last_outcome = None
    st.session_state.last_error = None
    st.session_state.secret = random.randint(low, high)
    st.session_state.active_difficulty = difficulty
    log_game_start(difficulty, low, high, attempt_limit)


if "secret" not in st.session_state:
    start_new_game()

if "active_difficulty" not in st.session_state:
    st.session_state.active_difficulty = difficulty

if st.session_state.active_difficulty != difficulty:
    start_new_game()
    st.rerun()

for key, default in {
    "attempts": 0,
    "score": 0,
    "status": "playing",
    "history": [],
    "last_coaching": None,
    "last_outcome": None,
    "last_error": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


attempts_left = attempt_limit - st.session_state.attempts
progress = min(1.0, st.session_state.attempts / max(attempt_limit, 1))
status_label = st.session_state.status.title()
latest_guess = next((item for item in reversed(st.session_state.history) if isinstance(item, int)), None)
latest_guess_display = latest_guess if latest_guess is not None else "None"


left, right = st.columns([1.45, 0.95], gap="large")

with left:
    st.markdown(
        """
        <div class="eyebrow">Applied AI coaching lab</div>
        <h1 class="hero-title">Binary search, made visible.</h1>
        <p class="hero-copy">
            Play the original number-guessing game while an agent analyzes every move,
            retrieves strategy context, calculates the best next midpoint, and explains
            the decision in plain language.
        </p>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="metric-grid">
            <div class="metric"><span>Range</span><strong>{low}-{high}</strong></div>
            <div class="metric"><span>Attempts left</span><strong>{attempts_left}</strong></div>
            <div class="metric"><span>Score</span><strong>{st.session_state.score}</strong></div>
            <div class="metric"><span>Status</span><strong>{status_label}</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="panel panel-intro">
            <p class="panel-title">Guess console</p>
            <p class="panel-copy">Enter a whole number from {low} through {high}. The game validates the value before the coach sees it.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("guess_form", clear_on_submit=False):
        raw_guess = st.text_input(
            "Your guess",
            key=f"guess_input_{difficulty}",
            placeholder=f"Try the midpoint: {low + (high - low) // 2}",
            help="Numbers outside the active range are rejected before scoring.",
        )
        submit = st.form_submit_button("Submit guess", disabled=st.session_state.status != "playing")

    action_col, status_col = st.columns([0.34, 0.66], gap="large")
    with action_col:
        new_game = st.button("Start new round", use_container_width=True)
    with status_col:
        st.markdown(
            f"""
            <div class="status-line">
                <span class="status-dot"></span>
                <span>Round state: {status_label}. Latest guess: {latest_guess_display}.</span>
            </div>
            <div class="range-track" style="--progress: {progress:.3f};"></div>
            """,
            unsafe_allow_html=True,
        )

    if st.session_state.last_error:
        st.error(st.session_state.last_error)

    if st.session_state.last_outcome == "Too High" and show_hint:
        st.warning("The previous guess was too high. Search below it.")
    elif st.session_state.last_outcome == "Too Low" and show_hint:
        st.warning("The previous guess was too low. Search above it.")

    if new_game:
        start_new_game()
        st.rerun()

    if submit:
        st.session_state.last_error = None
        state_ok, state_err = validate_game_state(
            st.session_state.attempts, attempt_limit, st.session_state.status
        )
        if not state_ok:
            st.session_state.last_error = state_err
            st.rerun()

        ok, guess_int, err = validate_guess(raw_guess, low, high)

        if not ok:
            st.session_state.history.append(raw_guess)
            st.session_state.last_error = err
            st.rerun()

        st.session_state.attempts += 1
        st.session_state.history.append(guess_int)
        outcome = check_guess(guess_int, st.session_state.secret)
        st.session_state.last_outcome = outcome

        st.session_state.score = update_score(
            current_score=st.session_state.score,
            outcome=outcome,
            attempt_number=st.session_state.attempts,
        )

        log_guess(guess_int, outcome, st.session_state.attempts, st.session_state.score)

        if ai_coaching_enabled and outcome != "Win":
            attempts_left_after_guess = attempt_limit - st.session_state.attempts
            coaching_placeholder = st.empty()
            coaching_placeholder.markdown('<div class="skeleton"></div>', unsafe_allow_html=True)
            coaching = get_coaching(
                guess=guess_int,
                outcome=outcome,
                history=st.session_state.history,
                low=low,
                high=high,
                attempts_left=attempts_left_after_guess,
                difficulty=difficulty,
            )
            coaching_placeholder.empty()
            st.session_state.last_coaching = coaching

        if outcome == "Win":
            st.session_state.status = "won"
            log_game_end("won", st.session_state.score, st.session_state.attempts, st.session_state.secret)
        elif st.session_state.attempts >= attempt_limit:
            st.session_state.status = "lost"
            log_game_end("lost", st.session_state.score, st.session_state.attempts, st.session_state.secret)

        st.rerun()

    st.markdown(
        '<div class="panel panel-intro"><p class="panel-title">Guess history</p></div>',
        unsafe_allow_html=True,
    )
    numeric_history = [item for item in st.session_state.history if isinstance(item, int)]
    if numeric_history:
        for index, item in enumerate(reversed(numeric_history[-6:]), start=1):
            age = len(numeric_history) - index + 1
            st.markdown(
                f"""
                <div class="history-row">
                    <div class="history-number">{item}</div>
                    <div>
                        <div class="history-meta">Attempt {age} of {attempt_limit}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            '<div class="empty-state">No guesses yet. Start with the midpoint to give the agent a strong baseline.</div>',
            unsafe_allow_html=True,
        )

with right:
    st.markdown(
        '<div class="panel panel-intro"><p class="panel-title">Coach Binary</p></div>',
        unsafe_allow_html=True,
    )

    if st.session_state.status == "won":
        st.success(
            f"You won. The secret was {st.session_state.secret}. Final score: {st.session_state.score}."
        )
    elif st.session_state.status == "lost":
        st.error(
            f"Round lost. The secret was {st.session_state.secret}. Final score: {st.session_state.score}."
        )
    elif st.session_state.last_coaching:
        coaching = st.session_state.last_coaching
        confidence = coaching.confidence
        confidence_label = "High" if confidence >= 0.7 else "Medium" if confidence >= 0.4 else "Low"
        st.markdown(
            f"""
            <p class="panel-copy">Current win confidence: <strong>{confidence_label} ({confidence:.0%})</strong></p>
            <div class="coach-tip">{coaching.tip}</div>
            """,
            unsafe_allow_html=True,
        )
        if coaching.optimal_next_guess is not None:
            st.metric("Optimal next guess", coaching.optimal_next_guess)
    else:
        st.markdown(
            """
            <div class="empty-state">
                The coach will appear after your first valid non-winning guess. It will show a tip,
                confidence score, RAG sources, and the computed midpoint.
            </div>
            """,
            unsafe_allow_html=True,
        )

    if show_reasoning and st.session_state.last_coaching:
        coaching = st.session_state.last_coaching
        with st.expander("Agent reasoning trace", expanded=True):
            for step in coaching.reasoning_trace:
                st.code(step, language=None)
            if coaching.rag_sources:
                st.caption(f"RAG sources: {', '.join(coaching.rag_sources)}")

    with st.expander("Session event log", expanded=False):
        events = read_recent_events(15)
        if events:
            for event in reversed(events):
                event_type = event.get("event_type", "unknown")
                ts = event.get("timestamp", "")[:19]
                if event_type == "guess_submitted":
                    st.write(
                        f"[{ts}] Guess {event.get('guess')} -> {event.get('outcome')} | Score {event.get('current_score')}"
                    )
                elif event_type == "ai_coaching":
                    st.write(
                        f"[{ts}] AI coaching | Confidence {event.get('confidence_score', 0):.0%} | Latency {event.get('api_latency_ms')}ms"
                    )
                elif event_type == "game_start":
                    st.write(
                        f"[{ts}] New round | {event.get('difficulty')} ({event.get('range_low')}-{event.get('range_high')})"
                    )
                elif event_type == "game_end":
                    st.write(
                        f"[{ts}] Round ended | {event.get('status')} | Final score {event.get('final_score')}"
                    )
                elif event_type == "error":
                    st.write(f"[{ts}] Error in {event.get('component')}: {event.get('error')}")
        else:
            st.caption("No events logged yet.")

    with st.expander("Developer state", expanded=False):
        st.write("Secret:", st.session_state.secret)
        st.write("Attempts:", st.session_state.attempts)
        st.write("Score:", st.session_state.score)
        st.write("Difficulty:", difficulty)
        st.write("History:", st.session_state.history)
