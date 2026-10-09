# =============================================================================
# TMICC Change Management Consultant
# -----------------------------------------------------------------------------
# A rule-based consulting prototype built with Streamlit.
#
# IMPORTANT: This app does NOT use a live AI model, an API key or any paid
# service. Everything is produced by the transparent Python rules and text
# templates you can read in this file.
#
# HOW THE FILE IS ORGANISED (read top to bottom):
#   PART 1  Knowledge base  - frameworks, themes, keywords, templates
#   PART 2  Rule engine     - small functions that score and select
#   PART 3  Report builder  - turns the results into the 5 output sections
#   PART 4  Streamlit pages - what the user sees
#
# HOW TO EDIT IT SAFELY:
#   - To make the app recognise a new word: add it to a "keywords" list in THEMES.
#   - To change which framework a theme points to: edit that theme's "weights".
#   - To add or reword advice: edit the entries in CONTENT.
#   You do not need to touch PART 2, 3 or 4 for any of those changes.
# =============================================================================

import re

import streamlit as st

APP_TITLE = "TMICC Change Management Consultant"

# =============================================================================
# PART 1 - KNOWLEDGE BASE
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
}

# ---- 1b. Themes --------------------------------------------------------------
# Each theme has:
#   label    - the name shown to the user
#   keywords - words/phrases searched for at the START of words in the challenge
#              (so "resist" also matches "resistance" and "resisting")
#   weights  - how strongly the theme points to each framework (0-3)
THEMES = {
    "urgency": {
        "label": "Urgency and performance pressure",
        "keywords": ["urgent", "urgency", "deadline", "crisis", "declin", "falling",
                     "competitor", "pressure", "losing", "cost", "quickly", "fast",
                     "complacen"],
        "weights": {"Kotter": 3, "Pfeffer": 1},
    },
    "vision": {
        "label": "Vision, direction and communication",
        "keywords": ["vision", "unclear", "confus", "communicat", "direction",
                     "purpose", "strategy", "message", "do not understand",
                     "don't understand", "uncertain"],
        "weights": {"Kotter": 3, "Schein": 1},
    },
    "resistance": {
        "label": "Resistance, anxiety and morale",
        "keywords": ["resist", "reluctan", "pushback", "push back", "oppos",
                     "unwilling", "fear", "anxious", "anxiety", "morale", "sceptic",
                     "skeptic", "refus", "disengag", "worried"],
        "weights": {"Kotter": 2, "Ritti & Levy": 2, "Schein": 2},
    },
    "power": {
        "label": "Power, authority and control of resources",
        "keywords": ["power", "influence", "authority", "control", "budget",
                     "resource", "depend", "decision", "veto", "gatekeep", "sponsor",
                     "approval", "hierarch"],
        "weights": {"Pfeffer": 3, "Ritti & Levy": 1},
    },
    "politics": {
        "label": "Politics, competing interests, winners and losers",
        "keywords": ["politic", "winner", "loser", "win", "lose", "conflict", "turf",
                     "silo", "agenda", "coalition", "rival", "job loss", "redundan",
                     "restructur", "stakeholder", "union", "blame", "disagree"],
        "weights": {"Ritti & Levy": 3, "Pfeffer": 2},
    },
    "culture": {
        "label": "Culture, values and habits",
        "keywords": ["culture", "cultural", "values", "behaviour", "behavior",
                     "mindset", "tradition", "norms", "habit", "the way we",
                     "identity", "heritage", "assumption", "legacy", "belief",
                     "ways of working"],
        "weights": {"Schein": 3, "Kotter": 1},
    },
    "integration": {
        "label": "Structural change: merger, integration or separation",
        "keywords": ["merger", "merg", "acquisition", "acquir", "integrat",
                     "demerger", "separat", "spin-off", "spin off", "carve",
                     "standalone", "stand-alone", "independent", "parent company",
                     "former parent"],
        "weights": {"Schein": 2, "Pfeffer": 2, "Kotter": 1},
    },
    "technology": {
        "label": "Technology, systems and process change",
        "keywords": ["system", "digital", "erp", "technology", "software", "process",
                     "automat", "tool", "data", "rollout", "roll-out", "roll out",
                     "implement", "workaround"],
        "weights": {"Kotter": 2, "Schein": 1, "Ritti & Levy": 1},
    },
    "sustaining": {
        "label": "Sustaining momentum and embedding change",
        "keywords": ["sustain", "embed", "stick", "revert", "slipping", "fatigue",
                     "momentum", "stall", "backslid", "old ways", "old habits",
                     "initiative overload"],
        "weights": {"Kotter": 3, "Schein": 2},
    },
}

# ---- 1c. Stakeholder groups the app can recognise in the text ---------------
STAKEHOLDERS = {
    "senior leaders": ["senior lead", "executive", "board", "ceo", "director", "top team"],
    "middle managers": ["middle manag", "line manag", "managers", "supervisor"],
    "frontline employees": ["frontline", "front-line", "employees", "staff", "workforce", "workers"],
    "trade unions and works councils": ["union", "works council"],
    "the former parent company": ["parent company", "former parent", "unilever"],
    "customers and retailers": ["customer", "retailer", "consumer"],
    "suppliers and partners": ["supplier", "partner", "vendor", "distributor"],
    "IT and digital teams": ["it team", "it department", "digital team", "technology team"],
    "HR": ["hr ", "human resources"],
    "finance": ["finance", "cfo"],
    "factory and supply chain teams": ["factory", "factories", "plant", "supply chain", "operations"],
    "investors": ["investor", "shareholder"],
}
# Groups outside the organisation. They are listed in the analysis, but are not
# inserted into recommendations such as "run listening sessions with ...".
EXTERNAL_GROUPS = ["the former parent company", "customers and retailers",
                   "suppliers and partners", "investors"]

