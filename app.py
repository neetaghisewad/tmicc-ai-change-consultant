# =============================================================================
# TMICC Change Management Consultant
# A transparent, rule-based Streamlit prototype. No paid API or AI model.
#
# This file contains only the screens (the user interface).
# The rules live in the "consultant" folder:
#   consultant/documents.py  - reads the five Word documents
#   consultant/retrieval.py  - searches them
#   consultant/knowledge.py  - general framework content (edit text here)
#   consultant/questions.py  - question type and framework routing rules
#   consultant/answers.py    - builds the source-labelled answer
# =============================================================================

import re
from collections import Counter

import streamlit as st

from consultant import answers, documents, knowledge, retrieval

APP_TITLE = "TMICC Change Management Consultant"

# Keep the five Word documents in the SAME GitHub folder as app.py.
# The list of files is defined in consultant/documents.py.
KNOWLEDGE_DOCUMENTS = documents.KNOWLEDGE_DOCUMENTS

# Framework summaries, benefits, limitations and keywords.
# They are defined once, in consultant/knowledge.py, and shared by every tab.
FRAMEWORKS = knowledge.FRAMEWORKS

# Keyword themes used by the "Analyse a challenge" tab.
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

@st.cache_data(show_spinner=False)
def load_knowledge():
    """Read the five Word documents (cached so it happens once)."""
    return documents.load_documents()


@st.cache_resource(show_spinner=False)
def load_knowledge_base():
    """Documents plus the search index used by the chat and the analysis."""
    return answers.build_knowledge_base(load_knowledge())


def keyword_score(text, keywords):
    """Count how many keywords appear in the text.

    Word endings are ignored, so "stakeholders" matches "stakeholder" and
    "cultural" matches "culture".
    """
    text_stems = set(retrieval.tokenize(text))
    score = 0
    matched = []
    for word in keywords:
        word_stems = retrieval.tokenize(word)
        if word_stems and all(item in text_stems for item in word_stems):
            score += 1
            matched.append(word)
    return score, matched

def select_frameworks(challenge, change_type, stage, manual_choice, max_frameworks):
    # Only the words the user typed are scored. The dropdown labels are not
    # searched for keywords (otherwise choosing "Implementation" would itself
    # score points); the change type is handled by the explicit rule below.
    combined = challenge
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

# ---------------------------------------------------------------------------
# "Ask the consultant" tab (chat)
# ---------------------------------------------------------------------------

def queue_question(text):
    """Called when an example-question button is clicked."""
    st.session_state["pending_question"] = text


def clear_conversation():
    st.session_state["chat_history"] = []


def ask_consultant(question):
    """Answer one question and add it to the conversation history.

    The previous answer's analysis is passed in so that follow-up questions
    such as "what are the risks of that?" keep their topic.
    """
    history = st.session_state.setdefault("chat_history", [])
    previous = history[-1]["analysis"] if history else None
    try:
        answer = answers.answer_question(question, load_knowledge_base(), previous)
        history.append({
            "question": question,
            "markdown": answer["markdown"],
            "analysis": answer["analysis"],
        })
    except Exception as exc:  # never let one bad question break the app
        history.append({
            "question": question,
            "markdown": (
                "Sorry, I could not process that question because of an internal error "
                f"(`{type(exc).__name__}`). Please try rephrasing it."
            ),
            "analysis": previous,
        })


def render_chat_tab():
    st.header("Ask the consultant")
    st.caption(
        "Ask in your own words. Answers are assembled by rules from your five Word documents "
        "and from built-in general guidance. Every statement is labelled with its source. "
        "This is not an AI model."
    )

    knowledge_base = load_knowledge_base()
    problems = [doc for doc in knowledge_base["documents"] if doc["error"]]
    if problems:
        st.error(
            "Some documents could not be read, so answers will be incomplete: "
            + ", ".join(doc["file"] for doc in problems)
        )

    history = st.session_state.setdefault("chat_history", [])

    with st.expander("Example questions", expanded=not history):
        for number, text in enumerate(knowledge.EXAMPLE_QUESTIONS):
            st.button(text, key=f"example_{number}", on_click=queue_question, args=(text,))

    # The conversation is drawn in this container, which sits above the
    # question box even though it is filled in afterwards.
    conversation = st.container()

    with st.form("ask_form", clear_on_submit=True):
        typed = st.text_area(
            "Your question",
            height=90,
            placeholder="Example: How should TMICC manage resistance from the Ben & Jerry's board?",
        )
        submitted = st.form_submit_button("Ask")

    question = st.session_state.pop("pending_question", None)
    if submitted and normalise(typed):
        question = normalise(typed)
    if question:
        ask_consultant(question)

    with conversation:
        if not history:
            st.info("No questions yet. Type one below or pick an example above.")
        for turn in history:
            with st.chat_message("user"):
                st.write(turn["question"])
            with st.chat_message("assistant"):
                st.markdown(turn["markdown"])

    if history:
        left, right = st.columns(2)
        with left:
            st.download_button(
                "Download conversation (Markdown)",
                data=answers.conversation_to_markdown(history),
                file_name="tmicc_consultant_conversation.md",
                mime="text/markdown",
            )
        with right:
            st.button("Clear conversation", on_click=clear_conversation)


