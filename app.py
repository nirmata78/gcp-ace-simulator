"""GCP ACE Exam Simulator — browser UI.

Run with:  streamlit run app.py

The shell deliberately imitates a Pearson VUE / Kryterion delivery window: a
sticky status header with the countdown, an uncluttered single-question body, a
collapsible item palette, and a fixed navigation bar. Streamlit's own chrome is
hidden so nothing on screen competes with the question.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

st.set_page_config(
    page_title="Google Cloud ACE — Practice Exam",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --------------------------------------------------------------------------
# Fail-fast network policy
# --------------------------------------------------------------------------
# Checked before anything else. The exam engine itself runs offline, so the
# escape hatch below exists for pure offline study; it is documented in README.

from check_network import ABORT_MESSAGE, is_online  # noqa: E402

if os.environ.get("ACE_SKIP_NETWORK_CHECK") != "1":
    if not is_online():
        print(ABORT_MESSAGE, file=sys.stderr)
        sys.stderr.flush()
        # os._exit terminates the Streamlit server itself with status 1;
        # st.stop() would only halt this script run and leave the server up.
        os._exit(1)

from src.exam_engine import (  # noqa: E402
    ExamSession,
    HISTORY_PATH,
    DATA_DIR,
    REPORTS_DIR,
    filtered_pool,
    load_bank,
    load_history,
    record_attempt,
    seen_question_ids,
    weighted_sample,
)
from src.blueprint import GUIDE_DATE, OBJECTIVES, SECTION_LIST, objective_weights, objectives_in  # noqa: E402
from src.models import (  # noqa: E402
    CERTIFYING_QUESTION_COUNT,
    DOMAIN_SHORT,
    DOMAINS,
    EXAM_DURATION_SECONDS,
    PASS_THRESHOLD,
)
from src.pdf_generator import generate_and_open  # noqa: E402

OPTION_KEYS = ["A", "B", "C", "D"]


# --------------------------------------------------------------------------
# Styling — the exam shell
# --------------------------------------------------------------------------

BASE_CSS = """
<style>
  /* --- strip Streamlit chrome: a candidate should see only the exam --- */
  #MainMenu, footer, header[data-testid="stHeader"] { display: none !important; }
  [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }
  [data-testid="stSidebarCollapsedControl"] { display: none !important; }

  :root {
    --ace-ink: #12181f;
    --ace-muted: #5b6875;
    --ace-rule: #d6dce3;
    --ace-band: #f2f5f8;
    --ace-accent: #1a56b0;
    --ace-pass: #1a7f4b;
    --ace-fail: #b3261e;
    --ace-flag: #b26a00;
  }

  .stApp { background: #ffffff; }
  html, body, [class*="st-"] { color: var(--ace-ink); }

  .block-container {
    padding-top: 5.6rem !important;
    padding-bottom: 6.5rem !important;
    max-width: 1100px;
  }

  /* --- sticky status header --- */
  .st-key-examheader {
    position: fixed; top: 0; left: 0; right: 0; z-index: 1000;
    background: var(--ace-ink); color: #fff;
    border-bottom: 3px solid var(--ace-accent);
    padding: 0.55rem 1.6rem;
    box-shadow: 0 2px 10px rgba(0,0,0,0.18);
  }
  .st-key-examheader * { color: #fff !important; }
  .ace-hdr {
    display: flex; align-items: center; justify-content: space-between;
    gap: 1.5rem; font-size: 0.9rem;
  }
  .ace-hdr .who { font-weight: 700; letter-spacing: 0.01em; }
  .ace-hdr .who small {
    display: block; font-weight: 400; opacity: 0.72; font-size: 0.74rem;
    letter-spacing: 0.06em; text-transform: uppercase;
  }
  .ace-hdr .mid { display: flex; gap: 1.6rem; opacity: 0.92; font-size: 0.82rem; }
  .ace-hdr .mid b { font-size: 0.95rem; display: block; }
  .ace-clock {
    font-variant-numeric: tabular-nums;
    font-family: ui-monospace, Menlo, Consolas, monospace;
    font-size: 1.55rem; font-weight: 700; line-height: 1.1;
    padding: 0.1rem 0.7rem; border-radius: 5px; background: rgba(255,255,255,0.10);
  }
  .ace-clock.warn { background: rgba(255,193,7,0.22); }
  .ace-clock.crit { background: rgba(220,53,69,0.30); animation: acepulse 1.4s infinite; }
  @keyframes acepulse { 0%,100% { opacity: 1; } 50% { opacity: 0.55; } }
  .ace-clock small {
    display: block; font-size: 0.6rem; font-weight: 500; opacity: 0.72;
    letter-spacing: 0.1em; text-transform: uppercase; text-align: center;
  }

  /* --- sticky navigation bar --- */
  .st-key-examnav {
    position: fixed; bottom: 0; left: 0; right: 0; z-index: 1000;
    background: var(--ace-band); border-top: 1px solid var(--ace-rule);
    padding: 0.6rem 1.6rem 0.5rem;
    box-shadow: 0 -2px 10px rgba(0,0,0,0.07);
  }
  .st-key-examnav .stButton > button { width: 100%; font-weight: 600; }

  /* --- question body --- */
  .ace-qmeta {
    font-size: 0.72rem; letter-spacing: 0.09em; text-transform: uppercase;
    color: var(--ace-muted); font-weight: 700; margin-bottom: 0.3rem;
  }
  .ace-qnum { font-size: 1.05rem; font-weight: 700; color: var(--ace-accent); }
  .ace-stem {
    font-size: 1.06rem; line-height: 1.62; margin: 0.5rem 0 1.1rem;
    padding-bottom: 1rem; border-bottom: 1px solid var(--ace-rule);
  }
  .ace-flagged-note {
    display: inline-block; background: #fff4e0; color: var(--ace-flag);
    border: 1px solid #f0d9ac; border-radius: 3px;
    padding: 0.1rem 0.5rem; font-size: 0.72rem; font-weight: 700;
    letter-spacing: 0.06em; text-transform: uppercase;
  }
  div[role="radiogroup"] label {
    padding: 0.42rem 0.6rem; border-radius: 5px; line-height: 1.5;
    border: 1px solid transparent; margin-bottom: 0.12rem;
  }
  div[role="radiogroup"] label:hover { background: var(--ace-band); }

  /* --- palette --- */
  .ace-legend { font-size: 0.76rem; color: var(--ace-muted); margin-bottom: 0.5rem; }
  .ace-legend span { margin-right: 1.1rem; white-space: nowrap; }
  .ace-swatch {
    display: inline-block; width: 11px; height: 11px; border-radius: 2px;
    margin-right: 0.32rem; vertical-align: -1px; border: 1px solid rgba(0,0,0,0.18);
  }
  .ace-pal .stButton > button {
    padding: 0.16rem 0; font-size: 0.76rem; font-weight: 700;
    border-radius: 3px; min-height: 1.9rem; width: 100%;
  }

  /* --- feedback blocks (learning mode) --- */
  .ace-fb { border-left: 4px solid; padding: 0.75rem 1rem; border-radius: 0 5px 5px 0; margin: 0.6rem 0; }
  .ace-fb.ok { border-color: var(--ace-pass); background: #edf7f1; }
  .ace-fb.no { border-color: var(--ace-fail); background: #fdefee; }
  .ace-fb h4 { margin: 0 0 0.3rem; font-size: 0.95rem; }
  .ace-breakdown { font-size: 0.9rem; line-height: 1.55; }
  .ace-breakdown li { margin-bottom: 0.34rem; }

  /* --- results --- */
  .ace-verdict {
    text-align: center; padding: 1.5rem; border-radius: 8px;
    border: 1px solid var(--ace-rule); background: var(--ace-band); margin-bottom: 1.2rem;
  }
  .ace-verdict .big { font-size: 2.6rem; font-weight: 800; line-height: 1.1; }
  .ace-verdict .sub { color: var(--ace-muted); font-size: 0.98rem; margin-top: 0.35rem; }
  .ace-bar { background: #e6ebf0; border-radius: 3px; height: 9px; overflow: hidden; }
  .ace-bar > div { height: 100%; }
</style>
"""


def palette_css(session: ExamSession) -> str:
    """Per-button colour rules for the palette grid, keyed on widget state."""
    colours = {
        "answered": ("#1a56b0", "#ffffff", "#1a56b0"),
        "flagged": ("#f5a623", "#3d2c00", "#c98100"),
        "unanswered": ("#ffffff", "#5b6875", "#c3ccd5"),
    }
    rules = []
    for i in range(session.total):
        bg, fg, border = colours[session.status_of(i)]
        weight = "800" if i == session.index else "700"
        outline = (
            "box-shadow: 0 0 0 2px #12181f inset;" if i == session.index else ""
        )
        rules.append(
            f".st-key-pal_{i} button {{ background:{bg} !important; color:{fg} !important;"
            f" border:1px solid {border} !important; font-weight:{weight} !important; {outline} }}"
        )
    return "<style>" + "\n".join(rules) + "</style>"


# --------------------------------------------------------------------------
# Session state
# --------------------------------------------------------------------------


def init_state() -> None:
    st.session_state.setdefault("screen", "home")
    st.session_state.setdefault("session", None)
    st.session_state.setdefault("attempt", None)
    st.session_state.setdefault("report", None)
    st.session_state.setdefault("report_opened", False)
    st.session_state.setdefault("candidate", "Candidate")
    st.session_state.setdefault("show_submit_confirm", False)


def start_exam(mode: str, questions, duration: int) -> None:
    st.session_state.session = ExamSession(questions, mode=mode, duration_seconds=duration)
    st.session_state.attempt = None
    st.session_state.report = None
    st.session_state.report_opened = False
    st.session_state.show_submit_confirm = False
    st.session_state.screen = "exam"


def submit_exam(expired: bool = False) -> None:
    """Deferred grading: this is the only place answers are scored."""
    sess: ExamSession = st.session_state.session
    if expired:
        sess.time_expired = True

    attempt = sess.build_attempt()
    path = None
    opened = False
    try:
        path, opened = generate_and_open(
            attempt,
            sess.questions,
            candidate=st.session_state.candidate,
            out_dir=REPORTS_DIR,
            auto_open=True,
        )
        attempt.report_path = str(path)
    except Exception as exc:  # a PDF failure must never lose the score
        st.session_state.report_error = str(exc)

    record_attempt(attempt, HISTORY_PATH)
    st.session_state.attempt = attempt
    st.session_state.report = path
    st.session_state.report_opened = opened
    st.session_state.screen = "results"


# --------------------------------------------------------------------------
# Screens
# --------------------------------------------------------------------------


def screen_home() -> None:
    try:
        bank = load_bank(DATA_DIR)
    except FileNotFoundError as exc:
        st.error(str(exc))
        return

    st.markdown(
        "<div style='padding-top:0.5rem'>"
        "<div style='font-size:0.74rem;letter-spacing:0.14em;text-transform:uppercase;"
        "color:#5b6875;font-weight:700'>Google Cloud Certification</div>"
        "<h1 style='margin:0.1rem 0 0.2rem;font-size:2rem'>Associate Cloud Engineer</h1>"
        "<div style='color:#5b6875'>Local practice examination simulator</div></div>",
        unsafe_allow_html=True,
    )
    st.divider()

    counts = bank.counts()
    cols = st.columns(len(DOMAINS))
    for col, d in zip(cols, DOMAINS):
        col.metric(DOMAIN_SHORT[d], counts[d])
    n_new = sum(1 for q in bank.questions if q.is_new)
    st.caption(
        f"{len(bank.questions)} questions on the exam guide live from {GUIDE_DATE} — four sections, "
        f"twelve objectives; {n_new} of them on topics that guide introduced."
    )

    st.session_state.candidate = st.text_input(
        "Candidate name (printed on the score report)",
        value=st.session_state.candidate,
    )

    tab_cert, tab_learn, tab_hist = st.tabs(
        ["🎓 Certifying Mode", "📖 Learning Mode", "📊 History"]
    )

    # ---- certifying -----------------------------------------------------
    with tab_cert:
        st.markdown(
            f"**Timed examination.** {CERTIFYING_QUESTION_COUNT} questions sampled at the "
            f"guide's section weights (20 / 30 / 30 / 20), spread across its objectives, "
            f"{EXAM_DURATION_SECONDS // 60} minutes, deferred grading. As in the real delivery "
            "window, the item's topic is not shown while you sit. A PDF score report is produced "
            "and opened in your browser on submission."
        )
        prefer_unseen = st.checkbox(
            "Prefer questions I have not answered in earlier attempts", value=True,
            help="Unseen questions are drawn first in every objective, so repeated attempts "
                 "measure knowledge rather than recall of the items.",
        )
        c1, c2, c3 = st.columns(3)
        n = c1.number_input("Questions", 10, min(200, len(bank.questions)),
                            CERTIFYING_QUESTION_COUNT, step=5)
        mins = c2.number_input("Minutes", 5, 240, EXAM_DURATION_SECONDS // 60, step=5)
        c3.markdown("<div style='height:1.85rem'></div>", unsafe_allow_html=True)
        if c3.button("▶  Begin examination", type="primary", use_container_width=True):
            seen = seen_question_ids(HISTORY_PATH) if prefer_unseen else None
            start_exam("certifying", weighted_sample(bank, int(n), seen=seen), int(mins) * 60)
            st.rerun()

        with st.expander("Blueprint used for sampling (per 50 questions)"):
            w = objective_weights()
            for sec in SECTION_LIST:
                st.markdown(f"**{sec.label}** — {sec.weight:.0%} · {round(sec.weight * 50)} items")
                for o in objectives_in(sec.number):
                    st.write(f"- {o.id} {o.title} — ~{w[o.id] * 50:.1f}")
            st.caption("The guide publishes section weights only; inside a section the items are "
                       "split in proportion to each objective's number of guide bullets.")

    # ---- learning -------------------------------------------------------
    with tab_learn:
        st.markdown(
            "**Untimed practice.** Answer, then reveal the full distractor analysis, the "
            "gcloud syntax and the documentation reference before moving on."
        )
        picked = st.multiselect(
            "Sections (leave empty for all)", DOMAINS,
            format_func=lambda d: DOMAIN_SHORT[d],
        )
        objs = [o for o in OBJECTIVES if not picked
                or any(d.startswith(f"Section {o.split('.')[0]}:") for d in picked)]
        picked_objs = st.multiselect(
            "Objectives (leave empty for all)", objs,
            format_func=lambda o: f"{o} {OBJECTIVES[o].title}",
        )
        new_only = st.checkbox("Only topics introduced by the June 2026 guide")
        pool = filtered_pool(bank, picked or None, None, picked_objs or None, new_only)
        subs = sorted({q.subtopic for q in pool})
        picked_subs = st.multiselect("Subtopics (leave empty for all)", subs)
        pool = filtered_pool(bank, picked or None, picked_subs or None, picked_objs or None, new_only)

        c1, c2 = st.columns([1, 2])
        n = c1.number_input("Questions", 1, max(1, len(pool)), min(20, len(pool)), step=5)
        c2.markdown("<div style='height:1.85rem'></div>", unsafe_allow_html=True)
        if c2.button("▶  Start practice", type="primary", use_container_width=True,
                     disabled=not pool):
            import random
            start_exam("learning", random.sample(pool, int(n)), 10 ** 9)
            st.rerun()
        st.caption(f"{len(pool)} questions match the current filter.")

    # ---- history --------------------------------------------------------
    with tab_hist:
        history = load_history(HISTORY_PATH)
        if not history.attempts:
            st.info("No attempts recorded yet. Your results will appear here.")
        else:
            rows = [
                {
                    "Finished": a.finished_at.replace("T", " ").replace("+00:00", ""),
                    "Mode": a.mode,
                    "Score": f"{a.correct_count}/{a.question_count}",
                    "%": round(a.score_pct * 100, 1),
                    "Result": "PASS" if a.passed else "FAIL",
                }
                for a in reversed(history.attempts)
            ]
            st.dataframe(rows, use_container_width=True, hide_index=True)

            st.markdown("##### Rolling accuracy by section (all attempts)")
            for d, ds in load_history(HISTORY_PATH).rolling_domain_accuracy().items():
                colour = "var(--ace-pass)" if ds.pct >= PASS_THRESHOLD else "var(--ace-fail)"
                st.markdown(
                    f"<div style='display:flex;gap:0.8rem;align-items:center;margin-bottom:0.4rem'>"
                    f"<div style='width:140px;font-size:0.85rem'>{DOMAIN_SHORT[d]}</div>"
                    f"<div class='ace-bar' style='flex:1'>"
                    f"<div style='width:{ds.pct*100:.1f}%;background:{colour}'></div></div>"
                    f"<div style='width:80px;text-align:right;font-size:0.85rem'>"
                    f"{ds.correct}/{ds.total} · {ds.pct*100:.0f}%</div></div>",
                    unsafe_allow_html=True,
                )


def render_header(sess: ExamSession) -> None:
    """Sticky status bar. The clock fragment reruns itself once a second."""
    with st.container(key="examheader"):

        # Timed exams need a per-second countdown; untimed practice ticks more
        # slowly so the elapsed clock still looks alive without the churn.
        @st.fragment(run_every=1 if sess.is_timed else 5)
        def _bar() -> None:
            if sess.is_timed and sess.check_expiry() and not sess.submitted:
                submit_exam(expired=True)
                st.rerun(scope="app")

            remaining = sess.remaining_seconds
            cls = "ace-clock"
            if sess.is_timed:
                if remaining <= 300:
                    cls += " crit"
                elif remaining <= 900:
                    cls += " warn"
                clock = ExamSession.format_clock(remaining)
                label = "Time remaining"
            else:
                clock = ExamSession.format_clock(sess.elapsed_seconds)
                label = "Elapsed"

            mode = "Certifying" if sess.is_timed else "Learning"
            st.markdown(
                f"""<div class="ace-hdr">
  <div class="who">{st.session_state.candidate}
    <small>Google Cloud · Associate Cloud Engineer · {mode} Mode</small></div>
  <div class="mid">
    <div>Item<b>{sess.index + 1} of {sess.total}</b></div>
    <div>Answered<b>{sess.answered_count}</b></div>
    <div>Unanswered<b>{sess.unanswered_count}</b></div>
    <div>Flagged<b>{sess.flagged_count}</b></div>
  </div>
  <div class="{cls}">{clock}<small>{label}</small></div>
</div>""",
                unsafe_allow_html=True,
            )

        _bar()


def render_palette(sess: ExamSession) -> None:
    with st.expander(
        f"▦  Question palette — {sess.answered_count} answered · "
        f"{sess.unanswered_count} unanswered · {sess.flagged_count} flagged",
        expanded=False,
    ):
        st.markdown(
            "<div class='ace-legend'>"
            "<span><i class='ace-swatch' style='background:#1a56b0'></i>Answered</span>"
            "<span><i class='ace-swatch' style='background:#ffffff'></i>Unanswered</span>"
            "<span><i class='ace-swatch' style='background:#f5a623'></i>Flagged for review</span>"
            "<span><i class='ace-swatch' style='background:#12181f'></i>Current item</span>"
            "</div>",
            unsafe_allow_html=True,
        )
        st.markdown("<div class='ace-pal'>", unsafe_allow_html=True)
        per_row = 10
        for start in range(0, sess.total, per_row):
            cols = st.columns(per_row)
            for offset in range(per_row):
                i = start + offset
                if i >= sess.total:
                    break
                with cols[offset]:
                    if st.button(str(i + 1), key=f"pal_{i}", use_container_width=True):
                        sess.goto(i)
                        st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


def render_question(sess: ExamSession) -> None:
    q = sess.current
    flagged = q.id in sess.flagged

    # The real exam never labels an item's topic; only learning mode does.
    meta = (f"{DOMAIN_SHORT.get(q.domain, q.domain)} &nbsp;·&nbsp; {q.objective} &nbsp;·&nbsp; {q.subtopic}"
            if not sess.is_timed else "Google Cloud · Associate Cloud Engineer")
    st.markdown(
        f"<div class='ace-qmeta'>{meta}</div>"
        f"<div class='ace-qnum'>Question {sess.index + 1} of {sess.total}"
        + ("&nbsp; <span class='ace-flagged-note'>⚑ Flagged</span>" if flagged else "")
        + "</div>"
        f"<div class='ace-stem'>{q.question}</div>",
        unsafe_allow_html=True,
    )

    current = sess.answers.get(q.id)
    idx = OPTION_KEYS.index(current) if current in OPTION_KEYS else None
    revealed = sess.is_revealed(q.id) if not sess.is_timed else False

    choice = st.radio(
        "Select one answer",
        OPTION_KEYS,
        index=idx,
        key=f"radio_{q.id}",
        format_func=lambda k: f"{k}.  {q.options[k]}",
        disabled=revealed,
        label_visibility="collapsed",
    )
    if choice and choice != current:
        sess.answer(choice, q.id)
        st.rerun()

    # ---- learning-mode feedback ----------------------------------------
    if not sess.is_timed:
        c1, c2 = st.columns([1, 4])
        if not revealed:
            if c1.button("Check answer", type="primary", disabled=choice is None):
                sess.reveal(q.id)
                st.rerun()
            if choice is None:
                c2.caption("Choose an option to reveal the analysis.")
        else:
            correct = choice == q.correct_answer
            tone = "ok" if correct else "no"
            st.markdown(
                f"<div class='ace-fb {tone}'><h4>"
                + (
                    f"✓ Correct — {q.correct_answer}"
                    if correct
                    else f"✗ Incorrect — you chose {choice}; the answer is {q.correct_answer}"
                )
                + f"</h4>{q.explanation.summary}</div>",
                unsafe_allow_html=True,
            )
            items = "".join(
                f"<li><b>{k}.</b> {q.explanation.option_breakdown[k]}</li>"
                for k in OPTION_KEYS
            )
            st.markdown(
                f"<div class='ace-breakdown'><b>Option analysis</b><ul>{items}</ul></div>",
                unsafe_allow_html=True,
            )
            if q.explanation.gcloud_command:
                st.markdown("**Command**")
                st.code(q.explanation.gcloud_command, language="bash")
            if q.explanation.doc_ref:
                st.markdown(f"📄 [Google Cloud documentation]({q.explanation.doc_ref})")


def render_nav(sess: ExamSession) -> None:
    with st.container(key="examnav"):
        c1, c2, c3, c4, c5 = st.columns([1, 1, 1.4, 3, 1.4])

        if c1.button("◀  Previous", use_container_width=True, disabled=sess.index == 0):
            sess.prev_question()
            st.rerun()

        if c2.button("Next  ▶", use_container_width=True,
                     disabled=sess.index >= sess.total - 1):
            sess.next_question()
            st.rerun()

        flagged = sess.current.id in sess.flagged
        if c3.button("⚑  Unflag" if flagged else "⚑  Flag for Review",
                     use_container_width=True,
                     type="secondary"):
            sess.toggle_flag()
            st.rerun()

        with c4:
            done = sess.answered_count
            st.markdown(
                f"<div style='padding-top:0.35rem;font-size:0.82rem;color:#5b6875'>"
                f"{done} of {sess.total} answered"
                f"<div class='ace-bar' style='margin-top:0.25rem'>"
                f"<div style='width:{done/sess.total*100:.1f}%;background:#1a56b0'></div>"
                f"</div></div>",
                unsafe_allow_html=True,
            )

        label = "Submit Exam" if sess.is_timed else "End & Score"
        if c5.button(label, type="primary", use_container_width=True):
            st.session_state.show_submit_confirm = True
            st.rerun()


@st.dialog("Submit for grading?")
def confirm_submit(sess: ExamSession) -> None:
    st.write(
        f"You have answered **{sess.answered_count} of {sess.total}** questions."
    )
    if sess.unanswered_count:
        st.warning(f"{sess.unanswered_count} question(s) will be marked incorrect.")
    if sess.flagged_count:
        st.info(f"{sess.flagged_count} question(s) are still flagged for review.")
    st.caption("Submitting is final. A PDF report will be generated and opened in your browser.")

    c1, c2 = st.columns(2)
    if c1.button("Return to exam", use_container_width=True):
        st.session_state.show_submit_confirm = False
        st.rerun()
    if c2.button("Submit now", type="primary", use_container_width=True):
        st.session_state.show_submit_confirm = False
        submit_exam()
        st.rerun()


def screen_exam() -> None:
    sess: ExamSession = st.session_state.session
    st.markdown(palette_css(sess), unsafe_allow_html=True)

    render_header(sess)
    render_palette(sess)
    render_question(sess)
    render_nav(sess)

    if st.session_state.show_submit_confirm:
        confirm_submit(sess)


def screen_results() -> None:
    attempt = st.session_state.attempt
    sess: ExamSession = st.session_state.session
    passed = attempt.passed
    colour = "var(--ace-pass)" if passed else "var(--ace-fail)"

    st.markdown(
        f"<div class='ace-verdict'>"
        f"<div class='big' style='color:{colour}'>{'PASS' if passed else 'DID NOT PASS'}</div>"
        f"<div class='sub'>{attempt.correct_count} of {attempt.question_count} correct · "
        f"<b>{attempt.score_pct*100:.1f}%</b> · threshold {PASS_THRESHOLD*100:.0f}%</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    if attempt.time_expired:
        st.warning("Time expired — the exam was submitted automatically.")

    mins, secs = divmod(int(attempt.duration_seconds), 60)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Score", f"{attempt.score_pct*100:.1f}%")
    c2.metric("Correct", f"{attempt.correct_count}/{attempt.question_count}")
    c3.metric("Time used", f"{mins}m {secs:02d}s")
    c4.metric("Unanswered", sum(1 for a in attempt.answers if not a.is_answered))

    # ---- report ---------------------------------------------------------
    report = st.session_state.report
    if report:
        if st.session_state.report_opened:
            st.success(f"Score report generated and opened in your browser: `{report.name}`")
        else:
            st.info(
                f"Score report generated: `{report}`. "
                "The browser could not be launched automatically — open it from the link below."
            )
        with open(report, "rb") as fh:
            st.download_button("⬇  Download PDF report", fh, file_name=report.name,
                               mime="application/pdf")
    elif st.session_state.get("report_error"):
        st.error(f"The PDF report could not be generated: {st.session_state.report_error}")

    # ---- domain breakdown ----------------------------------------------
    st.markdown("#### Performance by section")
    for ds in attempt.domain_scores():
        colour = "var(--ace-pass)" if ds.pct >= PASS_THRESHOLD else "var(--ace-fail)"
        st.markdown(
            f"<div style='display:flex;gap:0.8rem;align-items:center;margin-bottom:0.5rem'>"
            f"<div style='width:140px;font-size:0.88rem'>{DOMAIN_SHORT[ds.domain]}</div>"
            f"<div class='ace-bar' style='flex:1'>"
            f"<div style='width:{ds.pct*100:.1f}%;background:{colour}'></div></div>"
            f"<div style='width:90px;text-align:right;font-size:0.88rem'>"
            f"{ds.correct}/{ds.total} · {ds.pct*100:.0f}%</div></div>",
            unsafe_allow_html=True,
        )

    obj_rows = attempt.objective_scores()
    if obj_rows:
        st.markdown("#### Performance by objective")
        st.dataframe(
            [{"Objective": f"{o} {OBJECTIVES[o].title}", "Correct": f"{c}/{t}",
              "Accuracy": f"{c/t*100:.0f}%"} for o, c, t in obj_rows],
            use_container_width=True, hide_index=True,
        )

    gaps = attempt.subtopic_gaps()
    if gaps:
        st.markdown("#### Weakest subtopics")
        st.dataframe(
            [{"Subtopic": s, "Correct": f"{c}/{t}", "Accuracy": f"{c/t*100:.0f}%"}
             for s, c, t in gaps],
            use_container_width=True, hide_index=True,
        )

    # ---- item review ----------------------------------------------------
    st.markdown("#### Item review")
    qmap = {q.id: q for q in sess.questions}
    only_wrong = st.checkbox("Show only missed and unanswered items", value=True)

    for n, rec in enumerate(attempt.answers, start=1):
        if only_wrong and rec.is_correct:
            continue
        q = qmap.get(rec.question_id)
        if q is None:
            continue
        mark = "✓" if rec.is_correct else ("—" if not rec.is_answered else "✗")
        # The title names the lesson, so the review reads as a study list.
        with st.expander(f"{mark}  Q{n} · {q.title}  ·  {DOMAIN_SHORT.get(q.domain, '')} · {q.objective} {q.subtopic}"):
            st.caption(f"`{q.id}` — {q.summary}")
            st.markdown(q.question)
            for k in OPTION_KEYS:
                if k == q.correct_answer:
                    st.markdown(f"**:green[{k}. {q.options[k]}]**  ← correct")
                elif k == rec.selected:
                    st.markdown(f":red[{k}. {q.options[k]}]  ← your answer")
                else:
                    st.markdown(f"{k}. {q.options[k]}")
            st.markdown(f"**Why:** {q.explanation.summary}")
            for k in OPTION_KEYS:
                st.caption(f"**{k}.** {q.explanation.option_breakdown[k]}")
            if q.explanation.gcloud_command:
                st.code(q.explanation.gcloud_command, language="bash")
            if q.explanation.doc_ref:
                st.markdown(f"📄 [Documentation]({q.explanation.doc_ref})")

    st.divider()
    c1, c2 = st.columns(2)
    if c1.button("↺  Return to start", use_container_width=True, type="primary"):
        st.session_state.session = None
        st.session_state.attempt = None
        st.session_state.screen = "home"
        st.rerun()
    if c2.button("Review the exam again", use_container_width=True):
        st.rerun()


# --------------------------------------------------------------------------


def main() -> None:
    st.markdown(BASE_CSS, unsafe_allow_html=True)
    init_state()

    screen = st.session_state.screen
    if screen == "exam" and st.session_state.session is not None:
        screen_exam()
    elif screen == "results" and st.session_state.attempt is not None:
        screen_results()
    else:
        screen_home()


main()