# ---- 1d. Optional context the user can choose -------------------------------
# Each change type maps to (theme it strengthens, phrase used inside templates).
CHANGE_TYPES = {
    "Not specified": (None, "the change"),
    "Separation / demerger / becoming standalone": ("integration", "the separation"),
    "Merger / acquisition / integration": ("integration", "the integration"),
    "Restructuring / cost reduction": ("politics", "the restructuring"),
    "Digital / technology / process change": ("technology", "the new system or process"),
    "Culture or behaviour change": ("culture", "the culture change"),
    "New strategy or operating model": ("vision", "the new strategy"),
}
STAGES = ["Not specified", "Not started", "Planning", "Under way",
          "Stalling or losing momentum", "Embedding"]
LEVELS = ["Not specified", "Low", "Medium", "High"]

# ---- 1e. Sequencing phases for recommendations ------------------------------
PHASES = {1: "Diagnose", 2: "Mobilise", 3: "Deliver", 4: "Embed"}

# ---- 1f. Kotter's eight steps (used by the optional readiness check) --------
# Each item: (step name, phase, action template if this step is the weakest)
KOTTER_STEPS = [
    ("Create a sense of urgency", 1,
     "Rebuild the case for change with evidence that {who} find credible, because urgency scored lowest in your readiness check."),
    ("Build a guiding coalition", 2,
     "Form or strengthen a guiding coalition with enough credibility and authority across the affected units, because coalition strength scored lowest in your readiness check."),
    ("Form a strategic vision", 2,
     "Agree a short, concrete vision for {change} that states what will change and what will stay, because vision clarity scored lowest in your readiness check."),
    ("Communicate the vision", 2,
     "Communicate the vision for {change} repeatedly through leaders' own words and actions, because communication scored lowest in your readiness check."),
    ("Remove barriers and empower action", 3,
     "Identify and remove the structural, skills and system barriers that stop {who} acting, because empowerment scored lowest in your readiness check."),
    ("Generate short-term wins", 3,
     "Plan two or three visible short-term wins for {change} and credit the people who deliver them, because short-term wins scored lowest in your readiness check."),
    ("Sustain acceleration", 4,
     "Use early results to tackle the next, harder changes and avoid declaring success too early, because sustaining momentum scored lowest in your readiness check."),
    ("Anchor change in the culture", 4,
     "Link the new behaviours to recognition, promotion and induction so they outlast the project, because anchoring scored lowest in your readiness check."),
]