def main():
    st.set_page_config(page_title=APP_TITLE, page_icon="🧭", layout="wide")
    st.title("🧭 " + APP_TITLE)
    st.caption("A transparent, rule-based consulting prototype for change challenges at TMICC.")

    with st.sidebar:
        st.subheader("About this app")
        st.write(
            "Ask a question or describe a change challenge. The app uses rules to choose "
            "frameworks, searches the five Word documents for relevant passages, and "
            "assembles a structured answer."
        )
        st.info("No live AI model, API key or paid service is used. Everything is rule-based.")
        st.subheader("Source labels")
        st.markdown(knowledge.LEGEND)
        st.subheader("Frameworks")
        st.write("Kotter • Pfeffer • Ritti & Levy • Schein")

    tab_chat, tab_analyse, tab_knowledge, tab_reference, tab_method = st.tabs([
        "Ask the consultant", "Analyse a challenge", "Knowledge base documents",
        "Framework reference", "How this app works",
    ])

    with tab_chat:
        render_chat_tab()

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
            st.caption(
                "All five documents are searched using the words in your description. "
                "Each passage is quoted exactly, with its file and section."
            )
            knowledge_base = load_knowledge_base()
            for doc in knowledge_base["documents"]:
                if doc["error"]:
                    st.caption(f"{doc['file']}: {doc['error']}")
            results = retrieval.search(knowledge_base["index"], analysis["challenge"], max_results=10)
            shown = answers.relevant(results, limit=8)
            for result in shown:
                passage = result["passage"]
                st.markdown(f"> {passage['text']}")
                st.caption(
                    f"Source: {documents.source_label(passage)}  •  matched words: "
                    + ", ".join(result["matched"])
                )
            if not shown:
                st.info(
                    "No relevant passage was found by the keyword search. "
                    "The documents may still contain useful information; try adding specific terms from them."
                )
            missing = retrieval.words_not_in_documents(knowledge_base["index"], analysis["challenge"])
            if missing:
                st.caption("Words in your description that appear nowhere in the documents: " + ", ".join(missing[:8]))

    with tab_knowledge:
        st.header("Knowledge base documents")
        st.write("The Word files must be stored in the repository's root folder beside `app.py`.")
        loaded_documents = load_knowledge()
        for doc in loaded_documents:
            if doc["error"]:
                st.error(f"**{doc['file']}** — {doc['error']}")
            elif doc["characters"] == 0:
                st.warning(f"**{doc['file']}** — opened, but no text was extracted.")
            else:
                st.success(
                    f"**{doc['file']}** — loaded ({doc['characters']:,} characters, "
                    f"{len(doc['passages'])} searchable passages)"
                )
                if doc["warning"]:
                    st.warning(doc["warning"])
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
**1. Reading the documents.** The five `.docx` files are read with Python's built-in libraries. Lines that Word stored separately are joined back into whole statements, and each statement remembers the heading it sits under (for example *RITTI.docx > DECISION 2 > LOSERS*).

**2. Understanding the question.** Rules look for words and phrases to decide the type of question (advice, diagnosis, plan, comparison, risks and benefits, stakeholders, a factual question, and so on). A question worded as a follow-up ("what are the risks of that?") reuses the topic of the previous one.

**3. Choosing frameworks.** Each framework scores points when it is named, when a routing topic or keyword matches, and when the best-matching passages come from its own document. One clear fit is used alone; two are combined; if none fits, the app says so and does not force one.

**4. Searching the documents.** All five documents are searched with a standard keyword-ranking formula (BM25). Word endings are ignored ("stakeholders" matches "stakeholder"), known abbreviations are expanded ("TSA", "B&J"), and closely related words are searched at a lower weight.

**5. Building the answer.** The layout depends on the type of question. Every statement carries one of three labels:
""")
        st.markdown(knowledge.LEGEND)
        st.markdown("""
**Important limitations**
- This is a rule-based tool. It does not use an AI model and does not understand language the way a person or a large language model does.
- It matches words, so a question phrased in unusual terms may be misclassified or may miss relevant passages.
- It never writes its own statements about TMICC. If the documents do not cover something, it says so and offers only general guidance.
- Timelines, owners and success measures in roadmaps are illustrative general guidance; the documents contain none.
- The documents themselves have not been checked against outside sources. Human review is required before acting on any recommendation.
""")

if __name__ == "__main__":
    main()
