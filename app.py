# =============================================================================
# TMICC Change Management Consultant
# A transparent, rule-based Streamlit prototype. No paid API or AI model.
# =============================================================================

import os
import re
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter

import streamlit as st

APP_TITLE = "TMICC Change Management Consultant"

# Keep these five Word documents in the SAME GitHub folder as app.py.
KNOWLEDGE_DOCUMENTS = [
    {"file": "KOTTER 8.docx", "topic": "Kotter"},
    {"file": "PFEFFER NETWORK MAP.docx", "topic": "Pfeffer"},
    {"file": "RITTI.docx", "topic": "Ritti & Levy"},
    {"file": "SCHEIN THREE.docx", "topic": "Schein"},
    {"file": "TMICC ORCHESTRATOR CONTEXT DOCUMENT.docx", "topic": "TMICC context"},
]

FRAMEWORKS = {
    "Kotter": {
        "title": "Kotter — change readiness and the 8-step model",
        "focus": "Whether the organisation is ready for change and which stage needs attention.",
        "summary": (
            "Kotter's model moves from creating urgency and building a guiding coalition "
            "through communicating a vision, enabling action, generating wins, sustaining "
            "acceleration and anchoring change in culture."
        ),
        "benefits": [
            "Provides a clear sequence and practical milestones.",
            "Highlights communication, leadership alignment and visible wins.",
            "Helps identify where momentum may be breaking down.",
        ],
        "limitations": [
            "Can appear too linear for complex, iterative change.",
            "May understate employee-led change and local differences.",
            "Progress through the steps is not always easy to measure objectively.",
        ],
        "keywords": [
            "urgency", "resistance", "communication", "vision", "leadership",
            "coalition", "milestone", "momentum", "readiness", "adoption",
            "training", "change fatigue", "buy-in", "implementation",
        ],
    },
    "Pfeffer": {
        "title": "Pfeffer — power, influence and dependencies",
        "focus": "Who holds influence, resources, information and approval power.",
        "summary": (
            "A power and influence lens examines dependencies, informal networks, "
            "control of scarce resources, decision rights and the people who can enable "
            "or block a change."
        ),
        "benefits": [
            "Makes informal influence and hidden dependencies visible.",
            "Helps identify sponsors, blockers and critical relationships.",
            "Supports a practical stakeholder-engagement plan.",
        ],
        "limitations": [
            "Power and influence can be difficult to measure reliably.",
            "May overemphasise politics if used without an ethical lens.",
            "Can overlook shared purpose, trust and intrinsic motivation.",
        ],
        "keywords": [
            "power", "influence", "stakeholder", "dependency", "dependencies",
            "approval", "resources", "network", "sponsor", "blocker",
            "decision", "authority", "politics", "informal", "control",
        ],
    },
    "Ritti & Levy": {
        "title": "Ritti & Levy — organisational politics and informal rules",
        "focus": "How interests, perceived winners and losers, and unwritten rules shape behaviour.",
        "summary": (
            "This lens considers the informal side of organisations: unwritten rules, "
            "competing interests, organisational politics, and how people respond when "
            "they believe a change may benefit or disadvantage them."
        ),
        "benefits": [
            "Surfaces concerns that formal organisation charts may miss.",
            "Helps anticipate perceived losses, conflict and resistance.",
            "Encourages attention to informal norms and everyday behaviour.",
        ],
        "limitations": [
            "It can be tempting to interpret every disagreement as self-interest.",
            "People's motives are difficult to infer without evidence.",
            "Political analysis should be balanced with structural and cultural analysis.",
        ],
        "keywords": [
            "winners", "losers", "unwritten", "rules", "politics", "conflict",
            "interests", "incentives", "status", "identity", "territory",
            "resistance", "informal", "fairness", "competition",
        ],
    },
    "Schein": {
        "title": "Schein — culture: artefacts, values and underlying assumptions",
        "focus": "Whether the change aligns with or challenges the organisation's culture.",
        "summary": (
            "Schein's culture model distinguishes visible artefacts, espoused values and "
            "deeper underlying assumptions. The deeper assumptions can strongly shape "
            "behaviour while remaining difficult to see or discuss."
        ),
        "benefits": [
            "Looks beyond formal messages to the assumptions driving behaviour.",
            "Helps explain why people may reject a change that looks sensible on paper.",
            "Connects leadership behaviour, everyday practices and stated values.",
        ],
        "limitations": [
            "Underlying assumptions are difficult to observe directly.",
            "Culture can vary across teams, sites and professional groups.",
            "Culture change often takes time and cannot be delivered by communication alone.",
        ],
        "keywords": [
            "culture", "values", "assumptions", "beliefs", "identity",
            "norms", "rituals", "artefacts", "artifacts", "behaviour",
            "behavior", "trust", "psychological safety", "legacy", "subculture",
        ],
    },
}