# ---- 1g. Content library -----------------------------------------------------
# One entry per (framework, theme). Each entry holds reusable templates:
#   questions - diagnostic questions
#   insight   - what this framework would say about this theme
#   rec       - one recommendation, with a phase (1-4) used for sequencing
#   risk      - the risk or trade-off attached to that recommendation
# Placeholders: {who} = stakeholder groups found in the text,
#               {change} = phrase for the change type chosen.
CONTENT = [
    # ---------------- urgency ----------------
    {"framework": "Kotter", "theme": "urgency", "phase": 1,
     "questions": [
         "What evidence (customer, cost, competitor or deadline data) shows {who} that staying the same is riskier than changing?",
         "How many of the leaders who must act would describe {change} as urgent today?"],
     "insight": "Your challenge describes time or performance pressure. Kotter argues that change stalls when urgency is felt by the top team but not by the people who must change their daily work.",
     "rec": "Build a short, evidence-based case for change (three to five facts and one deadline) and test it with {who} before any roll-out, so urgency is shared and not simply announced.",
     "risk": "Urgency built on fear can produce anxiety and short-term compliance instead of commitment."},
    {"framework": "Pfeffer", "theme": "urgency", "phase": 2,
     "questions": [
         "Who controls the resources (budget, people, data) needed to move quickly, and what do they need in return?"],
     "insight": "Under time pressure, whoever controls scarce resources gains influence. Speed depends on these dependencies more than on the formal plan.",
     "rec": "Map the critical resources for the first 90 days of {change} and secure explicit commitments from the people who control them before the timeline is published.",
     "risk": "Securing fast commitments can mean concessions to powerful units that restrict later choices."},

    # ---------------- vision ----------------
    {"framework": "Kotter", "theme": "vision", "phase": 2,
     "questions": [
         "Can {who} explain in two sentences what will be different after {change}, and why?",
         "Which messages about {change} currently contradict each other across leaders or channels?"],
     "insight": "Your challenge signals unclear direction or communication. In Kotter's model an under-communicated vision is a common reason for failure: people cannot act on what they cannot picture.",
     "rec": "Write a one-page vision for {change} (what changes, what stays, what it means for each affected group) and have leaders repeat it consistently through existing channels.",
     "risk": "A simple vision can over-promise; if early decisions contradict it, credibility falls quickly."},
    {"framework": "Schein", "theme": "vision", "phase": 3,
     "questions": [
         "Do the values stated in the new direction match what people see leaders actually reward and tolerate?"],
     "insight": "Schein separates espoused values from underlying assumptions. If the new message conflicts with what people believe is really valued, it will be heard as a slogan.",
     "rec": "Check the vision against day-to-day artefacts (targets, meeting routines, reward criteria) and change at least one visible artefact so the message is backed by evidence.",
     "risk": "Changing visible artefacts without deeper change can look cosmetic."},

    # ---------------- resistance ----------------
    {"framework": "Kotter", "theme": "resistance", "phase": 3,
     "questions": [
         "Which specific barriers (skills, systems, structures, sceptical managers) stop willing people from acting?",
         "Is the resistance about the goal, the pace, or the way {change} is being carried out?"],
     "insight": "Kotter treats much resistance as obstacles to remove: people who are willing may still be blocked by structures, skills gaps or their own managers.",
     "rec": "Run listening sessions with {who} to sort objections into goal, pace and method, then remove the two most frequently cited practical barriers and say publicly that you did.",
     "risk": "Listening raises expectations; if nothing visibly changes afterwards, resistance hardens."},
    {"framework": "Ritti & Levy", "theme": "resistance", "phase": 1,
     "questions": [
         "What exactly does each resisting group stand to lose: status, autonomy, job security or expertise?",
         "Who appears to agree in meetings but is quietly not cooperating?"],
     "insight": "Through the Ritti & Levy lens, resistance is often rational: people respond to what they expect to win or lose under the unwritten rules, more than to the official rationale.",
     "rec": "Produce a confidential winners-and-losers map covering {who}, and design a specific offer (role, development, recognition or protection) for each group that loses.",
     "risk": "Offers to losing groups cost money and may seem unfair to groups that supported the change from the start."},
    {"framework": "Schein", "theme": "resistance", "phase": 3,
     "questions": [
         "What past experience taught people that this kind of change is unsafe or will not last?",
         "What would {who} have to unlearn for {change} to work?"],
     "insight": "Schein links resistance to learning anxiety: people fear losing competence, identity or group membership. Unless psychological safety rises, extra pressure increases defensiveness.",
     "rec": "Lower learning anxiety for {who}: provide training, practice time and visible role-modelling by leaders before performance is judged under the new way of working.",
     "risk": "Building psychological safety takes time and can slow delivery against a fixed deadline."},

    # ---------------- power ----------------
    {"framework": "Pfeffer", "theme": "power", "phase": 1,
     "questions": [
         "Which individuals or units control what {change} depends on: budget, information, expertise or approval?",
         "Where does formal authority differ from real influence?"],
     "insight": "Pfeffer's view is that implementation is decided by power as much as by the quality of the analysis. The key question is whose cooperation the change depends on, and what those people depend on in turn.",
     "rec": "Draw a dependency map: list the five to eight people or units that {change} cannot proceed without, rate their support, and agree who will build the relationship with each.",
     "risk": "Focusing on powerful actors can sideline less powerful groups whose daily cooperation is still needed."},
    {"framework": "Ritti & Levy", "theme": "power", "phase": 2,
     "questions": [
         "Which unwritten rules decide who gets heard in decisions, and who is routinely bypassed?"],
     "insight": "Formal decision rights rarely describe how decisions are really made. Ritti & Levy stress knowing 'the ropes': the informal rules about whose approval matters.",
     "rec": "Before each major decision point, brief the informal influencers individually so that concerns surface in private and can be addressed before the formal meeting.",
     "risk": "Private briefings can look like deals behind closed doors unless they are followed by open communication."},

    # ---------------- politics ----------------
    {"framework": "Ritti & Levy", "theme": "politics", "phase": 1,
     "questions": [
         "Who gains and who loses power, resources or status from {change}?",
         "Which groups are competing to shape the outcome, and what does each one want?"],
     "insight": "Your challenge shows signs of competing interests. Ritti & Levy treat organisations as political arenas, in which change redistributes status and resources and creates winners and losers who act accordingly.",
     "rec": "Classify stakeholders ({who}) by what they gain or lose and by their influence, then set a distinct approach for each group: involve, negotiate, reassure or monitor.",
     "risk": "A written winners-and-losers analysis is sensitive; if it leaks it can damage trust."},
    {"framework": "Pfeffer", "theme": "politics", "phase": 2,
     "questions": [
         "Which coalition could block {change}, and what holds that coalition together?",
         "What sources of power does the change team have: sponsorship, expertise, information or allies?"],
     "insight": "Pfeffer suggests that where interests conflict, outcomes follow from coalitions and control of scarce resources. A change team without allies inside the affected units will be outvoted in practice.",
     "rec": "Build a cross-unit sponsoring coalition that includes at least one respected figure from each unit that could block {change}, and give them a real role in decisions.",
     "risk": "A broad coalition requires compromise, which can dilute the original ambition."},

    # ---------------- culture ----------------
    {"framework": "Schein", "theme": "culture", "phase": 1,
     "questions": [
         "Which visible artefacts (structures, rituals, language, workplace layout) express the current culture?",
         "Which taken-for-granted assumptions would {change} contradict?"],
     "insight": "Your challenge refers to culture, values or habits. Schein's three levels suggest that artefacts and stated values are easier to change than underlying assumptions, which drive behaviour without being discussed.",
     "rec": "Run a short culture diagnosis with mixed groups drawn from {who}: list artefacts, espoused values and the assumptions behind them, and mark which assumptions help and which hinder {change}.",
     "risk": "A culture diagnosis can surface uncomfortable truths that leaders are not ready to act on."},
    {"framework": "Kotter", "theme": "culture", "phase": 4,
     "questions": [
         "Which new behaviours have already produced a result that can be pointed to?"],
     "insight": "Kotter places culture last: new behaviours become 'the way we do things here' only after people see that they work.",
     "rec": "Anchor the new behaviours by building them into promotion, recognition and induction criteria once results are visible, in preference to opening with a values campaign.",
     "risk": "Leaving culture until late risks early gains being reversed by old habits."},

    # ---------------- integration / separation ----------------
    {"framework": "Schein", "theme": "integration", "phase": 2,
     "questions": [
         "Which assumptions were inherited from the previous or partner organisation, and which still fit?",
         "Where do two groups use the same words but mean different things?"],
     "insight": "Structural change brings together, or splits apart, groups with different learned assumptions. Schein would expect friction where those assumptions meet, even when the structure chart looks clear.",
     "rec": "Identify three or four inherited practices to keep, adapt or drop deliberately, and explain each choice so that the organisation's identity is rebuilt on purpose and not by default.",
     "risk": "Explicitly dropping inherited practices can be read as criticism of people's past work."},
    {"framework": "Pfeffer", "theme": "integration", "phase": 1,
     "questions": [
         "Which services, systems or decisions still depend on another organisation or unit, and until when?",
         "Who gains or loses bargaining power as these dependencies change?"],
     "insight": "Separation and integration redraw dependencies. From Pfeffer's resource-dependence perspective, units that control what others newly depend on (systems, data, shared services) gain power during the transition.",
     "rec": "List every critical dependency created or removed by {change}, name an owner and an end date for each, and escalate those without a credible alternative.",
     "risk": "Reducing dependencies quickly may raise cost or operational risk in the short term."},
    {"framework": "Kotter", "theme": "integration", "phase": 3,
     "questions": [
         "What early, visible result would prove that the new structure works better?"],
     "insight": "Large structural change has a long horizon, so Kotter's short-term wins matter: without visible proof within months, sceptics gain ground.",
     "rec": "Plan two or three short-term wins tied to the new structure (for example a faster decision or a simplified process) and publicise who delivered them.",
     "risk": "Chasing quick wins can pull effort away from harder structural work."},

    # ---------------- technology ----------------
    {"framework": "Kotter", "theme": "technology", "phase": 3,
     "questions": [
         "What stops users adopting the new system or process even when they agree with it?",
         "Which pilot group could show a result first?"],
     "insight": "Technology and process changes often fail at adoption, not installation. Kotter's steps on removing barriers and creating short-term wins apply directly.",
     "rec": "Pilot {change} with one willing team, fix the barriers they report, and use their result as the first short-term win before a wider roll-out.",
     "risk": "A pilot run with volunteers may not predict how reluctant teams will respond."},
    {"framework": "Schein", "theme": "technology", "phase": 2,
     "questions": [
         "Which current habits or workarounds does the new system make impossible, and why did they exist?"],
     "insight": "New tools carry assumptions about how work should be done, such as transparency and standardisation. Where these clash with existing assumptions, people rebuild old practices around the new tool.",
     "rec": "List the workarounds people rely on today and decide for each whether the new process should absorb it, replace it or explicitly retire it.",
     "risk": "Absorbing too many workarounds erodes the standardisation the new system was meant to bring."},
    {"framework": "Ritti & Levy", "theme": "technology", "phase": 2,
     "questions": [
         "Whose expertise, or control over information, becomes less valuable after the new system?"],
     "insight": "Systems redistribute information, and information is a source of status. Ritti & Levy would look for groups whose informal standing rests on knowledge that the system now makes available to everyone.",
     "rec": "Give people whose expertise is displaced a visible role in the new set-up, such as super-user, trainer or process owner.",
     "risk": "Giving roles to former experts can entrench old thinking unless expectations are made clear."},

    # ---------------- sustaining ----------------
    {"framework": "Kotter", "theme": "sustaining", "phase": 4,
     "questions": [
         "Which early gains are at risk of reversal, and what is pulling people back?",
         "Has success been declared too early?"],
     "insight": "Your challenge shows signs of stalling or change fatigue. Kotter warns against declaring victory too soon: until changes are embedded, momentum has to be actively maintained.",
     "rec": "Reset momentum: publish what has been achieved, name the next two priorities, and replace or re-energise sponsors who have disengaged.",
     "risk": "Pushing for more change in a fatigued organisation can increase turnover and cynicism."},
    {"framework": "Schein", "theme": "sustaining", "phase": 4,
     "questions": [
         "Which old assumption is confirmed every time people slip back?",
         "What do leaders pay attention to, measure and reward now?"],
     "insight": "Schein's embedding mechanisms explain reversion: culture is reinforced by what leaders pay attention to, measure and reward. If people revert, those signals probably still point to the old priorities.",
     "rec": "Align the embedding mechanisms: change what leaders measure, review and reward so that these point to the new way of working.",
     "risk": "Changing measures and rewards can have unintended effects, such as gaming of new targets."},
]

