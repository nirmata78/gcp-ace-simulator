"""GCP ACE Exam Simulator — browser UI.

Run with:  streamlit run app.py

The shell deliberately imitates a Pearson VUE / Kryterion delivery window: a
sticky status header with the countdown, an uncluttered single-question body, a
collapsible item palette, and a fixed navigation bar. Streamlit's own chrome is
hidden so nothing on screen competes with the question.
"""

from __future__ import annotations

import html
import re
import sys
from datetime import datetime
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

from src.exam_engine import (  # noqa: E402
    ExamSession,
    DATA_DIR,
    filtered_pool,
    load_bank,
    load_history,
    record_attempt,
    seen_question_ids,
    weighted_sample,
)
from src.paths import history_path, reports_dir  # noqa: E402
from src.blueprint import GUIDE_DATE, OBJECTIVES, SECTION_LIST, objective_weights, objectives_in  # noqa: E402
from src.models import (  # noqa: E402
    CERTIFYING_QUESTION_COUNT,
    DOMAIN_SHORT,
    DOMAINS,
    EXAM_DURATION_SECONDS,
    PASS_THRESHOLD,
)
from src.retrospective import (  # noqa: E402
    build_report,
    in_review,
    margin_lede,
    restates,
    timing_facts,
)
from src import study_links  # noqa: E402

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

  /* Material 3 baseline tokens (light). The legacy --ace-* names map onto them. */
  :root {
    --md-primary: #0b57d0;
    --md-on-primary: #ffffff;
    --md-primary-container: #d3e3fd;
    --md-on-primary-container: #041e49;
    --md-surface: #ffffff;
    --md-surface-low: #f8fafd;
    --md-surface-container: #f0f4f9;
    --md-surface-high: #e9eef6;
    --md-on-surface: #1f1f1f;
    --md-on-surface-variant: #444746;
    --md-outline: #747775;
    --md-outline-variant: #c4c7c5;
    --md-error: #b3261e;
    --md-error-container: #f9dedc;
    --md-success: #146c2e;
    --md-success-container: #c4eed0;
    --md-warning: #7c5800;
    --md-warning-container: #ffdf99;
    --md-elev-1: 0 1px 2px rgba(0,0,0,.30), 0 1px 3px 1px rgba(0,0,0,.15);
    --md-elev-2: 0 1px 2px rgba(0,0,0,.30), 0 2px 6px 2px rgba(0,0,0,.15);

    --ace-ink: var(--md-on-surface);
    --ace-muted: var(--md-on-surface-variant);
    --ace-rule: var(--md-outline-variant);
    --ace-band: var(--md-surface-container);
    --ace-accent: var(--md-primary);
    --ace-pass: var(--md-success);
    --ace-fail: var(--md-error);
    --ace-flag: var(--md-warning);

    /* Bar heights in rem, so they grow with the type. The page and the panel lay out from these. */
    --ace-hdr: 4rem;
    --ace-nav: 4.75rem;
    --ace-gutter: clamp(16px, 2.5vw, 40px);
  }

  /* Type scales with the window, as browser zoom would: 16px up to ~1300px wide, about 20px
     on a 1728px laptop screen, at most 24px. Streamlit sizes in rem, so everything follows. */
  html { font-size: clamp(16px, calc(4px + 0.93vw), 24px) !important; }
  .stApp { background: var(--md-surface); color: var(--md-on-surface); }

  /* Buttons: Material filled (primary) and outlined (secondary), with legible hover,
     pressed, focus and disabled states. Streamlit's own hover darkens text into the fill. */
  [data-testid^="stBaseButton"] { transition: background-color .15s, box-shadow .15s, border-color .15s; }
  [data-testid^="stBaseButton"] p { color: inherit !important; font-weight: 600; }
  [data-testid="stBaseButton-primary"] {
    background: var(--md-primary) !important; color: var(--md-on-primary) !important;
    border: 1px solid var(--md-primary) !important; }
  [data-testid="stBaseButton-primary"]:hover {
    background: #0842a0 !important; border-color: #0842a0 !important; color: #fff !important;
    box-shadow: var(--md-elev-1); }
  [data-testid="stBaseButton-primary"]:active { background: #062e6f !important; color: #fff !important; }
  [data-testid="stBaseButton-secondary"] {
    background: var(--md-surface) !important; color: var(--md-primary) !important;
    border: 1px solid var(--md-outline) !important; }
  [data-testid="stBaseButton-secondary"]:hover {
    background: #e8effa !important; color: #0842a0 !important; border-color: var(--md-primary) !important; }
  [data-testid="stBaseButton-secondary"]:active { background: var(--md-primary-container) !important; }
  [data-testid^="stBaseButton"]:focus-visible {
    outline: 3px solid var(--md-primary-container) !important; outline-offset: 2px; }
  [data-testid^="stBaseButton"]:disabled, [data-testid^="stBaseButton"][disabled] {
    background: rgba(31,31,31,.06) !important; color: rgba(31,31,31,.42) !important;
    border-color: rgba(31,31,31,.14) !important; box-shadow: none !important; }

  /* Fill the window. Reading width is kept by the layout, not by an empty margin. */
  .block-container {
    max-width: 2000px !important;
    padding: calc(var(--ace-hdr) + 4px) var(--ace-gutter) 32px !important;
  }
  .block-container:has(.st-key-examnav) { padding-bottom: calc(var(--ace-nav) + 24px) !important; }
  .block-container:not(:has(.st-key-examheader)) { padding-top: 32px !important; }

  /* --- top app bar --- */
  .st-key-examheader {
    position: fixed; top: 0; left: 0; right: 0; z-index: 1000;
    height: var(--ace-hdr); box-sizing: border-box; overflow: hidden;
    display: flex; flex-direction: column; justify-content: center;
    background: var(--md-surface-container); color: var(--md-on-surface);
    border-bottom: 1px solid var(--md-outline-variant);
    padding: 0 var(--ace-gutter);
  }
  .st-key-examheader > div { width: 100%; }
  .st-key-examheader [data-testid="stMarkdownContainer"] p { margin: 0; }
  .ace-hdr {
    display: flex; align-items: center; justify-content: space-between;
    gap: 1.5rem; font-size: 0.875rem; line-height: 1.25; width: 100%;
  }
  .ace-hdr .who { font-weight: 600; font-size: 1rem; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .ace-hdr .who small {
    display: block; font-weight: 500; color: var(--md-on-surface-variant); font-size: 0.6875rem;
    letter-spacing: 0.06em; text-transform: uppercase; overflow: hidden; text-overflow: ellipsis;
  }
  .ace-hdr .mid { display: flex; gap: 1.75rem; color: var(--md-on-surface-variant); font-size: 0.75rem; }
  .ace-hdr .mid > div { display: flex; flex-direction: column; align-items: center; }
  .ace-hdr .mid b { font-size: 1rem; color: var(--md-on-surface); font-weight: 600; }
  .ace-clock {
    font-variant-numeric: tabular-nums;
    font-family: ui-monospace, "Roboto Mono", Menlo, Consolas, monospace;
    font-size: 1.375rem; font-weight: 600; line-height: 1.1; text-align: center;
    padding: 6px 14px; border-radius: 12px;
    background: var(--md-primary-container); color: var(--md-on-primary-container);
  }
  .ace-clock.warn { background: var(--md-warning-container); color: #261a00; }
  .ace-clock.crit { background: var(--md-error-container); color: #410e0b; animation: acepulse 1.4s infinite; }
  @keyframes acepulse { 0%,100% { opacity: 1; } 50% { opacity: 0.6; } }
  @media (prefers-reduced-motion: reduce) { .ace-clock.crit { animation: none; } }
  .ace-clock small {
    display: block; font-size: 0.625rem; font-weight: 500; opacity: 0.8;
    letter-spacing: 0.1em; text-transform: uppercase; font-family: inherit;
  }

  /* --- bottom app bar --- */
  .st-key-examnav {
    position: fixed; bottom: 0; left: 0; right: 0; z-index: 1000;
    height: var(--ace-nav); box-sizing: border-box;
    /* A column flex box: justify-content is what centres the row vertically. */
    display: flex; flex-direction: column; justify-content: center;
    background: var(--md-surface-container); border-top: 1px solid var(--md-outline-variant);
    padding: 0 var(--ace-gutter);
  }
  .st-key-examnav > div { width: 100%; }
  .st-key-examnav [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; align-items: center; gap: 0.75rem !important; }
  .st-key-examnav .stButton > button { min-height: 2.75rem; }
  .st-key-examnav [data-testid="stColumn"] { min-width: 0 !important; }
  .st-key-examnav .stButton > button { width: 100%; font-weight: 600; white-space: nowrap; }
  .ace-progress { font-size: 0.8125rem; color: var(--md-on-surface-variant); padding: 0 0.5rem; }

  /* --- question body --- */
  .ace-qmeta {
    font-size: 0.75rem; letter-spacing: 0.08em; text-transform: uppercase;
    color: var(--ace-muted); font-weight: 600; margin-bottom: 0.3rem;
  }
  .ace-qnum { font-size: 1.05rem; font-weight: 600; color: var(--ace-accent); }
  .ace-stem {
    font-size: 1.0625rem; line-height: 1.62; margin: 0.5rem 0 1.1rem;
    padding-bottom: 1rem; border-bottom: 1px solid var(--ace-rule);
  }
  .ace-flagged-note {
    display: inline-block; background: var(--md-warning-container); color: #261a00;
    border-radius: 8px; padding: 0.1rem 0.6rem; font-size: 0.75rem; font-weight: 600;
  }
  /* Answer options read at the stem's size, each a full-width target. */
  div[role="radiogroup"] { gap: 0.25rem; width: 100%; }
  div[role="radiogroup"] > div { width: 100%; }
  div[role="radiogroup"] label {
    padding: 0.6rem 0.85rem; border-radius: 12px; line-height: 1.55; width: 100%;
    border: 1px solid transparent; margin-bottom: 0.1rem;
  }
  div[role="radiogroup"] label p, div[role="radiogroup"] label div { font-size: 1.0625rem !important; line-height: 1.55; }
  /* Revealed options are disabled, but must stay readable rather than greyed out. */
  div[role="radiogroup"] label { opacity: 1 !important; }
  div[role="radiogroup"] label p { color: var(--md-on-surface) !important; }
  div[role="radiogroup"] label:hover { background: var(--md-surface-container); }

  /* --- palette --- */
  .ace-legend { font-size: 0.76rem; color: var(--ace-muted); margin-bottom: 0.5rem; }
  .ace-legend span { margin-right: 1.1rem; white-space: nowrap; }
  .ace-swatch {
    display: inline-block; width: 11px; height: 11px; border-radius: 3px;
    margin-right: 0.32rem; vertical-align: -1px; border: 1px solid rgba(0,0,0,0.18);
  }
  .ace-pal .stButton > button {
    padding: 0.16rem 0; font-size: 0.76rem; font-weight: 700;
    border-radius: 8px; min-height: 1.9rem; width: 100%;
  }

  /* --- feedback blocks (learning mode) --- */
  .ace-fb { padding: 0.75rem 1rem; border-radius: 12px; margin: 0.6rem 0; }
  .ace-fb.ok { background: var(--md-success-container); color: #002106; }
  .ace-fb.no { background: var(--md-error-container); color: #410e0b; }
  .ace-fb h4 { margin: 0 0 0.3rem; font-size: 0.95rem; padding: 0; }
  .ace-breakdown { font-size: 0.9rem; line-height: 1.55; }
  .ace-breakdown li { margin-bottom: 0.34rem; }
  .ace-bar { background: var(--md-surface-high); border-radius: 4px; height: 8px; overflow: hidden; }
  .ace-bar > div { height: 100%; border-radius: 4px; }

  /* --- learning mode: question | splitter | study panel ---
     The split is a CSS variable the splitter script sets, so it survives reruns. */
  [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .st-key-studypanel) {
    gap: 0 !important; align-items: stretch !important;
  }
  [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .st-key-studypanel) > [data-testid="stColumn"]:first-child {
    flex: 0 0 var(--ace-split, 60%) !important; width: auto !important; max-width: none !important;
    min-width: 0 !important; padding-right: 20px; box-sizing: border-box;
  }
  [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .st-key-studypanel) > [data-testid="stColumn"]:last-child {
    flex: 1 1 0 !important; width: auto !important; min-width: 0 !important;
    position: relative; padding-left: 20px; box-sizing: border-box;
  }
  /* Sticky needs a tall parent: stretch the panel column's inner blocks to its full height. */
  [data-testid="stColumn"]:has(.st-key-studypanel) > div,
  [data-testid="stColumn"]:has(.st-key-studypanel) > div > div:has(.st-key-studypanel) { height: 100%; }

  .ace-splitter {
    position: absolute; top: 0; bottom: 0; left: -12px; width: 24px; z-index: 5;
    cursor: col-resize; touch-action: none; outline: none;
  }
  .ace-splitter::before {
    content: ""; position: absolute; top: 0; bottom: 0; left: 11.5px; width: 1px;
    background: var(--md-outline-variant); transition: background .15s, width .15s, left .15s;
  }
  .ace-splitter .ace-grip {
    position: sticky; top: calc(var(--ace-hdr) + 40vh); margin-left: 8px;
    width: 8px; height: 48px; border-radius: 4px; background: var(--md-outline);
    transition: background .15s, transform .15s;
  }
  .ace-splitter:hover::before, .ace-splitter:focus-visible::before, body.ace-resizing .ace-splitter::before {
    background: var(--md-primary); width: 3px; left: 10.5px;
  }
  .ace-splitter:hover .ace-grip, .ace-splitter:focus-visible .ace-grip,
  body.ace-resizing .ace-splitter .ace-grip { background: var(--md-primary); transform: scaleY(1.15); }
  .ace-splitter:focus-visible .ace-grip { box-shadow: 0 0 0 3px var(--md-primary-container); }
  body.ace-resizing { cursor: col-resize !important; user-select: none !important; }
  body.ace-resizing iframe { pointer-events: none; }

  /* The study panel: a sheet that slides in, fits between the bars and scrolls on its own. */
  @keyframes ace-slide-in { from { transform: translateX(48px); opacity: 0; } to { transform: none; opacity: 1; } }
  .st-key-studypanel {
    position: sticky; top: calc(var(--ace-hdr) + 16px);
    max-height: var(--ace-panel-max, calc(100vh - var(--ace-hdr) - var(--ace-nav) - 32px)); overflow-y: auto;
    overscroll-behavior: contain; scrollbar-gutter: stable;
    background: var(--md-surface-low); border: 1px solid var(--md-outline-variant);
    border-radius: 16px; padding: 16px 20px 20px; box-sizing: border-box;
    animation: ace-slide-in 0.28s cubic-bezier(.2,0,0,1);
  }
  @media (prefers-reduced-motion: reduce) { .st-key-studypanel { animation: none; } }
  .st-key-studypanel p, .st-key-studypanel li { font-size: 0.92rem; }
  .st-key-studypanel table { font-size: 0.8rem; }
  .st-key-studypanel pre { white-space: pre-wrap; word-break: break-word; }
  .ace-panel-h { font-size: 0.75rem; letter-spacing: 0.1em; text-transform: uppercase;
    color: var(--ace-muted); font-weight: 600; margin-bottom: 0.2rem; }
  .ace-panel-links { font-size: 0.85rem; margin: 0.1rem 0 0.4rem; }

  /* --- score report --- */
  .ace-card {
    background: var(--md-surface-low); border: 1px solid var(--md-outline-variant);
    border-radius: 16px; padding: 20px 24px; margin-bottom: 16px;
  }
  .ace-card h3 { font-size: 0.75rem; letter-spacing: 0.1em; text-transform: uppercase;
    color: var(--ace-muted); font-weight: 600; margin: 0 0 12px; padding: 0; }
  .ace-hero { display: grid; grid-template-columns: auto 1fr; gap: 8px 32px; align-items: center; }
  .ace-hero .score { font-size: 3.5rem; font-weight: 500; line-height: 1; letter-spacing: -0.02em; }
  .ace-chip { display: inline-flex; align-items: center; gap: 6px; border-radius: 8px;
    padding: 4px 12px; font-size: 0.8125rem; font-weight: 600; white-space: nowrap; }
  .ace-chip.pass { background: var(--md-success-container); color: #002106; }
  .ace-chip.fail { background: var(--md-error-container); color: #410e0b; }
  .ace-chip.flag { background: var(--md-warning-container); color: #261a00; }
  .ace-chip.info { background: var(--md-primary-container); color: var(--md-on-primary-container); }
  .ace-hero .lede { color: var(--md-on-surface-variant); margin-top: 8px; }
  .ace-meter { position: relative; height: 10px; border-radius: 5px; background: var(--md-surface-high);
    margin-top: 16px; grid-column: 1 / -1; }
  .ace-meter > div { height: 100%; border-radius: 5px; }
  .ace-meter > i { position: absolute; top: -5px; bottom: -5px; width: 2px; background: var(--md-on-surface); }
  .ace-meter-legend { grid-column: 1 / -1; display: flex; justify-content: space-between;
    font-size: 0.75rem; color: var(--md-on-surface-variant); }
  .ace-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(132px, 1fr)); gap: 12px; margin-bottom: 16px; }
  .ace-stat { background: var(--md-surface-container); border-radius: 12px; padding: 12px 16px; }
  .ace-stat b { display: block; font-size: 1.5rem; font-weight: 500; line-height: 1.2; }
  .ace-stat span { font-size: 0.75rem; color: var(--md-on-surface-variant); letter-spacing: 0.04em; }
  .ace-grid2 { margin-bottom: 16px; display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 420px), 1fr)); gap: 16px; }
  .ace-grid2 > .ace-card { margin-bottom: 0; }
  .ace-secrow { display: grid; grid-template-columns: minmax(96px, 140px) 1fr auto; gap: 12px;
    align-items: center; margin-bottom: 10px; font-size: 0.875rem; }
  .ace-secrow span:last-child { font-variant-numeric: tabular-nums; color: var(--md-on-surface-variant); }
  .ace-links { margin: 0; padding-left: 1.1rem; font-size: 0.9rem; line-height: 1.7; }
  .ace-links small { color: var(--md-on-surface-variant); }

  .ace-opt { display: grid; grid-template-columns: 32px 1fr; gap: 12px; padding: 12px 14px;
    border-radius: 12px; border: 1px solid var(--md-outline-variant); margin-bottom: 8px; }
  .ace-opt .k { width: 32px; height: 32px; border-radius: 16px; display: grid; place-items: center;
    font-weight: 600; background: var(--md-surface-high); }
  .ace-opt.right { background: #e7f6ec; border-color: var(--md-success); }
  .ace-opt.right .k { background: var(--md-success); color: #fff; }
  .ace-opt.mine { background: #fcecea; border-color: var(--md-error); }
  .ace-opt.mine .k { background: var(--md-error); color: #fff; }
  .ace-opt .t { font-weight: 500; }
  .ace-opt .why { font-size: 0.875rem; color: var(--md-on-surface-variant); margin-top: 4px; }
  .ace-opt .tag { font-size: 0.6875rem; font-weight: 700; letter-spacing: 0.06em; margin-left: 6px; }
  .ace-opt.right .tag { color: var(--md-success); }
  .ace-opt.mine .tag { color: var(--md-error); }
  .ace-q { font-size: 1.0625rem; line-height: 1.6; margin: 4px 0 14px; }
  .ace-note { border-radius: 12px; padding: 12px 16px; margin: 8px 0; font-size: 0.925rem; }
  .ace-note.miss { background: var(--md-error-container); color: #410e0b; }
  .ace-note.flag { background: var(--md-warning-container); color: #261a00; }
  .ace-note.ok { background: var(--md-success-container); color: #002106; }
  .ace-note.spot { background: #fff4d6; color: #261a00; }
  .ace-note.study { background: var(--md-primary-container); color: var(--md-on-primary-container); }
  .ace-note .lbl { display: block; font-size: 0.6875rem; font-weight: 700; letter-spacing: 0.08em;
    text-transform: uppercase; opacity: 0.8; margin-bottom: 2px; }
  .ace-meta { font-size: 0.8125rem; color: var(--md-on-surface-variant); }
  [data-testid="stExpander"] details { border-radius: 12px !important; }
  .st-key-splitterjs { position: absolute !important; width: 0; height: 0; overflow: hidden; }

  /* --- adaptive layout --- */
  @media (max-width: 1000px) {
    /* Too narrow for two panes: the panel goes under the question and the splitter hides. */
    [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .st-key-studypanel) { flex-wrap: wrap !important; }
    [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .st-key-studypanel) > [data-testid="stColumn"]:first-child,
    [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .st-key-studypanel) > [data-testid="stColumn"]:last-child {
      flex: 1 1 100% !important; padding: 0 !important; }
    .ace-splitter { display: none; }
    .st-key-studypanel { position: static; max-height: none; margin-top: 16px; }
    .ace-hdr .mid { gap: 1rem; }
    .st-key-examnav [data-testid="stColumn"]:has(.ace-progress) { display: none; }
  }
  @media (max-width: 720px) {
    :root { --ace-nav: 64px; }
    .ace-hdr .mid > div:not(:first-child) { display: none; }
    .ace-hdr .who small { display: none; }
    .ace-clock { font-size: 1.1rem; padding: 4px 10px; }
    .st-key-examnav .stButton > button { padding-left: 6px; padding-right: 6px; font-size: 0.8125rem; }
    .ace-hero { grid-template-columns: 1fr; }
  }
  @media (max-width: 560px) {
    /* Phone: the nav keeps its icons; the labels stay for screen readers. */
    .st-key-examnav [data-testid="stColumn"]:not(:last-child) button [data-testid="stMarkdownContainer"] {
      position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
    .st-key-examnav [data-testid="stColumn"]:not(:last-child) button { gap: 0; }
    .ace-hdr { gap: 0.75rem; }
    .ace-hero .score { font-size: 2.75rem; }
  }
</style>
"""


def palette_css(session: ExamSession) -> str:
    """Per-button colour rules for the palette grid, keyed on widget state."""
    colours = {
        "answered": ("#0b57d0", "#ffffff", "#0b57d0"),
        "flagged": ("#ffdf99", "#261a00", "#7c5800"),
        "unanswered": ("#ffffff", "#444746", "#c4c7c5"),
    }
    rules = []
    for i in range(session.total):
        bg, fg, border = colours[session.status_of(i)]
        weight = "800" if i == session.index else "700"
        outline = (
            "box-shadow: 0 0 0 2px #1f1f1f inset;" if i == session.index else ""
        )
        rules.append(
            f".st-key-pal_{i} button {{ background:{bg} !important; color:{fg} !important;"
            f" border:1px solid {border} !important; font-weight:{weight} !important; {outline} }}"
        )
    return "<style>" + "\n".join(rules) + "</style>"


# The splitter between the question and the study panel. Streamlit can't drag a
# column edge, so this script runs in the page itself: it adds a handle to the panel
# column and sets --ace-split, which the stylesheet uses as the question's width.
# The width is kept per browser in localStorage. Pointer, touch and keyboard
# (arrows, Home, End) all work; double-click resets it.
SPLITTER_JS = r"""
(function () {
  var P = window.parent, d = P.document;
  if (d.getElementById("ace-splitter-js")) { return; }
  var s = d.createElement("script");
  s.id = "ace-splitter-js";
  s.textContent = "(" + function () {
    var KEY = "ace-split", MIN = 30, MAX = 75, DEF = 60, d = document, v = DEF;
    try { var saved = parseFloat(localStorage.getItem(KEY)); if (saved >= MIN && saved <= MAX) { v = saved; } } catch (e) {}
    function apply(x, save) {
      v = Math.round(Math.min(MAX, Math.max(MIN, x)) * 10) / 10;
      d.documentElement.style.setProperty("--ace-split", v + "%");
      var h = d.querySelector(".ace-splitter");
      if (h) { h.setAttribute("aria-valuenow", String(Math.round(v))); }
      if (save) { try { localStorage.setItem(KEY, String(v)); } catch (e) {} }
    }
    function attach() {
      var panel = d.querySelector(".st-key-studypanel");
      var col = panel && panel.closest('[data-testid="stColumn"]');
      if (!col || col.querySelector(":scope > .ace-splitter")) { return; }
      var row = col.parentElement, h = d.createElement("div");
      h.className = "ace-splitter";
      h.tabIndex = 0;
      h.setAttribute("role", "separator");
      h.setAttribute("aria-orientation", "vertical");
      h.setAttribute("aria-label", "Resize the study panel");
      h.setAttribute("aria-valuemin", String(MIN));
      h.setAttribute("aria-valuemax", String(MAX));
      h.title = "Drag to resize. Double-click to reset.";
      h.innerHTML = '<div class="ace-grip"></div>';
      col.prepend(h);
      apply(v, false);
      h.addEventListener("pointerdown", function (e) {
        if (e.button !== 0) { return; }
        e.preventDefault();
        h.setPointerCapture(e.pointerId);
        d.body.classList.add("ace-resizing");
        function move(ev) {
          var r = row.getBoundingClientRect();
          apply((ev.clientX - r.left) / r.width * 100, false);
        }
        function up() {
          h.removeEventListener("pointermove", move);
          h.removeEventListener("pointerup", up);
          h.removeEventListener("pointercancel", up);
          d.body.classList.remove("ace-resizing");
          apply(v, true);
        }
        h.addEventListener("pointermove", move);
        h.addEventListener("pointerup", up);
        h.addEventListener("pointercancel", up);
      });
      h.addEventListener("dblclick", function () { apply(DEF, true); });
      h.addEventListener("keydown", function (e) {
        var step = e.shiftKey ? 10 : 2, k = e.key;
        if (k === "ArrowLeft") { apply(v - step, true); }
        else if (k === "ArrowRight") { apply(v + step, true); }
        else if (k === "Home") { apply(MIN, true); }
        else if (k === "End") { apply(MAX, true); }
        else { return; }
        e.preventDefault();
      });
    }
    // The panel fits between where it starts on screen and the bottom bar, so it never
    // runs under the bar before the page scrolls far enough for it to stick.
    var queued = false;
    function fit() {
      queued = false;
      var panel = d.querySelector(".st-key-studypanel");
      if (!panel) { return; }
      var navEl = d.querySelector(".st-key-examnav"), hdrEl = d.querySelector(".st-key-examheader");
      var nav = navEl ? navEl.getBoundingClientRect().height : 0;
      var hdr = hdrEl ? hdrEl.getBoundingClientRect().height : 0;
      var top = Math.max(panel.getBoundingClientRect().top, hdr + 16);
      d.documentElement.style.setProperty("--ace-panel-max", Math.max(240, innerHeight - top - nav - 16) + "px");
    }
    // Streamlit mutates the DOM constantly (the clock ticks every second), so the observer
    // only queues one attach-and-fit per frame, and both return at once without a panel.
    function queue() { if (!queued) { queued = true; requestAnimationFrame(function () { attach(); fit(); }); } }
    apply(v, false);
    attach();
    fit();
    new MutationObserver(queue).observe(d.body, { childList: true, subtree: true });
    d.addEventListener("scroll", queue, true);
    addEventListener("resize", queue);
  } + ")();";
  d.head.appendChild(s);
})();
"""


def install_splitter() -> None:
    """Load the splitter script into the page once; it re-attaches itself after reruns."""
    with st.container(key="splitterjs"):  # zero-size; the script works on the parent page
        st.iframe(f"<script>{SPLITTER_JS}</script>", height=1)


# --------------------------------------------------------------------------
# Session state
# --------------------------------------------------------------------------


def init_state() -> None:
    st.session_state.setdefault("screen", "home")
    st.session_state.setdefault("session", None)
    st.session_state.setdefault("attempt", None)
    st.session_state.setdefault("report", None)
    st.session_state.setdefault("candidate", "Candidate")
    st.session_state.setdefault("show_submit_confirm", False)
    st.session_state.setdefault("study_panel_pref", True)  # not a widget key, so it outlives the exam screen


def start_exam(mode: str, questions, duration: int) -> None:
    st.session_state.session = ExamSession(questions, mode=mode, duration_seconds=duration)
    st.session_state.attempt = None
    st.session_state.report = None
    st.session_state.report_caches = {}
    st.session_state.review_limit = REVIEW_PAGE
    st.session_state.report_error = None
    st.session_state.history_error = None
    st.session_state.show_submit_confirm = False
    st.session_state.screen = "exam"


def submit_exam(expired: bool = False) -> None:
    """Deferred grading: this is the only place answers are scored."""
    sess: ExamSession = st.session_state.session
    if expired:
        sess.time_expired = True

    attempt = sess.build_attempt()
    path = None
    try:  # the PDF is kept with the history; the app shows the same review on screen
        path = build_report(attempt, sess.questions, candidate=st.session_state.candidate,
                            out_dir=reports_dir())
        attempt.report_path = str(path)
    except Exception as exc:  # a PDF failure must never lose the score
        st.session_state.report_error = str(exc)

    try:
        record_attempt(attempt, history_path())
    except OSError as exc:  # a full or read-only disk must not lose the score either
        st.session_state.history_error = f"{history_path()}: {exc}"
    st.session_state.attempt = attempt
    st.session_state.report = path
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
            "window, the item's topic is not shown while you sit. On submission your score "
            "report opens here, reviewing your missed and flagged questions, with a PDF to "
            "download."
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
            seen = seen_question_ids(history_path()) if prefer_unseen else None
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
        history = load_history(history_path())
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
            for d, ds in load_history(history_path()).rolling_domain_accuracy().items():
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
            "<span><i class='ace-swatch' style='background:#0b57d0'></i>Answered</span>"
            "<span><i class='ace-swatch' style='background:#ffffff'></i>Unanswered</span>"
            "<span><i class='ace-swatch' style='background:#ffdf99'></i>Flagged for review</span>"
            "<span><i class='ace-swatch' style='background:#1f1f1f'></i>Current item</span>"
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
    if revealed:  # mark the answer, and a wrong pick, in the list itself
        marks = {q.correct_answer: ("#e7f6ec", "var(--md-success)")}
        if choice and choice != q.correct_answer:
            marks[choice] = ("#fcecea", "var(--md-error)")
        st.markdown("<style>" + "".join(
            f".st-key-radio_{q.id} div[role='radiogroup'] > :nth-child({OPTION_KEYS.index(k) + 1}) label"
            f" {{ background: {bg}; border-color: {line} !important; }}"
            for k, (bg, line) in marks.items()) + "</style>", unsafe_allow_html=True)

    # ---- learning-mode feedback ----------------------------------------
    if not sess.is_timed:
        c1, c2 = st.columns([1.4, 3])
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
            if st.session_state.study_panel_pref:
                return  # the study panel carries the option analysis, command and links
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
        c1, c2, c3, c4, c5 = st.columns([1, 1, 1.3, 3, 1.3], vertical_alignment="center")

        if c1.button("Previous", icon=":material/chevron_left:", use_container_width=True,
                     disabled=sess.index == 0):
            sess.prev_question()
            st.rerun()

        if c2.button("Next", icon=":material/chevron_right:", icon_position="right",
                     use_container_width=True, disabled=sess.index >= sess.total - 1):
            sess.next_question()
            st.rerun()

        flagged = sess.current.id in sess.flagged
        if c3.button("Unflag" if flagged else "Flag for Review",
                     icon=":material/flag:" if not flagged else ":material/outlined_flag:",
                     use_container_width=True,
                     type="secondary"):
            sess.toggle_flag()
            st.rerun()

        with c4:
            done = sess.answered_count
            st.markdown(
                f"<div class='ace-progress'>"
                f"{done} of {sess.total} answered"
                f"<div class='ace-bar' style='margin-top:0.3rem'>"
                f"<div style='width:{done/sess.total*100:.1f}%;background:var(--md-primary)'></div>"
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
    st.caption("Submitting is final. Your score report opens here, with a PDF to download.")

    c1, c2 = st.columns(2)
    if c1.button("Return to exam", use_container_width=True):
        st.session_state.show_submit_confirm = False
        st.rerun()
    if c2.button("Submit now", type="primary", use_container_width=True):
        st.session_state.show_submit_confirm = False
        submit_exam()
        st.rerun()


def _md(text: str) -> str:
    """Theory Markdown for st.markdown, which would otherwise read $ as LaTeX."""
    out, fenced = [], False
    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            fenced = not fenced
        elif not fenced:  # code blocks are shown as written
            line = re.sub(r"^#{1,6} +(.+)$", r"**\1**", line)  # headings would dwarf the panel
            line = line.replace("$", "\\$")
        out.append(line)
    return "\n".join(out)


def _section_links(sec: study_links.Section) -> str:
    links = f"<a href='{sec.url}' target='_blank'>Read on the theory site ↗</a>"
    if sec.video_url:
        links += (f" &nbsp;·&nbsp; <a href='{sec.video_url}' target='_blank'>"
                  f"Watch from {sec.video_clock} ↗</a>")
    return f"<div class='ace-panel-links'>{links}</div>"


def render_study_panel(sess: ExamSession) -> None:
    """Learning mode: quick theory recall, and after checking, why the answer is right."""
    q = sess.current
    sections = study_links.sections_for(q)
    with st.container(key="studypanel"):
        st.markdown(f"<div class='ace-panel-h'>Study panel</div><b>{q.subtopic}</b>",
                    unsafe_allow_html=True)
        # After checking, the explanation is what's wanted first.
        if sess.is_revealed(q.id):
            why, recall = st.tabs(["✅ Why it's right", "📘 Quick recall"])
        else:
            recall, why = st.tabs(["📘 Quick recall", "✅ Why it's right"])
        with recall:
            for i, sec in enumerate(sections):
                with st.expander(sec.label, expanded=i == 0):
                    st.markdown(_section_links(sec), unsafe_allow_html=True)
                    st.markdown(_md(sec.text))
            card = study_links.recall_card(sections[0].part) if sections else None
            if card:
                with st.expander(f"Part {card.part} recall card"):
                    st.markdown(_section_links(card), unsafe_allow_html=True)
                    st.markdown(_md(card.text))
            st.caption(f"Whole course: [{study_links.video_title()}]({study_links.video_url()})")
        with why:
            if not sess.is_revealed(q.id):
                st.info("Choose an answer and press **Check answer** to see why it is right "
                        "or wrong. The recall tab doesn't give the answer away.")
                return
            k = q.correct_answer
            st.markdown(f"**The answer is {k}.** {q.options[k]}")
            if not restates(q.explanation.summary, q.explanation.option_breakdown[k]):
                st.markdown(q.explanation.summary)
            st.markdown(f"**Why {k} is right.** {q.explanation.option_breakdown[k]}")
            st.markdown("**Why the others are wrong**")
            st.markdown("\n".join(f"- **{o}.** {q.explanation.option_breakdown[o]}"
                                   for o in OPTION_KEYS if o != k))
            if q.explanation.gcloud_command:
                st.markdown("**Command**")
                st.code(q.explanation.gcloud_command, language="bash")
            st.markdown(f"**Spot it next time.** {q.summary}")
            if q.explanation.doc_ref:
                st.markdown(f"📄 [Google Cloud documentation]({q.explanation.doc_ref})")
            if sections:
                st.markdown("**Rewatch**")
                st.markdown("\n".join(
                    f"- [{s.label}]({s.url})" + (f" · [video {s.video_clock}]({s.video_url})"
                                                 if s.video_url else "")
                    for s in sections))


def screen_exam() -> None:
    sess: ExamSession = st.session_state.session
    st.markdown(palette_css(sess), unsafe_allow_html=True)

    render_header(sess)
    if sess.is_timed:
        render_palette(sess)
        render_question(sess)
        render_nav(sess)
    else:
        pal, tog = st.columns([5, 1.2], vertical_alignment="center")
        with pal:
            render_palette(sess)
        with tog:
            st.session_state.study_panel_pref = st.toggle(
                "Study panel", value=st.session_state.study_panel_pref,
                help="Theory recall for this question, and after checking, the full "
                     "explanation. Drag the divider to resize it.")
        if st.session_state.study_panel_pref:
            install_splitter()
            main, side = st.columns([3, 2], gap=None)
            with main:
                render_question(sess)
                render_nav(sess)
            with side:
                render_study_panel(sess)
        else:
            render_question(sess)
            render_nav(sess)

    if st.session_state.show_submit_confirm:
        confirm_submit(sess)


def _inline(text: str) -> str:
    """Bank text as HTML: escaped, with `code` and **bold** kept."""
    out = html.escape(text or "", quote=False)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    return re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", out)


def _links_html(sections, counts=None) -> str:
    """Theory sections as a list: the page on the site and the chapter in the video."""
    items = []
    for sec in sections:
        line = (f"<b>§{html.escape(sec.key)}</b> <a href='{sec.url}' target='_blank'>"
                f"{html.escape(sec.title)}</a>")
        if sec.video_url:
            line += f" · <a href='{sec.video_url}' target='_blank'>video {sec.video_clock}</a>"
        if counts:
            n = counts[sec.key]
            line += f" <small>· {n} item{'s' if n != 1 else ''}</small>"
        items.append(f"<li>{line}</li>")
    return f"<ul class='ace-links'>{''.join(items)}</ul>"


REVIEW_PAGE = 10  # reviewed questions rendered per page on the results screen


def _report_pdf(attempt, questions, candidate: str, cache: dict, all_items: bool):
    """A download callable for a report PDF, read or built only when someone downloads it.

    Streamlit runs it from a server thread, outside the script, so it must not touch
    st.session_state: everything it needs is bound here. ``cache`` keeps the path, and the
    error of a failed build, which the next rerun of the results screen shows; a failed
    build isn't retried on every click.
    """
    def build() -> bytes:
        if cache.get("error"):
            raise RuntimeError(cache["error"])
        path = cache.get("path")
        if path is None or not Path(path).exists():  # never built, or removed from reports/
            try:
                path = build_report(attempt, questions, candidate=candidate,
                                    out_dir=reports_dir(), all_items=all_items)
            except Exception as exc:
                cache["error"] = str(exc)
                raise
            cache["path"] = path
        return Path(path).read_bytes()
    return build


def render_report_summary(attempt, att: dict) -> None:
    passed = attempt.passed
    pct = attempt.score_pct
    colour = "var(--md-success)" if passed else "var(--md-error)"
    chip = ("<span class='ace-chip pass'>✓ Pass</span>" if passed
            else "<span class='ace-chip fail'>✗ Did not pass</span>")
    try:
        when = datetime.fromisoformat(attempt.finished_at).strftime("%d %B %Y, %H:%M")
    except (TypeError, ValueError):
        when = ""
    st.markdown(
        f"<div class='ace-card'><div class='ace-hero'>"
        f"<div class='score' style='color:{colour}'>{pct*100:.0f}%</div>"
        f"<div>{chip} <span class='ace-chip info'>{attempt.mode.title()} mode</span>"
        f"<div class='lede'>{attempt.correct_count} of {attempt.question_count} correct · "
        f"pass mark {PASS_THRESHOLD*100:.0f}%. {margin_lede(attempt.correct_count, attempt.question_count)}</div>"
        f"<div class='ace-meta'>{html.escape(st.session_state.candidate)} · {when} · "
        f"attempt <code>{attempt.attempt_id}</code></div></div>"
        f"<div class='ace-meter' role='img' aria-label='Score {pct*100:.0f}%, pass mark "
        f"{PASS_THRESHOLD*100:.0f}%'><div style='width:{pct*100:.1f}%;background:{colour}'></div>"
        f"<i style='left:{PASS_THRESHOLD*100:.0f}%'></i></div>"
        f"<div class='ace-meter-legend'><span>0%</span><span>pass mark "
        f"{PASS_THRESHOLD*100:.0f}%</span><span>100%</span></div>"
        f"</div></div>",
        unsafe_allow_html=True,
    )
    if attempt.time_expired:
        st.warning("Time expired — the exam was submitted automatically.")

    answers = attempt.answers
    wrong = sum(1 for a in answers if a.is_answered and not a.is_correct)
    flagged_ok = sum(1 for a in answers if a.flagged and a.is_correct)
    mins, secs = divmod(int(attempt.duration_seconds), 60)
    stats = [(f"{attempt.correct_count}/{attempt.question_count}", "Correct"),
             (str(wrong), "Answered wrongly"),
             (str(sum(1 for a in answers if not a.is_answered)), "Unanswered"),
             (str(flagged_ok), "Flagged, correct"),
             (f"{mins}m {secs:02d}s", "Time used")]
    st.markdown("<div class='ace-stats'>" + "".join(
        f"<div class='ace-stat'><b>{v}</b><span>{k}</span></div>" for v, k in stats) + "</div>",
        unsafe_allow_html=True)

    rows = []
    for ds in attempt.domain_scores():
        c = "var(--md-success)" if ds.pct >= PASS_THRESHOLD else "var(--md-error)"
        rows.append(
            f"<div class='ace-secrow'><span>{DOMAIN_SHORT[ds.domain]}</span>"
            f"<div class='ace-bar'><div style='width:{ds.pct*100:.1f}%;background:{c}'></div></div>"
            f"<span>{ds.correct}/{ds.total} · {ds.pct*100:.0f}%</span></div>")
    qmap = {q.id: q for q in st.session_state.session.questions}
    weak = [qmap[a["question_id"]] for a in att["answers"]
            if in_review(a) and a["question_id"] in qmap]
    study = ""
    if weak:
        ranked = study_links.rank_sections(weak)[:6]
        study = ("<div class='ace-card'><h3>Where to study next</h3>"
                 "<div class='ace-meta'>The theory behind your misses and flags, most first.</div>"
                 + _links_html([s for s, _ in ranked], {s.key: n for s, n in ranked})
                 + f"<div class='ace-meta'>Whole course: <a href='{study_links.video_url()}' "
                   f"target='_blank'>{html.escape(study_links.video_title())}</a></div></div>")
    st.markdown(
        "<div class='ace-grid2'>"
        "<div class='ace-card'><h3>Performance by section</h3>" + "".join(rows) + "</div>"
        f"<div class='ace-card'><h3>Timing</h3><div>{timing_facts(att)}</div></div>"
        + study + "</div>",
        unsafe_allow_html=True,
    )

    obj_rows = attempt.objective_scores()
    gaps = attempt.subtopic_gaps()
    if obj_rows or gaps:
        with st.expander("Performance by objective and subtopic", icon=":material/table_chart:"):
            a, b = st.columns(2, gap="medium")
            if obj_rows:
                a.dataframe(
                    [{"Objective": f"{o} {OBJECTIVES[o].title}", "Correct": f"{c}/{t}",
                      "Accuracy": f"{c/t*100:.0f}%"} for o, c, t in obj_rows],
                    use_container_width=True, hide_index=True)
            if gaps:
                b.dataframe(
                    [{"Weakest subtopics": s, "Correct": f"{c}/{t}", "Accuracy": f"{c/t*100:.0f}%"}
                     for s, c, t in gaps],
                    use_container_width=True, hide_index=True)


def render_review_item(n: int, rec, q, expanded: bool) -> None:
    """One reviewed question: the options explained, the verdict, the theory and links."""
    missed = not rec.is_correct
    kind = "miss" if missed else ("flag" if rec.flagged else "ok")
    icon = {"miss": ":red[:material/cancel:]", "flag": ":orange[:material/flag:]",
            "ok": ":green[:material/check_circle:]"}[kind]
    label = f"{icon} **Q{n} · {q.title}** · {DOMAIN_SHORT.get(q.domain, '')} · {q.objective}"
    with st.expander(label, expanded=expanded):
        st.markdown(
            f"<div class='ace-meta'>{html.escape(q.subtopic)} · {rec.seconds_spent:.0f}s spent · "
            f"{'flagged' if rec.flagged else 'not flagged'} · <code>{q.id}</code></div>"
            f"<div class='ace-q'>{_inline(q.question)}</div>",
            unsafe_allow_html=True)
        opts = []
        for k in OPTION_KEYS:
            cls, tag = "", ""
            if k == q.correct_answer:
                cls, tag = "right", ("CORRECT · YOUR ANSWER" if k == rec.selected else "CORRECT ANSWER")
            elif k == rec.selected:
                cls, tag = "mine", "YOUR ANSWER"
            opts.append(
                f"<div class='ace-opt {cls}'><div class='k'>{k}</div><div>"
                f"<span class='t'>{_inline(q.options[k])}</span>"
                + (f"<span class='tag'>{tag}</span>" if tag else "")
                + f"<div class='why'>{_inline(q.explanation.option_breakdown[k])}</div></div></div>")
        st.markdown("".join(opts), unsafe_allow_html=True)

        k = q.correct_answer
        if missed and not rec.selected:
            verdict = f"<b>You left it unanswered.</b> The correct answer is <b>{k}</b>."
        elif missed:
            verdict = f"<b>You answered {rec.selected}.</b> The correct answer is <b>{k}</b>."
        elif rec.flagged:
            verdict = (f"<b>You answered {k}, correctly</b>, but flagged it, so it's reviewed "
                       f"here as a guess.")
        else:
            verdict = f"<b>You answered {k}, correctly.</b> Reviewed to confirm the reasoning."
        # Option {k}'s own analysis is already on its card; add the summary only if it says more.
        why = ("" if restates(q.explanation.summary, q.explanation.option_breakdown[k]) else
               f"<div class='ace-note ok'><span class='lbl'>Why {k} is right</span>"
               f"{_inline(q.explanation.summary)}</div>")
        st.markdown(f"<div class='ace-note {kind}'>{verdict}</div>{why}", unsafe_allow_html=True)
        if q.explanation.gcloud_command:
            st.code(q.explanation.gcloud_command, language="bash")
        st.markdown(
            f"<div class='ace-note spot'><span class='lbl'>Spot it next time</span>"
            f"{_inline(q.summary)}</div>", unsafe_allow_html=True)

        sections = study_links.sections_for(q)
        if sections:
            sec = sections[0]
            st.markdown(f"<div class='ace-panel-h' style='margin-top:12px'>From the course · "
                        f"{html.escape(sec.label)}</div>", unsafe_allow_html=True)
            with st.container(height=280, border=True):
                st.markdown(_md(sec.text))
            st.markdown(
                "<div class='ace-note study'><span class='lbl'>Study next: the theory, and the "
                "video to rewatch</span>" + _links_html(sections) + "</div>",
                unsafe_allow_html=True)
        if q.explanation.doc_ref:
            st.markdown(f"<div class='ace-meta'>Reference: <a href='{q.explanation.doc_ref}' "
                        f"target='_blank'>{html.escape(q.explanation.doc_ref)}</a></div>",
                        unsafe_allow_html=True)


def screen_results() -> None:
    attempt = st.session_state.attempt
    sess: ExamSession = st.session_state.session
    att = attempt.model_dump(mode="json")

    top = st.columns([3, 1], vertical_alignment="center")
    top[0].markdown("## Score report and review")
    with top[1].container(horizontal_alignment="right"):
        if st.button("Return to start", icon=":material/home:", type="primary", key="home_top"):
            _return_home()

    if st.session_state.get("history_error"):
        st.error("This attempt could not be saved to your history, so note your score: "
                 f"{st.session_state.history_error}. Check ACE_STATE_DIR and its permissions.")

    render_report_summary(attempt, att)

    # ---- the review, and the PDF of the same review ---------------------
    st.markdown("### Review")
    bar = st.columns([3, 2], vertical_alignment="bottom")
    with bar[0]:
        scope = st.segmented_control(
            "The report reviews", ["Missed and flagged", "Every question"],
            default="Missed and flagged", required=True, key="review_scope",
            help="Each question shows every option explained, the theory from the course, "
                 "and links to the theory site and the video.")
    all_items = scope == "Every question"
    with bar[1].container(horizontal_alignment="right"):
        report = st.session_state.report
        caches = st.session_state.setdefault("report_caches", {})
        cache = caches.setdefault("full" if all_items else "short",
                                  {} if all_items else {"path": report})
        if cache.get("error"):
            st.error(f"The PDF could not be generated: {cache['error']}")
        elif st.session_state.get("report_error") and not all_items:
            st.error(f"The PDF could not be generated: {st.session_state.report_error}")
        else:
            kind = "report-full" if all_items else "report"
            st.download_button(
                "Download PDF report",
                _report_pdf(attempt, list(sess.questions), st.session_state.candidate, cache, all_items),
                icon=":material/download:", file_name=f"ACE-{kind}-{attempt.attempt_id}.pdf",
                mime="application/pdf", on_click="rerun")  # the rerun shows a failed build
    if report is not None:
        st.caption(f"A copy of the missed-and-flagged PDF is saved as `{Path(report).name}` "
                   f"in your reports folder.")

    qmap = {q.id: q for q in sess.questions}
    shown = [(n, rec) for n, rec in enumerate(attempt.answers, start=1)
             if rec.question_id in qmap and (all_items or rec.flagged or not rec.is_correct)]
    if not shown:
        st.success("Nothing to review: every answer was correct and none was flagged. "
                   "Choose **Every question** to go through the reasoning anyway.")
    # Expanders render their contents even when closed, so a long review is paged.
    limit = st.session_state.setdefault("review_limit", REVIEW_PAGE)
    for i, (n, rec) in enumerate(shown[:limit]):
        render_review_item(n, rec, qmap[rec.question_id], expanded=i == 0)
    if len(shown) > limit:
        if st.button(f"Show {min(REVIEW_PAGE, len(shown) - limit)} more of {len(shown) - limit} remaining",
                     icon=":material/expand_more:"):
            st.session_state.review_limit = limit + REVIEW_PAGE
            st.rerun()

    st.divider()
    if st.button("Return to start", icon=":material/home:", type="primary"):
        _return_home()


def _return_home() -> None:
    st.session_state.session = None
    st.session_state.attempt = None
    st.session_state.screen = "home"
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
