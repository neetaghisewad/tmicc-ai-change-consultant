
import streamlit as st

st.set_page_config(
    page_title="TMICC Change Management Consultant",
    page_icon="🍦",
    layout="wide"
)

st.title("TMICC Change Management Consultant")
st.caption("A multi-perspective change management decision-support prototype")
st.info(
    "Portfolio demonstration inspired by TMICC's separation from Unilever. "
    "This is a recreated prototype, not the original Copilot Studio deployment."
)

st.subheader("Describe your change challenge")
question = st.text_area(
    "What organisational change challenge are you facing?",
    placeholder=(
        "Example: How can TMICC protect the Ben & Jerry's culture "
        "while establishing independent decision-making?"
    ),
    height=120
)

frameworks = {
    "Kotter": {
        "focus": "Change readiness, urgency, leadership alignment and sequencing",
        "questions": [
            "Is there a clear case for change?",
            "Are leaders aligned around the vision?",
            "What barriers could prevent implementation?",
            "What short-term wins could build momentum?"
        ]
    },
    "Pfeffer": {
        "focus": "Power, influence, networks and organisational dependencies",
        "questions": [
            "Who controls critical resources and decisions?",
            "Which influential stakeholders need to be engaged?",
            "Where are the key dependencies?",
            "How might informal power affect implementation?"
        ]
    },
    "Ritti & Levy": {
        "focus": "Stakeholder interests, winners and losers, and organisational politics",
        "questions": [
            "Who gains or loses influence from the change?",
            "Which stakeholder interests may conflict?",
            "Where might resistance emerge?",
            "How can competing interests be addressed fairly?"
        ]
    },
    "Schein": {
        "focus": "Organisational culture, values and underlying assumptions",
        "questions": [
            "What visible cultural practices may be affected?",
            "Which stated values need to be protected?",
            "What underlying assumptions could drive resistance?",
            "How can leaders make the desired culture visible in practice?"
        ]
    }
}

def select_frameworks(text):
    q = text.lower()

    politics_terms = [
        "power", "influence", "politic", "conflict", "control",
        "stakeholder", "resistance", "winners", "losers", "interests"
    ]
    culture_terms = [
        "culture", "values", "belief", "identity", "ben and jerry",
        "assumption", "heritage", "norms", "belonging"
    ]
    change_terms = [
        "readiness", "urgency", "leadership", "implementation",
        "sequence", "momentum", "barrier", "communicat", "vision",
        "change plan", "short-term win"
    ]
    power_terms = [
        "dependency", "dependencies", "network", "resource",
        "decision rights", "authority", "negotiat"
    ]

    selected = []

    if any(term in q for term in change_terms):
        selected.append("Kotter")
    if any(term in q for term in power_terms):
        selected.append("Pfeffer")
    if any(term in q for term in politics_terms):
        selected.append("Ritti & Levy")
    if any(term in q for term in culture_terms):
        selected.append("Schein")

    if not selected:
        selected = ["Kotter", "Ritti & Levy"]

    return selected

if st.button("Analyse change challenge", type="primary"):
    if not question.strip():
        st.warning("Please describe a change challenge first.")
    else:
        selected = select_frameworks(question)

        st.header("1. Frameworks selected and why")
        for name in selected:
            st.markdown(f"**{name}** — {frameworks[name]['focus']}.")

        st.header("2. Analysis and diagnosis")
        st.write(
            "Use the questions below to examine the challenge. "
            "These are diagnostic prompts, not verified findings about TMICC."
        )

        for name in selected:
            with st.expander(f"{name} specialist perspective", expanded=True):
                for item in frameworks[name]["questions"]:
                    st.markdown(f"- {item}")

        st.header("3. Recommended next actions")
        st.markdown(
            "1. Establish the facts and identify affected stakeholders.\n"
            "2. Validate the main risks with people close to the change.\n"
            "3. Agree ownership, decision rights and success measures.\n"
            "4. Pilot an action and review the results before scaling."
        )

        st.header("4. Risks and trade-offs")
        st.markdown(
            "- Moving too quickly may increase resistance.\n"
            "- Excessive consultation may slow decisions.\n"
            "- A single framework may overlook cultural or political factors."
        )

        st.header("5. Limitations and blind spots")
        st.write(
            "This prototype selects perspectives using simple keyword rules. "
            "It does not independently verify facts, run separate AI agents, "
            "or establish what is actually happening inside TMICC. "
            "Validate its prompts and recommendations with evidence."
        )

st.divider()
st.caption(
    "Frameworks: Kotter; Pfeffer; Ritti & Levy; Schein. "
    "Educational decision-support prototype."
)