# Used when a framework is selected but none of its themes were detected
# (for example in manual mode).
DEFAULT_CONTENT = {
    "Kotter": {"framework": "Kotter", "theme": None, "phase": 1,
               "questions": ["Which of Kotter's eight steps has been skipped or rushed in {change}?",
                             "How would {who} rate the urgency, the coalition and the vision today?"],
               "insight": "No Kotter-specific signal was found in your text, so the eight steps are applied as a general checklist.",
               "rec": "Assess {change} against all eight Kotter steps and address the earliest weak step first, because later steps depend on earlier ones.",
               "risk": "Applying the eight steps as a rigid sequence can miss the need to revisit earlier steps."},
    "Pfeffer": {"framework": "Pfeffer", "theme": None, "phase": 1,
                "questions": ["Whose cooperation does {change} depend on, and what do they depend on?",
                              "What sources of influence does the change team have?"],
                "insight": "No power-specific signal was found in your text, so Pfeffer is applied as a general check on dependencies and influence.",
                "rec": "List the people and units that {change} depends on and rate each one's influence and support before committing to a plan.",
                "risk": "Ratings of influence and support are subjective and should be checked with more than one source."},
    "Ritti & Levy": {"framework": "Ritti & Levy", "theme": None, "phase": 1,
                     "questions": ["Who gains and who loses from {change}?",
                                   "Which unwritten rules will shape how {who} respond?"],
                     "insight": "No politics-specific signal was found in your text, so Ritti & Levy is applied as a general stakeholder check.",
                     "rec": "Create a simple stakeholder list for {change} showing what each group gains, what it loses and how much influence it has.",
                     "risk": "Stakeholder positions shift over time, so a single snapshot becomes outdated."},
    "Schein": {"framework": "Schein", "theme": None, "phase": 1,
               "questions": ["Which artefacts, espoused values and underlying assumptions characterise the organisation today?",
                             "Which assumptions would {change} challenge?"],
               "insight": "No culture-specific signal was found in your text, so Schein is applied as a general check on cultural fit.",
               "rec": "Describe the current culture at Schein's three levels and note where {change} fits it and where it conflicts.",
               "risk": "Underlying assumptions are hard to observe from a description alone."},
}