THEMES = {
    "Urgency and readiness": {
        "keywords": ["urgent", "urgency", "deadline", "readiness", "pressure", "fatigue", "adoption"],
        "weights": {"Kotter": 3, "Schein": 1},
    },
    "Stakeholders and influence": {
        "keywords": ["stakeholder", "sponsor", "influence", "power", "approval", "dependency", "network", "blocker"],
        "weights": {"Pfeffer": 3, "Ritti & Levy": 1},
    },
    "Resistance and competing interests": {
        "keywords": ["resistance", "conflict", "winners", "losers", "incentive", "politics", "fairness", "status"],
        "weights": {"Ritti & Levy": 3, "Kotter": 1, "Pfeffer": 1},
    },
    "Culture and identity": {
        "keywords": ["culture", "values", "assumptions", "beliefs", "identity", "legacy", "norms", "trust"],
        "weights": {"Schein": 3, "Kotter": 1},
    },
    "Communication and implementation": {
        "keywords": ["communication", "communicate", "training", "implementation", "vision", "milestone", "rollout"],
        "weights": {"Kotter": 3, "Schein": 1},
    },
}

def normalise(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()

def extract_docx_text(path):
    """Extract readable text from a .docx using Python's built-in libraries."""
    try:
        with zipfile.ZipFile(path, "r") as archive:
            xml_bytes = archive.read("word/document.xml")
        root = ET.fromstring(xml_bytes)
        namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        paragraphs = []
        for paragraph in root.findall(".//w:p", namespace):
            parts = [node.text or "" for node in paragraph.findall(".//w:t", namespace)]
            paragraph_text = normalise("".join(parts))
            if paragraph_text:
                paragraphs.append(paragraph_text)
        return "\n".join(paragraphs), None
    except FileNotFoundError:
        return "", "File not found in the same folder as app.py."
    except (zipfile.BadZipFile, KeyError, ET.ParseError, OSError) as exc:
        return "", f"Could not read this Word file: {exc}"

@st.cache_data(show_spinner=False)
def load_knowledge():
    documents = []
    for item in KNOWLEDGE_DOCUMENTS:
        text, error = extract_docx_text(item["file"])
        documents.append({
            "file": item["file"],
            "topic": item["topic"],
            "text": text,
            "error": error,
            "characters": len(text),
        })
    return documents

def keyword_score(text, keywords):
    lowered = text.lower()
    score = 0
    matched = []
    for word in keywords:
        if re.search(r"\b" + re.escape(word.lower()) + r"\b", lowered):
            score += 1
            matched.append(word)
    return score, matched

def select_frameworks(challenge, change_type, stage, manual_choice, max_frameworks):
    combined = f"{challenge} {change_type} {stage}"
    scores = Counter()
    reasons = {name: [] for name in FRAMEWORKS}

    for theme_name, theme in THEMES.items():
        score, matched = keyword_score(combined, theme["keywords"])
        if score:
            for framework, weight in theme["weights"].items():
                scores[framework] += score * weight
                reasons[framework].append(
                    f"{theme_name}: matched {', '.join(matched[:5])}"
                )

    # Structural change commonly creates both adoption and dependency questions.
    if change_type in ["Separation / demerger / becoming standalone", "Merger or integration"]:
        scores["Kotter"] += 2
        scores["Pfeffer"] += 2
        reasons["Kotter"].append("Structural change: implementation and readiness need attention.")
        reasons["Pfeffer"].append("Structural change: decision rights and dependencies may shift.")

    if not any(scores.values()):
        scores["Kotter"] = 1
        scores["Schein"] = 1
        reasons["Kotter"].append("Default starting lens because few specific keywords were provided.")
        reasons["Schein"].append("Default starting lens to check cultural fit and assumptions.")

    if manual_choice:
        selected = [name for name in manual_choice if name in FRAMEWORKS][:max_frameworks]
    else:
        selected = [name for name, score in scores.most_common(max_frameworks) if score > 0]

    if not selected:
        selected = ["Kotter"]

    return selected, scores, reasons

def relevant_passages(document_text, query, max_passages=3):
    """Return document sentences/paragraphs sharing words with the challenge."""
    if not document_text.strip():
        return []
    query_words = {
        word.lower() for word in re.findall(r"[A-Za-z][A-Za-z'-]{3,}", query)
        if word.lower() not in {
            "this", "that", "with", "from", "into", "there", "their", "about",
            "which", "where", "when", "have", "will", "would", "could", "should",
            "organisation", "organization", "change", "changes",
        }
    }
    chunks = [normalise(part) for part in re.split(r"(?<=[.!?])\s+|\n+", document_text) if normalise(part)]
    ranked = []
    for chunk in chunks:
        chunk_words = set(re.findall(r"[A-Za-z][A-Za-z'-]{3,}", chunk.lower()))
        overlap = len(query_words & chunk_words)
        if overlap:
            ranked.append((overlap, chunk))
    ranked.sort(key=lambda item: item[0], reverse=True)
    return [chunk for _, chunk in ranked[:max_passages]]

def build_actions(selected, challenge, stage):
    actions = []
    for name in selected:
        if name == "Kotter":
            actions.extend([
                "Clarify why the change is necessary now and what happens if it is delayed.",
                "Identify the weakest change step: leadership alignment, communication, removing barriers, short-term wins or embedding the change.",
                "Set one visible near-term milestone and communicate progress consistently.",
            ])
        elif name == "Pfeffer":
            actions.extend([
                "Map the stakeholders who control approvals, resources, information and operational access.",
                "Identify dependencies and informal influencers, then agree how each will be engaged.",
                "Make decision rights explicit so teams know who can decide, advise and unblock work.",
            ])
        elif name == "Ritti & Levy":
            actions.extend([
                "Ask which groups expect to gain, lose or carry extra work because of the change.",
                "Use confidential listening sessions to surface unwritten rules and concerns without assuming motives.",
                "Address perceived unfairness with transparent criteria, involvement and feedback routes.",
            ])
        elif name == "Schein":
            actions.extend([
                "Compare visible practices and leadership messages with the values the organisation says it holds.",
                "Explore assumptions behind resistance through interviews, observation and team discussion.",
                "Pilot new behaviours and reinforce them through leadership role-modelling and everyday routines.",
            ])
    # Preserve order while removing duplicate actions.
    unique = []
    for action in actions:
        if action not in unique:
            unique.append(action)
    return unique[:9]

def main():
    st.set_page_config(page_title=APP_TITLE, page_icon="🧭", layout="wide")
    st.title("🧭 " + APP_TITLE)
    st.caption("A transparent, rule-based consulting prototype for change challenges at TMICC.")

    with st.sidebar:
        st.subheader("About this app")
        st.write(
            "Describe a change challenge. The app uses keyword rules to suggest frameworks "
            "and searches the five Word documents for passages sharing words with your description."
        )
        st.info("No live AI model, API key or paid service is used. Framework selection is rule-based.")
        st.subheader("Frameworks")
        st.write("Kotter • Pfeffer • Ritti & Levy • Schein")

    tab_analyse, tab_knowledge, tab_reference, tab_method = st.tabs([
        "Analyse a challenge", "Knowledge base documents", "Framework reference", "How this app works"
    ])

    with tab_analyse:
        st.header("Describe the change challenge")
        challenge = st.text_area(
            "What is happening, and what is the main change-management problem?",
            placeholder="Example: As TMICC becomes standalone, teams are uncertain about decision rights, legacy systems and the new culture.",
            height=150,
        )
        col1, col2 = st.columns(2)
        with col1:
            change_type = st.selectbox("Type of change", [
                "Separation / demerger / becoming standalone",
                "Merger or integration",
                "Digital or technology transformation",
                "Culture or operating-model change",
                "Process or organisation redesign",
                "Other / not sure",
            ])
        with col2:
            stage = st.selectbox("Stage of the change", [
                "Planning", "Design", "Implementation", "Embedding / sustainment", "Not sure"
            ])

        st.subheader("Framework selection")
        selection_mode = st.radio(
            "How should frameworks be chosen?",
            ["Automatic (rules choose the most relevant)", "Manual (I choose)"],
            horizontal=True,
        )
        manual_choice = []
        if selection_mode.startswith("Manual"):
            manual_choice = st.multiselect(
                "Choose frameworks",
                list(FRAMEWORKS.keys()),
                default=["Kotter", "Schein"],
            )
        max_frameworks = st.slider("Maximum number of frameworks", min_value=1, max_value=4, value=3)

        if st.button("Analyse challenge", type="primary"):
            if len(normalise(challenge)) < 12:
                st.warning("Please describe the challenge in at least a sentence so the rules have something to assess.")
            else:
                selected, scores, reasons = select_frameworks(
                    challenge,
                    change_type,
                    stage,
                    manual_choice if selection_mode.startswith("Manual") else None,
                    max_frameworks,
                )
                st.session_state["analysis"] = {
                    "challenge": challenge,
                    "change_type": change_type,
                    "stage": stage,
                    "selected": selected,
                    "scores": dict(scores),
                    "reasons": reasons,
                }

        analysis = st.session_state.get("analysis")
        if analysis:
            st.divider()
            st.header("Consulting-style diagnosis")
            st.caption(
                f"Change type: {analysis['change_type']}  •  Stage: {analysis['stage']}"
            )

            st.subheader("1. Frameworks selected and why")
            for name in analysis["selected"]:
                framework = FRAMEWORKS[name]
                score = analysis["scores"].get(name, 0)
                st.markdown(f"**{framework['title']}**  _(rule relevance score: {score})_")
                st.write(framework["focus"])
                st.write("**Why selected**")
                framework_reasons = analysis["reasons"].get(name, [])
                if framework_reasons:
                    for reason in framework_reasons[:4]:
                        st.markdown(f"- {reason}")
                else:
                    st.markdown("- Manually selected by the user.")
                st.write(framework["summary"])

            st.subheader("2. Key diagnosis")
            for name in analysis["selected"]:
                st.markdown(f"- **{name}:** {FRAMEWORKS[name]['focus']}")

            st.subheader("3. Recommended actions")
            for action in build_actions(analysis["selected"], analysis["challenge"], analysis["stage"]):
                st.markdown(f"- {action}")

            st.subheader("4. Benefits of the selected frameworks")
            for name in analysis["selected"]:
                st.markdown(f"**{name}**")
                for benefit in FRAMEWORKS[name]["benefits"]:
                    st.markdown(f"- {benefit}")

            st.subheader("5. Limitations and risks")
            for name in analysis["selected"]:
                st.markdown(f"**{name}**")
                for limitation in FRAMEWORKS[name]["limitations"]:
                    st.markdown(f"- {limitation}")
            st.warning(
                "Treat this as a structured starting point, not a verified diagnosis. "
                "Validate assumptions with TMICC employees, leaders and evidence."
            )

            st.subheader("6. Relevant passages from the knowledge documents")
            knowledge = load_knowledge()
            any_passage = False
            query = f"{analysis['challenge']} {analysis['change_type']} {analysis['stage']}"
            for doc in knowledge:
                if doc["topic"] not in analysis["selected"] and doc["topic"] != "TMICC context":
                    continue
                if doc["error"]:
                    st.caption(f"{doc['file']}: {doc['error']}")
                    continue
                passages = relevant_passages(doc["text"], query)
                if passages:
                    any_passage = True
                    st.markdown(f"**{doc['topic']} — source: `{doc['file']}`**")
                    for passage in passages:
                        st.markdown(f"> {passage}")
            if not any_passage:
                st.info(
                    "No relevant passage was found by the simple word-overlap search. "
                    "The document may still contain useful information; try adding specific terms from it."
                )

    with tab_knowledge:
        st.header("Knowledge base documents")
        st.write("The Word files must be stored in the repository's root folder beside `app.py`.")
        knowledge = load_knowledge()
        for doc in knowledge:
            if doc["error"]:
                st.error(f"**{doc['file']}** — {doc['error']}")
            elif doc["characters"] == 0:
                st.warning(f"**{doc['file']}** — opened, but no text was extracted.")
            else:
                st.success(f"**{doc['file']}** — loaded ({doc['characters']:,} characters)")
                with st.expander(f"Preview: {doc['topic']}"):
                    st.text(doc["text"][:5000])
                    if len(doc["text"]) > 5000:
                        st.caption("Preview limited to the first 5,000 characters.")

    with tab_reference:
        st.header("Framework reference")
        st.write("General framework summaries, benefits and limitations are built into this prototype.")
        st.caption("The Word documents are searched separately for relevant text; their content does not automatically rewrite these summaries.")
        for name, framework in FRAMEWORKS.items():
            with st.expander(framework["title"]):
                st.markdown(f"**Focus:** {framework['focus']}")
                st.write(framework["summary"])
                st.markdown("**Benefits**")
                for item in framework["benefits"]:
                    st.markdown(f"- {item}")
                st.markdown("**Limitations**")
                for item in framework["limitations"]:
                    st.markdown(f"- {item}")

    with tab_method:
        st.header("How this app works")
        st.markdown("""
**1. Input:** You describe the challenge, change type and stage.

**2. Rule engine:** The app searches for predefined keywords and adds relevance points to frameworks. The score is a transparent heuristic, not a validated scientific measure.

**3. Framework selection:** The highest-scoring frameworks are suggested, or you can choose them manually.

**4. Report:** The app displays selection reasons, a structured diagnosis, actions, benefits and limitations.

**5. Document search:** The app extracts text from the five `.docx` files and returns short passages with overlapping words. This is a simple word-overlap search, not semantic understanding.

**Important limitations**
- The app does not use a live AI model and does not independently understand the organisation.
- The selected framework and recommendations depend on the words entered.
- The document search may miss relevant passages that use different wording.
- Human review and evidence from TMICC are required before acting on recommendations.
""")

if __name__ == "__main__":
    main()
