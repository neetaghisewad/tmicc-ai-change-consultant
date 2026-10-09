# =============================================================================
# TMICC Change Management Consultant
# -----------------------------------------------------------------------------
# A rule-based consulting prototype built with Streamlit.
#
# IMPORTANT: This app does NOT use a live AI model, an API key or any paid
# service. It works in two transparent ways:
#   1. Keyword rules and pre-written templates (PART 1 and PART 2).
#   2. Text extracted from five Word documents stored next to this file, which
#      is matched to the user's challenge by shared words and quoted as written
#      (PART 3). The app does not understand the documents.
#
# HOW THE FILE IS ORGANISED (read top to bottom):
#   PART 1  Rules and templates  - frameworks, themes, keywords, templates
#   PART 2  Rule engine          - small functions that score and select
#   PART 3  Knowledge documents  - reads the .docx files and finds passages
#   PART 4  Report builder       - turns the results into the six report sections
#   PART 5  Streamlit pages      - what the user sees
#
# HOW TO EDIT IT SAFELY:
#   - To make the app recognise a new word: add it to a "keywords" list in THEMES.
#   - To change which framework a theme points to: edit that theme's "weights".
#   - To add or reword advice: edit the entries in CONTENT.
#   - To change the Word documents used: edit KNOWLEDGE_DOCUMENTS.
#
# REQUIREMENTS: only "streamlit". The Word files are read with Python's
# built-in zipfile and xml modules, so nothing else needs installing.
# =============================================================================

import os
import re
import xml.etree.ElementTree as ET
import zipfile

import streamlit as st

APP_TITLE = "TMICC Change Management Consultant"

# =============================================================================
# PART 1 - RULES AND TEMPLATES
# =============================================================================

# ---- 1a. The four frameworks -------------------------------------------------
FRAMEWORKS = {
    "Kotter": {
        "title": "Kotter - change readiness and the 8-step model",
        "focus": "How ready the organisation is and which step of the change process is weak.",
        "summary": (
            "Kotter describes change as eight steps, from creating urgency to anchoring "
            "new approaches in the culture. Later steps depend on earlier ones, so a "
            "skipped early step usually shows up as a problem later."
        ),
        "critique": (
            "Kotter's model is linear and leader-driven; real change is often messier, "
            "more iterative and shaped from below."
        ),
    },
    "Pfeffer": {
        "title": "Pfeffer - power, influence and dependencies",
        "focus": "Who the change depends on, and where real influence sits.",
        "summary": (
            "Pfeffer argues that getting things done depends on power and influence: "
            "who controls scarce resources, information and approvals, and who depends "
            "on whom."
        ),
        "critique": (
            "A power lens can under-weight goodwill, shared purpose and ethics, and "
            "power is hard to measure objectively."
        ),
    },
    "Ritti & Levy": {
        "title": "Ritti & Levy - stakeholders, winners and losers, organisational politics",
        "focus": "Who gains, who loses and which unwritten rules shape behaviour.",
        "summary": (
            "Ritti & Levy look at the informal side of organisations: the unwritten "
            "rules ('the ropes'), competing interests, and how change creates winners "
            "and losers who act on what they expect to gain or lose."
        ),
        "critique": (
            "A political lens can make every disagreement look like self-interest and "
            "relies on judgement about people's motives."
        ),
    },
    "Schein": {
        "title": "Schein - culture: artefacts, values and underlying assumptions",
        "focus": "Whether the change fits or contradicts the existing culture.",
        "summary": (
            "Schein describes culture at three levels: visible artefacts, espoused "
            "values and underlying assumptions. The deepest level drives behaviour "
            "and is the hardest to see and to change."
        ),
        "critique": (
            "Underlying assumptions are difficult to observe and culture change is "
            "slow, so findings are interpretive and take time to act on."
        ),
    },