# Used only if fewer than three recommendations are available.
GENERAL_RECS = [
    {"framework": "General", "theme": None, "phase": 1,
     "rec": "Validate this diagnosis with a small number of interviews across {who} before acting on it.",
     "risk": "A small interview sample may not represent the whole organisation."},
    {"framework": "General", "theme": None, "phase": 3,
     "rec": "Name one accountable owner and one sponsor for {change}, with a simple plan of who does what by when.",
     "risk": "Single-point ownership can create a bottleneck if the owner lacks time or authority."},
    {"framework": "General", "theme": None, "phase": 4,
     "rec": "Agree three or four measures of progress (adoption, behaviour and results) and a review date, so the approach can be adjusted using evidence.",
     "risk": "Measures chosen early may track activity instead of real change."},
]

EXAMPLES = {
    "Becoming a standalone company": (
        "Following separation from the former parent company, the business must operate as a "
        "standalone organisation. Employees are anxious about job security, middle managers are "
        "resisting new ways of working and the legacy culture is still strong."),
    "New system roll-out": (
        "A new ERP system is being rolled out across the factories under a tight deadline. Supply "
        "chain teams still rely on old workarounds, and the IT team controls the budget and the data."),
    "Contested restructuring": (
        "Senior leaders disagree about a restructuring. Regional directors fear losing control of "
        "their budgets, there is conflict between functions about who wins and who loses, and the "
        "union is concerned about redundancies."),
}


# =============================================================================
# PART 2 - RULE ENGINE
# =============================================================================

def find_keywords(text, keywords):
    """Return the keywords that appear at the start of a word in the text."""
    found = []
    for keyword in keywords:
        if re.search(r"\b" + re.escape(keyword), text):
            found.append(keyword)
    return found


def detect_themes(text, change_type, urgency, resistance, stage):
    """Score every theme: 1 point per matched keyword, +2 for chosen context."""
    text = text.lower()
    themes = {}
    for key, theme in THEMES.items():
        matched = find_keywords(text, theme["keywords"])
        themes[key] = {"score": len(matched), "matched": matched, "context": []}

    def add_context(theme_key, points, reason):
        themes[theme_key]["score"] += points
        themes[theme_key]["context"].append(reason)

    boosted_theme = CHANGE_TYPES[change_type][0]
    if boosted_theme:
        add_context(boosted_theme, 2, "change type: " + change_type)
    if urgency == "High":
        add_context("urgency", 2, "urgency set to High")
    if resistance == "High":
        add_context("resistance", 2, "resistance set to High")
    elif resistance == "Medium":
        add_context("resistance", 1, "resistance set to Medium")
    if stage == "Stalling or losing momentum":
        add_context("sustaining", 2, "stage: stalling")
    elif stage == "Embedding":
        add_context("sustaining", 1, "stage: embedding")
    return themes


def score_frameworks(themes):
    """Framework score = sum of (theme score x that theme's weight)."""
    scores = {name: 0 for name in FRAMEWORKS}
    for key, result in themes.items():
        for framework, weight in THEMES[key]["weights"].items():
            scores[framework] += result["score"] * weight
    return scores


def select_frameworks(scores, max_frameworks):
    """Keep frameworks scoring at least half of the top score."""
    top = max(scores.values())
    if top == 0:
        return ["Kotter", "Schein"], "fallback"
    ranked = sorted(scores, key=lambda name: scores[name], reverse=True)
    chosen = [name for name in ranked if scores[name] >= 0.5 * top]
    return chosen[:max_frameworks], "auto"


def detect_stakeholders(text):
    text = text.lower() + " "
    return [group for group, words in STAKEHOLDERS.items() if find_keywords(text, words)]


def join_words(items):
    """['a', 'b', 'c'] -> 'a, b and c'"""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def entries_for(framework, themes):
    """Content entries for one framework, most relevant theme first."""
    matches = []
    for entry in CONTENT:
        if entry["framework"] != framework:
            continue
        theme_score = themes[entry["theme"]]["score"]
        if theme_score > 0:
            priority = theme_score * THEMES[entry["theme"]]["weights"][framework]
            matches.append((priority, entry))
    matches.sort(key=lambda pair: pair[0], reverse=True)
    return [entry for _, entry in matches]


def kotter_readiness(ratings):
    """Summarise the optional 1-5 ratings of Kotter's eight steps."""
    average = sum(ratings) / len(ratings)
    if average < 2.5:
        level = "Low"
    elif average < 3.75:
        level = "Moderate"
    else:
        level = "High"
    weakest_index = ratings.index(min(ratings))  # earliest step with the lowest score
    return {"average": average, "level": level, "weakest": weakest_index, "ratings": ratings}


def build_recommendations(selected, themes, readiness):
    """Pick 3-5 recommendations and put them in sequence (phase order)."""
    picked = []

    def add(entry):
        if len(picked) < 5 and entry["rec"] not in [p["rec"] for p in picked]:
            picked.append(entry)

    # Rule 1: the weakest Kotter step (if the readiness check was completed)
    if readiness and "Kotter" in selected:
        name, phase, action = KOTTER_STEPS[readiness["weakest"]]
        add({"framework": "Kotter", "theme": None, "phase": phase, "rec": action,
             "risk": "Self-rated readiness scores reflect one person's view and may be optimistic or pessimistic.",
             "trigger": "Kotter readiness check: weakest step is '" + name + "'"})

    # Rule 2: the most relevant recommendation from each selected framework
    ranked = {name: entries_for(name, themes) for name in selected}
    for name in selected:
        add(ranked[name][0] if ranked[name] else DEFAULT_CONTENT[name])

    # Rule 3: fill the remaining places, taking turns between frameworks
    for position in range(1, 4):
        for name in selected:
            if position < len(ranked[name]):
                add(ranked[name][position])

    # Rule 4: always give at least three
    for entry in GENERAL_RECS:
        if len(picked) < 3:
            add(entry)

    picked.sort(key=lambda entry: entry["phase"])  # sequence: diagnose -> embed
    return picked


def build_tradeoffs(themes, urgency):
    """Extra trade-offs that appear only when certain themes occur together."""
    def active(key):
        return themes[key]["score"] > 0

    tradeoffs = []
    if active("urgency") and active("resistance"):
        tradeoffs.append("**Speed versus buy-in:** moving fast meets the deadline but leaves less time to work through resistance; slowing down builds commitment but may miss the window.")
    if active("urgency") and active("culture"):
        tradeoffs.append("**Deadline versus depth:** cultural assumptions change slowly, so a tight timetable may deliver new structures before behaviour has caught up.")
    if active("politics") and active("vision"):
        tradeoffs.append("**Transparency versus room to negotiate:** open communication builds trust, but naming winners and losers too early can harden positions.")
    if active("integration") and active("culture"):
        tradeoffs.append("**Continuity versus a fresh identity:** keeping inherited practices reassures people, while replacing them signals a new start; doing both needs clear explanation.")
    if active("power") and active("resistance"):
        tradeoffs.append("**Using authority versus earning commitment:** sponsors can force decisions through, but imposed change is more likely to be quietly reversed.")
    if not tradeoffs:
        tradeoffs.append("**Focus versus coverage:** concentrating on the highest-scoring themes makes the plan manageable, but lower-scoring issues may still matter.")
    return tradeoffs


def analyse(text, change_type, urgency, resistance, stage, mode, manual_choice,
            max_frameworks, ratings):
    """Run every rule and return one dictionary with all the results."""
    themes = detect_themes(text, change_type, urgency, resistance, stage)
    scores = score_frameworks(themes)
    readiness = kotter_readiness(ratings) if ratings else None

    if mode == "manual" and manual_choice:
        selected, how = list(manual_choice), "manual"
    else:
        selected, how = select_frameworks(scores, max_frameworks)
    if readiness and "Kotter" not in selected:
        selected.append("Kotter")

    stakeholders = detect_stakeholders(text)
    internal = [group for group in stakeholders if group not in EXTERNAL_GROUPS]
    who = join_words(internal[:3]) if internal else "the people most affected"
    change = CHANGE_TYPES[change_type][1]

    return {
        "text": text, "themes": themes, "scores": scores, "selected": selected,
        "how": how, "stakeholders": stakeholders, "who": who, "change": change,
        "readiness": readiness, "urgency": urgency,
        "recommendations": build_recommendations(selected, themes, readiness),
        "tradeoffs": build_tradeoffs(themes, urgency),
        "keyword_hits": sum(len(t["matched"]) for t in themes.values()),
    }


# =============================================================================
# PART 3 - REPORT BUILDER (always the same five sections)
# =============================================================================

def fill(template, result):
    """Insert the detected stakeholders and change type into a template."""
    return template.format(who=result["who"], change=result["change"])


def explain_theme(key, result):
    """e.g. 'Resistance (matched: resist, fear; resistance set to High)'"""
    info = result["themes"][key]
    parts = []
    if info["matched"]:
        parts.append("matched words: " + ", ".join(info["matched"]))
    parts.extend(info["context"])
    return THEMES[key]["label"] + " (" + "; ".join(parts) + ")"


def section_frameworks(result):
    lines = []
    for name in result["selected"]:
        reasons = []
        for key, info in result["themes"].items():
            weight = THEMES[key]["weights"].get(name, 0)
            if info["score"] > 0 and weight > 0:
                reasons.append((info["score"] * weight, explain_theme(key, result)))
        reasons.sort(reverse=True)
        lines.append("**" + FRAMEWORKS[name]["title"] + "** (relevance score: "
                     + str(result["scores"][name]) + ")")
        lines.append("- *What it examines:* " + FRAMEWORKS[name]["focus"])
        if reasons:
            for _, reason in reasons[:3]:
                lines.append("- *Why selected:* " + reason)
        elif result["how"] == "manual":
            lines.append("- *Why selected:* you chose it manually; no matching signals were found in the text.")
        elif result["readiness"] and name == "Kotter":
            lines.append("- *Why selected:* you completed the Kotter readiness check.")
        else:
            lines.append("- *Why selected:* default choice, because no keywords were matched.")
        lines.append("")

    if result["how"] == "manual":
        lines.append("*Selection method: frameworks chosen manually by you.*")
    elif result["how"] == "fallback":
        lines.append("*Selection method: no keywords were recognised, so the app defaulted to Kotter "
                     "(process) and Schein (culture) as a general starting point. Add more detail "
                     "for a more specific selection.*")
    else:
        lines.append("*Selection method: automatic. Frameworks scoring at least half of the top "
                     "score were selected.*")

    others = [n for n in FRAMEWORKS if n not in result["selected"]]
    if others:
        lines.append("")
        lines.append("Not selected: " + ", ".join(
            n + " (score " + str(result["scores"][n]) + ")" for n in others) + ".")
    return "\n".join(lines)


def section_analysis(result):
    lines = []
    if result["stakeholders"]:
        lines.append("**Stakeholder groups recognised in your text:** "
                     + join_words(result["stakeholders"]) + ".")
    else:
        lines.append("**Stakeholder groups recognised in your text:** none. Naming the groups "
                     "involved will make the output more specific.")
    lines.append("")

    for name in result["selected"]:
        entries = entries_for(name, result["themes"])[:3] or [DEFAULT_CONTENT[name]]
        lines.append("#### " + name)
        for entry in entries:
            lines.append("- " + fill(entry["insight"], result))
        if name == "Kotter" and result["readiness"]:
            ready = result["readiness"]
            lines.append("- **Readiness self-assessment:** average " + format(ready["average"], ".1f")
                         + " out of 5 (" + ready["level"] + " readiness). Weakest step: "
                         + KOTTER_STEPS[ready["weakest"]][0] + " ("
                         + str(ready["ratings"][ready["weakest"]]) + "/5).")
        lines.append("")
        lines.append("*Diagnostic questions to investigate:*")
        questions = []
        for entry in entries:
            questions.extend(entry["questions"])
        for number, question in enumerate(questions[:5], start=1):
            lines.append(str(number) + ". " + fill(question, result))
        lines.append("")
    return "\n".join(lines)


def trigger_text(entry, result):
    if entry.get("trigger"):
        return entry["trigger"]
    if entry["theme"]:
        return explain_theme(entry["theme"], result)
    return "general good practice (no specific signal detected)"


def section_recommendations(result):
    lines = []
    for number, entry in enumerate(result["recommendations"], start=1):
        lines.append("**" + str(number) + ". " + PHASES[entry["phase"]] + " - "
                     + entry["framework"] + "**")
        lines.append(fill(entry["rec"], result))
        lines.append("- *Triggered by:* " + trigger_text(entry, result))
        lines.append("")
    lines.append("*Sequence: recommendations are ordered Diagnose, Mobilise, Deliver, Embed. "
                 "Earlier steps provide the evidence and support that later steps rely on.*")
    return "\n".join(lines)


def section_risks(result):
    lines = ["**Risks attached to the recommendations**"]
    for number, entry in enumerate(result["recommendations"], start=1):
        lines.append("- Recommendation " + str(number) + ": " + entry["risk"])
    lines.append("")
    lines.append("**Trade-offs to decide**")
    for tradeoff in result["tradeoffs"]:
        lines.append("- " + tradeoff)
    return "\n".join(lines)


def section_limitations(result):
    lines = [
        "- **This is a rule-based prototype, not an AI model.** It matches keywords in your text "
        "and fills pre-written templates. It does not understand meaning.",
        "- **Keyword matching can misread text.** For example, 'there is no resistance' still "
        "triggers the resistance theme, and issues described in unusual words are missed.",
        "- **It only knows what you typed.** It has no data about the organisation, its people "
        "or its performance, so every point is a hypothesis to test.",
        "- **Templates are reused.** Similar challenges receive similar wording.",
    ]
    for name in result["selected"]:
        lines.append("- **" + name + ":** " + FRAMEWORKS[name]["critique"])
    if result["keyword_hits"] < 3:
        lines.append("- **Low confidence for this run:** fewer than three keywords were matched, "
                     "so the selection rests on very little evidence.")
    if len(result["text"].split()) < 25:
        lines.append("- **Short description:** your challenge is under 25 words. More detail on "
                     "who is involved and what is going wrong will improve the output.")
    lines.append("- Use this output to structure thinking and discussion, and validate it with "
                 "interviews, data and professional judgement before acting.")
    return "\n".join(lines)


def build_sections(result):
    return [
        ("1. Frameworks selected and why", section_frameworks(result)),
        ("2. Analysis", section_analysis(result)),
        ("3. Sequenced recommendations", section_recommendations(result)),
        ("4. Risks and trade-offs", section_risks(result)),
        ("5. Limitations", section_limitations(result)),
    ]


def build_download(result, sections):
    parts = ["# " + APP_TITLE, "",
             "*Generated by a rule-based prototype. No AI model was used.*", "",
             "## Challenge", result["text"], ""]
    for title, body in sections:
        parts.extend(["## " + title, body, ""])
    return "\n".join(parts)


# =============================================================================
# PART 4 - STREAMLIT PAGES
# =============================================================================

def load_example():
    st.session_state["challenge"] = EXAMPLES[st.session_state["example_choice"]]


def page_analyse():
    st.subheader("Describe the change challenge")
    col_example, col_button = st.columns([3, 1])
    col_example.selectbox("Example challenges (optional)", list(EXAMPLES), key="example_choice")
    col_button.write("")
    col_button.button("Load example", on_click=load_example)

    text = st.text_area(
        "Your challenge", key="challenge", height=150,
        placeholder="Describe what is changing, who is involved and what is going wrong...")

    st.markdown("**Optional context** (improves the selection)")
    c1, c2, c3, c4 = st.columns(4)
    change_type = c1.selectbox("Type of change", list(CHANGE_TYPES))
    urgency = c2.selectbox("Urgency", LEVELS)
    resistance = c3.selectbox("Level of resistance", LEVELS)
    stage = c4.selectbox("Stage of the change", STAGES)

    ratings = None
    with st.expander("Optional: Kotter change readiness self-assessment"):
        if st.checkbox("Include a readiness check (rate each step from 1 = weak to 5 = strong)"):
            left, right = st.columns(2)
            ratings = []
            for index, (name, _, _) in enumerate(KOTTER_STEPS):
                column = left if index < 4 else right
                ratings.append(column.slider(str(index + 1) + ". " + name, 1, 5, 3))

    st.markdown("**Framework selection**")
    mode_label = st.radio(
        "How should frameworks be chosen?",
        ["Automatic (rules choose the most relevant)", "Manual (I choose)"],
        horizontal=True)
    manual_choice = []
    max_frameworks = 3
    if mode_label.startswith("Manual"):
        manual_choice = st.multiselect("Frameworks to apply", list(FRAMEWORKS),
                                       default=list(FRAMEWORKS))
    else:
        max_frameworks = st.slider("Maximum number of frameworks", 1, 4, 3)

    if st.button("Analyse challenge", type="primary"):
        if not text.strip():
            st.warning("Please describe the challenge first.")
        elif mode_label.startswith("Manual") and not manual_choice:
            st.warning("Please choose at least one framework.")
        else:
            mode = "manual" if mode_label.startswith("Manual") else "auto"
            st.session_state["result"] = analyse(
                text.strip(), change_type, urgency, resistance, stage, mode,
                manual_choice, max_frameworks, ratings)

    result = st.session_state.get("result")
    if result:
        st.divider()
        st.caption("Output produced by transparent Python rules and templates. No AI model is used.")
        sections = build_sections(result)
        for title, body in sections:
            st.subheader(title)
            st.markdown(body)
        st.download_button("Download report (Markdown)", build_download(result, sections),
                           file_name="tmicc_change_report.md", mime="text/markdown")


def page_reference():
    st.subheader("Framework reference")
    st.write("A short guide to the four frameworks used in this app.")
    for name, framework in FRAMEWORKS.items():
        with st.expander(framework["title"]):
            st.markdown("**Focus:** " + framework["focus"])
            st.markdown(framework["summary"])
            st.markdown("**Limitation:** " + framework["critique"])
            st.markdown("**General diagnostic questions**")
            for question in DEFAULT_CONTENT[name]["questions"]:
                st.markdown("- " + question.format(who="the people affected", change="the change"))
            if name == "Kotter":
                st.markdown("**The eight steps**")
                for index, (step, _, _) in enumerate(KOTTER_STEPS, start=1):
                    st.markdown(str(index) + ". " + step)


def page_method():
    st.subheader("How this app works")
    st.markdown(
        "This app is a **rule-based prototype**. It does not call an AI model or any "
        "external service, and nothing you type leaves the app.\n\n"
        "1. **Theme detection.** Your text is searched for the keywords below. Each match "
        "adds 1 point to its theme; optional context you select adds up to 2 points.\n"
        "2. **Framework scoring.** Each theme points to frameworks with a weight from 1 to 3. "
        "A framework's score is the sum of theme points multiplied by weight.\n"
        "3. **Selection.** Frameworks scoring at least half of the top score are selected.\n"
        "4. **Templates.** Questions, insights, recommendations and risks are pre-written for "
        "each framework and theme, and filled in with the stakeholders and change type detected.\n"
        "5. **Sequencing.** Three to five recommendations are chosen and ordered: "
        "Diagnose, Mobilise, Deliver, Embed.")
    rows = []
    for theme in THEMES.values():
        rows.append({
            "Theme": theme["label"],
            "Keywords": ", ".join(theme["keywords"]),
            "Framework weights": ", ".join(k + " " + str(v) for k, v in theme["weights"].items()),
        })
    st.table(rows)


def main():
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    st.title(APP_TITLE)
    st.caption("A rule-based prototype applying Kotter, Pfeffer, Ritti & Levy and Schein "
               "to organisational change challenges.")

    with st.sidebar:
        st.header("About")
        st.write("Describe a change challenge and the app selects the most relevant "
                 "frameworks, then produces a structured consulting-style diagnosis.")
        st.info("No live AI model is used. Results come from keyword rules and "
                "pre-written templates, which you can inspect under 'How this app works'.")

    tab_analyse, tab_reference, tab_method = st.tabs(
        ["Analyse a challenge", "Framework reference", "How this app works"])
    with tab_analyse:
        page_analyse()
    with tab_reference:
        page_reference()
    with tab_method:
        page_method()


main()
