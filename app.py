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
                     "complacen", "viab", "margin", "prove"],
        "weights": {"Kotter": 3, "Pfeffer": 1},
    },
    "vision": {
        "label": "Vision, direction and communication",
        "keywords": ["vision", "unclear", "confus", "communicat", "direction",
                     "purpose", "strategy", "message", "do not understand",
                     "don't understand", "narrative", "positioning"],
        "weights": {"Kotter": 3, "Schein": 1},
    },
    "resistance": {
        "label": "Resistance, uncertainty and morale",
        "keywords": ["resist", "reluctan", "pushback", "push back", "oppos",
                     "unwilling", "fear", "anxious", "anxiety", "morale", "sceptic",
                     "skeptic", "refus", "disengag", "worried", "uncertain",
                     "insecur", "job security", "distrust"],
        "weights": {"Kotter": 2, "Ritti & Levy": 2, "Schein": 2},
    },
    "power": {
        "label": "Power, authority and control of resources",
        "keywords": ["power", "influence", "authority", "control", "budget",
                     "resource", "depend", "decision", "veto", "gatekeep", "sponsor",
                     "approval", "hierarch", "network", "broker", "leverage", "bargain"],
        "weights": {"Pfeffer": 3, "Ritti & Levy": 1},
    },
    "politics": {
        "label": "Politics, competing interests, winners and losers",
        "keywords": ["politic", "winner", "loser", "win", "lose", "conflict", "turf",
                     "silo", "agenda", "coalition", "rival", "job loss", "redundan",
                     "restructur", "union", "blame", "disagree", "dispute",
                     "litigation", "lawsuit", "fence", "autonomy", "payoff"],
        "weights": {"Ritti & Levy": 3, "Pfeffer": 2},
    },
    "culture": {
        "label": "Culture, values and habits",
        "keywords": ["culture", "cultural", "values", "behaviour", "behavior",
                     "mindset", "tradition", "norms", "habit", "the way we",
                     "identity", "heritage", "assumption", "legacy", "belief",
                     "ways of working", "ben & jerry", "ben and jerry", "mission",
                     "dna", "bureaucra", "agile", "agility", "artefact", "artifact",
                     "subculture", "ritual"],
        "weights": {"Schein": 3, "Kotter": 1},
    },
    "integration": {
        "label": "Structural change: separation, spin-off, merger or integration",
        "keywords": ["merger", "merg", "acquisition", "acquir", "integrat",
                     "demerger", "separat", "spin", "spun", "carve",
                     "standalone", "stand-alone", "independent", "parent company",
                     "former parent", "unilever", "transitional", "tsa", "listing",
                     "listed", "ipo"],
        "weights": {"Schein": 2, "Pfeffer": 2, "Kotter": 1},
    },
    "technology": {
        "label": "Technology, systems and process change",
        "keywords": ["system", "digital", "erp", "technology", "software", "process",
                     "automat", "tool", "data", "rollout", "roll-out", "roll out",
                     "implement", "workaround", "shared service", "platform",
                     "migrat", "cutover", "cut-over"],
        "weights": {"Kotter": 2, "Schein": 1, "Ritti & Levy": 1},
    },
    "sustaining": {
        "label": "Sustaining momentum and embedding change",
        "keywords": ["sustain", "embed", "stick", "revert", "slipping", "fatigue",
                     "momentum", "stall", "backslid", "old ways", "old habits",
                     "initiative overload"],
        "weights": {"Kotter": 3, "Schein": 2},
    },
    "governance": {
        "label": "Governance, decision rights and reporting lines",
        "keywords": ["governance", "reporting line", "report to", "reports to",
                     "decision right", "decision-making", "accountab", "responsibilit",
                     "mandate", "board", "operating model", "matrix", "oversight",
                     "charter", "approval process", "role clarity", "roles"],
        "weights": {"Pfeffer": 3, "Ritti & Levy": 2, "Schein": 1},
    },
    "leadership": {
        "label": "Leadership alignment and sponsorship",
        "keywords": ["leader", "ceo", "cfo", "chair", "executive", "top team",
                     "senior team", "management team", "align", "misalign"],
        "weights": {"Kotter": 3, "Pfeffer": 2},
    },
    "stakeholders": {
        "label": "Stakeholders and outside pressure",
        "keywords": ["stakeholder", "investor", "shareholder", "activist", "retailer",
                     "customer", "consumer", "supplier", "regulator", "government",
                     "ngo", "media", "partner", "reputation"],
        "weights": {"Ritti & Levy": 3, "Pfeffer": 2},
    },
    "readiness": {
        "label": "Organisational readiness and capability",
        "keywords": ["readiness", "ready", "prepared", "capabilit", "capacity",
                     "skill", "training", "retrain", "confidence", "overload",
                     "workload", "talent"],
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
    "the Ben & Jerry's board": ["ben & jerry", "ben and jerry"],
    "customers and retailers": ["customer", "retailer", "consumer"],
    "suppliers and partners": ["supplier", "partner", "vendor", "distributor"],
    "IT and digital teams": ["it team", "it department", "digital team", "technology team"],
    "HR": ["hr ", "human resources"],
    "finance": ["finance", "cfo"],
    "factory and supply chain teams": ["factory", "factories", "plant", "supply chain", "operations"],
    "investors": ["investor", "shareholder", "activist"],
    "regulators and governments": ["regulator", "government"],
}
# Groups that are listed in the analysis but are not inserted into
# recommendations such as "run listening sessions with ...".
EXTERNAL_GROUPS = ["the former parent company", "the Ben & Jerry's board",
                   "customers and retailers", "suppliers and partners", "investors",
                   "regulators and governments"]

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
    # ---------------- governance ----------------
    {"framework": "Pfeffer", "theme": "governance", "phase": 1,
     "questions": [
         "Who has the final say on each contested decision, and is that written down?",
         "Which reporting lines changed, and who gained or lost decision rights as a result?"],
     "insight": "Your challenge refers to governance, decision rights or reporting lines. Pfeffer would treat unclear governance as a contest over authority: until decision rights are settled, influence goes to whoever controls approvals and information.",
     "rec": "Write a decision-rights map for the contested decisions in {change}: who decides, who must be consulted and who can block, and have the sponsor confirm it.",
     "risk": "Fixing decision rights early can lock in arrangements before the organisation understands its new needs."},
    {"framework": "Ritti & Levy", "theme": "governance", "phase": 2,
     "questions": [
         "Which groups gain or lose autonomy under the proposed governance and reporting lines?"],
     "insight": "Governance changes redistribute autonomy. Ritti & Levy would expect groups that lose a say to defend the old arrangement, openly or informally.",
     "rec": "For each governance change in {change}, list who gains and who loses a say, and agree in advance what each losing group is offered or guaranteed.",
     "risk": "Guarantees to groups that lose autonomy can limit how far the new operating model can go."},
    {"framework": "Schein", "theme": "governance", "phase": 2,
     "questions": [
         "What do current approval processes and reporting lines assume about who can be trusted to decide?"],
     "insight": "Governance rules are artefacts. Schein would ask what assumptions about hierarchy, consensus and trust they express, because new rules built on old assumptions tend to be worked around.",
     "rec": "Review two or three approval processes affected by {change} and test whether each still fits the way the organisation says it wants to work.",
     "risk": "Removing approval steps can increase errors until new habits of accountability form."},

    # ---------------- leadership ----------------
    {"framework": "Kotter", "theme": "leadership", "phase": 2,
     "questions": [
         "Do the senior leaders describe the purpose and priorities of {change} in the same way?",
         "Which leaders are visibly sponsoring the change, and which are waiting?"],
     "insight": "Your challenge refers to leadership or its alignment. Kotter's second step depends on a guiding coalition that is united in public and in private; a divided top team sends mixed signals that stall later steps.",
     "rec": "Hold a working session with the senior team to agree the three priorities for {change} and what each leader will say and do in the next month.",
     "risk": "A quick show of unity can hide real disagreement, which resurfaces under pressure."},
    {"framework": "Pfeffer", "theme": "leadership", "phase": 1,
     "questions": [
         "What does each senior leader control, and whose support does each need?"],
     "insight": "Leadership disagreement is also a matter of power bases. Pfeffer would look at what each leader controls and depends on, to predict which coalitions are possible.",
     "rec": "Map each senior leader's power base, dependencies and stance on {change}, and identify which relationships must be strengthened first.",
     "risk": "A map of leaders' power bases is sensitive and can damage trust if shared carelessly."},

    # ---------------- stakeholders ----------------
    {"framework": "Ritti & Levy", "theme": "stakeholders", "phase": 1,
     "questions": [
         "Which outside stakeholders can help or harm {change}, and what does each want?",
         "Who is undecided, and what would move them?"],
     "insight": "Your challenge refers to stakeholders or outside pressure. Ritti & Levy would sort them into those who gain, those who lose and those sitting on the fence, because the undecided often settle the outcome.",
     "rec": "Build a winners, losers and fence-sitters map for the main decision in {change}, and plan how to secure the undecided before the decision is announced.",
     "risk": "Courting undecided stakeholders can require concessions that weaken the original proposal."},
    {"framework": "Pfeffer", "theme": "stakeholders", "phase": 2,
     "questions": [
         "Which outside stakeholders control something the organisation needs, and how replaceable is it?"],
     "insight": "Outside stakeholders matter in proportion to what they control. Pfeffer's dependence view asks who needs whom more.",
     "rec": "Rank outside stakeholders by how much {change} depends on what they control, and assign a senior relationship owner to the top three.",
     "risk": "Concentrating on the most powerful stakeholders can neglect smaller ones who shape reputation."},

    # ---------------- readiness ----------------
    {"framework": "Kotter", "theme": "readiness", "phase": 1,
     "questions": [
         "Which of Kotter's eight steps would {who} say is weakest today?",
         "Do people have the skills, time and tools to work in the new way?"],
     "insight": "Your challenge refers to readiness or capability. Kotter would test readiness step by step: urgency, coalition, vision and communication must be in place before people are asked to act.",
     "rec": "Run a short readiness check on {change} with {who} against Kotter's eight steps, and start with the earliest weak step.",
     "risk": "A readiness check raises expectations that the gaps it finds will be addressed."},
    {"framework": "Schein", "theme": "readiness", "phase": 3,
     "questions": [
         "What would people have to stop doing, and what makes that feel unsafe?"],
     "insight": "Readiness is also psychological. Schein would ask whether people feel safe enough to learn new ways of working, or whether learning anxiety keeps them with familiar routines.",
     "rec": "Give {who} protected time, training and visible leader role-modelling for the new ways of working before performance is judged on them.",
     "risk": "Protected learning time competes with delivery deadlines."},
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
    "TMICC: brand decisions and Ben & Jerry's": (
        "As CEO of TMICC after the spin-off from Unilever, I am considering centralising brand "
        "decisions. The Ben & Jerry's independent board disputes governance authority and is "
        "resisting, employees still feel the Unilever culture, and we depend on Unilever for "
        "IT, HR and legal services."),
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


# ---- 1h. Framework notes -----------------------------------------------------
# General reasoning about each framework. These notes are built into the app.
# They are NOT taken from the Word documents and are not evidence about TMICC.
# raise       - evidence that would make the framework MORE relevant
# lower       - evidence that would make it LESS relevant
# strengths   - what the framework helps a consultant see or do
# limitations - what it may overlook, and what else is needed
FRAMEWORK_NOTES = {
    "Kotter": {
        "raise": "evidence of a process problem: people cannot explain why the change is happening, there is no agreed leadership coalition, or milestones are slipping.",
        "lower": "evidence that the plan and its communication are sound and the real blockers are disputes over authority or culture, which Kotter does not examine in depth.",
        "strengths": [
            "Gives the change a clear order of work, from building urgency to anchoring new behaviour, so gaps in the sequence become visible.",
            "Tests whether a real guiding coalition exists before effort is spent on communication and roll-out.",
            "Short-term wins give sceptics and outside audiences early proof that the change works.",
        ],
        "limitations": [
            "Assumes leaders already agree on the direction; where the disagreement is about the direction itself, better communication will not resolve it.",
            "Linear and top-down, while separation work on systems, governance and reporting lines runs in parallel and repeats steps.",
            "Says little about who holds power and leaves culture to the final step, so it needs Pfeffer, Ritti & Levy or Schein alongside it.",
        ],
    },
    "Pfeffer": {
        "raise": "evidence that progress depends on who controls resources or approvals: reliance on another organisation for services, unclear decision rights, or decisions being reopened after they are made.",
        "lower": "evidence that authority and dependencies are clear and accepted, so delays come from somewhere else.",
        "strengths": [
            "Maps who controls the resources, approvals and information the change depends on, and who depends on whom.",
            "Separates formal authority on the organisation chart from real influence over decisions.",
            "Shows where relationships are missing, so effort goes into building the connections the change needs.",
        ],
        "limitations": [
            "Reads disagreement as a contest for power and may miss objections that rest on sincerely held values.",
            "Has little to say about people with little power whose daily cooperation the change still needs.",
            "Power is hard to observe and the framework offers no implementation sequence, so it needs interview evidence and a process model such as Kotter.",
        ],
    },
    "Ritti & Levy": {
        "raise": "evidence of winners and losers or informal resistance: groups losing status or autonomy, people agreeing in meetings but not cooperating, or informal networks still deciding how things get done.",
        "lower": "evidence that stakeholder interests are broadly aligned and the problems are practical ones such as systems, skills and timing.",
        "strengths": [
            "Identifies who gains, who loses and who is undecided for each decision, which explains support and resistance.",
            "Surfaces the unwritten rules that shape how decisions are really made.",
            "Treats resistance as a reasonable response to expected loss, which points to negotiation and specific offers.",
        ],
        "limitations": [
            "Relies on judgement about people's motives, with a risk of labelling legitimate concerns as political.",
            "Describes the political landscape but gives little direction on what to do first.",
            "Winners and losers shift as the change proceeds, so the map dates quickly and is sensitive to record and share.",
        ],
    },
    "Schein": {
        "raise": "evidence that behaviour is driven by deep assumptions: old habits continuing after structures change, stated values contradicting what leaders reward, or one group acting as if different rules apply.",
        "lower": "evidence that people share the values and the obstacles are structural or political.",
        "strengths": [
            "Separates visible artefacts and stated values from the underlying assumptions that drive behaviour.",
            "Explains why inherited habits persist after structures and reporting lines have changed.",
            "Helps leaders see where stated values and real assumptions contradict each other, and where subcultures clash.",
        ],
        "limitations": [
            "Slow and interpretive: surfacing assumptions takes time, while separation deadlines are fixed.",
            "Can understate power: a clash described as cultural may also be a dispute about authority.",
            "Underlying assumptions cannot be read from documents or keywords; interviews, observation and workshops are needed.",
        ],
    },
}

# ---- 1i. How pairs of frameworks fit together -------------------------------
PAIR_NOTES = {
    ("Kotter", "Pfeffer"): {
        "complement": "Kotter supplies the sequence of steps; Pfeffer shows whose support each step needs, especially when building the guiding coalition.",
        "conflict": "Kotter assumes a coalition united by a shared vision, while Pfeffer assumes people pursue their own interests, so open communication (Kotter) can pull against quiet alliance-building (Pfeffer)."},
    ("Kotter", "Ritti & Levy"): {
        "complement": "Kotter says what to do next; Ritti & Levy explain why some groups will not follow, by showing what they expect to lose.",
        "conflict": "Kotter treats resistance as a barrier to remove, while Ritti & Levy treat it as a rational response to loss, which points to negotiation instead of removal."},
    ("Kotter", "Schein"): {
        "complement": "Kotter gives the process and Schein tests whether each step fits the culture; both end with embedding new behaviour.",
        "conflict": "Kotter builds urgency first and leaves culture to the final step, while Schein warns that pressure raises learning anxiety and that culture must be understood early. They imply different paces."},
    ("Pfeffer", "Ritti & Levy"): {
        "complement": "Pfeffer maps power based on resources and formal position; Ritti & Levy add the informal rules and the winners and losers.",
        "conflict": "The two overlap, so using both risks an overly political reading. They also differ in focus: Pfeffer concentrates on powerful actors, Ritti & Levy on every group, including those losing out."},
    ("Pfeffer", "Schein"): {
        "complement": "Pfeffer shows who is able to decide; Schein shows which beliefs make those decisions acceptable to others.",
        "conflict": "The same disagreement is read differently: as a contest for control (Pfeffer) or as a clash of values (Schein). The remedies differ too: negotiating authority, or building shared understanding."},
    ("Ritti & Levy", "Schein"): {
        "complement": "Both look at the informal organisation: Ritti & Levy at interests, Schein at the assumptions beneath them.",
        "conflict": "Ritti & Levy suggest offering something to groups that lose, while Schein suggests an objection may be about identity, which cannot be traded away."},
}

# ---- 1j. Suggested owners, deliverables and timeframes ----------------------
# Timeframe comes from the recommendation's phase (1-4).
PHASE_TIMEFRAMES = {1: "Weeks 1-4", 2: "Weeks 4-8", 3: "Months 3-6", 4: "Months 6-12"}

# (framework, theme) -> (suggested owner, deliverable).
# For general recommendations the second part of the key is the phase number.
ACTION_DETAILS = {
    ("Kotter", "urgency"): ("Change sponsor (CEO or programme sponsor)", "One-page case for change, tested with the affected groups"),
    ("Pfeffer", "urgency"): ("Programme director", "90-day resource plan with named commitments"),
    ("Kotter", "vision"): ("CEO and executive team, with internal communications", "One-page vision and a briefing pack for leaders"),
    ("Schein", "vision"): ("HR director", "List of artefacts checked against the vision, with one visible change made"),
    ("Kotter", "resistance"): ("Line managers, supported by the change team", "Summary of objections by goal, pace and method, and two barriers removed"),
    ("Ritti & Levy", "resistance"): ("Change lead with HR", "Confidential winners-and-losers map with an offer for each group that loses"),
    ("Schein", "resistance"): ("HR (learning and development) with line managers", "Training and practice plan, with role-modelling commitments from leaders"),
    ("Pfeffer", "power"): ("Programme director", "Dependency map with a relationship owner for each key person or unit"),
    ("Ritti & Levy", "power"): ("Change sponsor", "Pre-briefing log for each major decision point"),
    ("Ritti & Levy", "politics"): ("Change lead", "Stakeholder map with an agreed approach for each group"),
    ("Pfeffer", "politics"): ("Change sponsor", "Named sponsoring coalition with agreed decision roles"),
    ("Schein", "culture"): ("HR director with a neutral facilitator", "Culture diagnosis: artefacts, values and the assumptions that help or hinder"),
    ("Kotter", "culture"): ("HR director and executive team", "Updated promotion, recognition and induction criteria"),
    ("Schein", "integration"): ("Executive team", "Keep, adapt or drop list of inherited practices, with reasons"),
    ("Pfeffer", "integration"): ("Programme director with function heads", "Dependency register with an owner and end date for each item"),
    ("Kotter", "integration"): ("Programme director", "Short-term wins plan with two or three named wins"),
    ("Kotter", "technology"): ("System or process owner", "Pilot report showing barriers fixed and the first result"),
    ("Schein", "technology"): ("Process owner with team leaders", "Workaround register: absorb, replace or retire"),
    ("Ritti & Levy", "technology"): ("Function heads", "List of super-user, trainer and process-owner roles"),
    ("Kotter", "sustaining"): ("Change sponsor", "Progress statement and the next two priorities"),
    ("Schein", "sustaining"): ("Executive team with HR and finance", "Revised measures, review routines and reward criteria"),
    ("Pfeffer", "governance"): ("Change sponsor with the company secretary or legal lead", "Decision-rights map confirmed by the sponsor"),
    ("Ritti & Levy", "governance"): ("Change lead", "Gains-and-losses list for each governance change, with agreed offers"),
    ("Schein", "governance"): ("HR director with process owners", "Review of two or three approval processes against stated ways of working"),
    ("Kotter", "leadership"): ("CEO", "Agreed priorities and a one-month commitment from each senior leader"),
    ("Pfeffer", "leadership"): ("Change sponsor", "Confidential map of senior leaders' power bases, dependencies and stance"),
    ("Ritti & Levy", "stakeholders"): ("Change lead with corporate affairs", "Winners, losers and fence-sitters map with a plan for the undecided"),
    ("Pfeffer", "stakeholders"): ("CEO and executive team", "Ranked stakeholder dependency list with three relationship owners"),
    ("Kotter", "readiness"): ("Change lead", "Readiness check against the eight steps, with the earliest weak step named"),
    ("Schein", "readiness"): ("HR (learning and development) with line managers", "Learning plan with protected time and leader role-modelling"),
    ("Kotter", None): ("Change lead", "Eight-step assessment with the earliest weak step identified"),
    ("Pfeffer", None): ("Change lead", "List of key people and units rated for influence and support"),
    ("Ritti & Levy", None): ("Change lead", "Stakeholder list showing gains, losses and influence"),
    ("Schein", None): ("HR director", "Three-level description of the current culture"),
    ("General", 1): ("Change lead", "Interview summary confirming or correcting this diagnosis"),
    ("General", 3): ("Change sponsor", "Named owner and a who-does-what-by-when plan"),
    ("General", 4): ("Programme office", "Three or four progress measures and a review date"),
}

# One (owner, deliverable) pair for each of Kotter's eight steps, in order.
# Used when the readiness check produces a recommendation.
KOTTER_STEP_DETAILS = [
    ("Change sponsor (CEO or programme sponsor)", "Evidence-based case for change"),
    ("Change sponsor", "Named guiding coalition with agreed roles"),
    ("CEO and executive team", "Short written vision: what changes and what stays"),
    ("Executive team with internal communications", "Communication plan led by leaders"),
    ("Programme director with function heads", "Barrier list with an owner and removal date for each"),
    ("Programme director", "Short-term wins plan with two or three named wins"),
    ("Change sponsor", "Next-phase priorities based on early results"),
    ("HR director and executive team", "Updated recognition, promotion and induction criteria"),
]


# ---- 1k. Knowledge documents (Word files) ------------------------------------
# These five files must sit in the SAME folder as app.py (the top level of the
# GitHub repository). The names must match exactly, including capital letters
# and spaces. "topic" says what each document is used for.
CONTEXT_TOPIC = "TMICC context"
KNOWLEDGE_DOCUMENTS = [
    {"file": "KOTTER 8.docx", "topic": "Kotter"},
    {"file": "PFEFFER NETWORK MAP.docx", "topic": "Pfeffer"},
    {"file": "RITTI.docx", "topic": "Ritti & Levy"},
    {"file": "SCHEIN THREE.docx", "topic": "Schein"},
    {"file": "TMICC ORCHESTRATOR CONTEXT DOCUMENT.docx", "topic": CONTEXT_TOPIC},
]

# Common words ignored when matching a challenge to document passages.
STOP_WORDS = {
    "the", "and", "for", "are", "but", "not", "has", "had", "was", "its", "our", "who",
    "how", "why", "can", "all", "any", "new", "one", "two", "out", "use", "may", "too",
    "you", "his", "her", "him", "she", "get", "got", "now", "yet", "own", "way", "off",
    "about", "after", "also", "been", "being", "between", "could", "does", "from",
    "have", "into", "more", "most", "much", "must", "need", "other", "over", "should",
    "some", "such", "than", "that", "their", "them", "then", "there", "these", "they",
    "this", "those", "very", "were", "what", "when", "where", "which", "while", "will",
    "with", "would", "your", "still", "change", "changes", "company", "organisation",
    "organization", "want", "wants", "like", "just", "only", "each", "both", "many",
}

# Words are matched on their first six letters, so "cultural" matches "culture".
# Words listed here are kept whole because their first six letters would clash
# with a different word ("government" must not match "governance").
STEM_EXCEPTIONS = {"government": "government", "governments": "government"}

# A document line containing one of these is flagged as tentative wording.
TENTATIVE_WORDS = ["likely", "may", "might", "could", "probably", "possibly",
                   "perhaps", "appears", "seems", "emerging", "to surface"]

# A document line containing one of these can be quoted in "Risks and trade-offs".
RISK_WORDS = ["risk", "tension", "dispute", "litigation", "lawsuit", "distraction",
              "dependency", "resistance", "pressure", "loss", "fear", "disruption",
              "watching"]

# Labels used in the report to separate evidence from reasoning.
TAG_DOCUMENT = "**Document:**"
TAG_TENTATIVE = "**Document (tentative wording):**"
TAG_HYPOTHESIS = "**Hypothesis:**"
TAG_QUESTION = "**Question:**"
TAG_ASSUMPTION = "**Assumption:**"


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
    kotter_added = False
    if readiness and "Kotter" not in selected:
        selected.append("Kotter")
        kotter_added = True

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
        # The user's actual inputs, kept so the report can show them exactly.
        "change_type": change_type, "resistance": resistance, "stage": stage,
        "max_frameworks": max_frameworks, "kotter_added": kotter_added,
    }


# =============================================================================
# PART 3 - KNOWLEDGE DOCUMENTS
# -----------------------------------------------------------------------------
# Reads the five Word (.docx) files that sit next to app.py and finds the
# passages that share words with the user's challenge. A .docx file is a zip
# file with its text stored as XML, so Python's standard library is enough.
# No AI model is involved: passages are found by matching words and are quoted
# exactly as written.
# =============================================================================

WORD_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
BULLET_MARKS = ("- ", "• ", "* ", "– ", "— ")
NUMBER_PATTERN = re.compile(r"^\d+[.)]\s+")
MAJOR_PATTERN = re.compile(r"^(DECISION|LEVEL|PART|SECTION|PHASE|STAGE)\s+\d+")
LABEL_PATTERN = re.compile(r"^[A-Z][A-Za-z0-9 &'’/–-]{1,40}:\s+\S")


def app_folder():
    """The folder that contains app.py (works locally and on Streamlit Cloud)."""
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except NameError:
        return os.getcwd()


def find_document(filename):
    """Return the full path of a knowledge document, or "" if it is missing."""
    for folder in [app_folder(), os.getcwd()]:
        path = os.path.join(folder, filename)
        if os.path.isfile(path):
            return path
        try:
            names = os.listdir(folder)
        except OSError:
            names = []
        for name in names:  # second chance: ignore differences in capital letters
            if name.lower() == filename.lower():
                return os.path.join(folder, name)
    return ""


def read_docx_lines(path):
    """Return the lines of a .docx file. Empty paragraphs are kept as ""."""
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
    lines = []
    for paragraph in root.iter(WORD_NS + "p"):
        text = ""
        for node in paragraph.iter():
            if node.tag == WORD_NS + "t":
                text += node.text or ""
            elif node.tag == WORD_NS + "tab":
                text += " "
            elif node.tag in (WORD_NS + "br", WORD_NS + "cr"):
                text += "\n"
        for line in text.split("\n"):
            lines.append(" ".join(line.split()))
    return lines


def classify_line(line):
    """Decide what kind of line this is: rule, bullet, numbered, major, minor, label or text."""
    if len(line) >= 3 and set(line) <= set("-_=*"):
        return "rule"                      # a separator such as ---
    if line.startswith(BULLET_MARKS):
        return "bullet"
    if NUMBER_PATTERN.match(line):
        return "numbered"
    before_bracket = line.split("(")[0].strip()
    letters = [char for char in before_bracket if char.isalpha()]
    all_capitals = len(letters) >= 3 and all(char.isupper() for char in letters)
    if line.endswith(":"):
        one_word = len(before_bracket.rstrip(":").split()) == 1
        # "KEY TENSIONS:" is a main heading; "WINNERS:" or "Supporting cast:" a sub-heading.
        return "major" if all_capitals and not one_word else "minor"
    if MAJOR_PATTERN.match(line) or all_capitals:
        return "major"
    if LABEL_PATTERN.match(line):
        return "label"                     # for example "Step 1 - Urgency: ..."
    return "text"


def continues(entry, line):
    """True if this line is the wrapped continuation of the previous entry."""
    if entry["kind"] == "heading":
        return entry["text"].endswith(",") or line[0].islower()
    return (not entry["text"].endswith((".", "?", "!"))
            or line[0].islower() or line[0] == "(")


def parse_entries(lines):
    """Turn raw lines into entries: headings and passages.

    The documents are typed as short lines, so a sentence often runs over two
    or three lines. This function joins wrapped lines back together and records
    which heading each passage sits under ("where").
    """
    entries = []
    major, minor = "", ""
    current = None                          # the entry a wrapped line may continue
    title_seen = False
    for line in lines:
        if not line:
            current = None
            continue
        kind = classify_line(line)
        if not title_seen:
            title_seen = True
            if kind == "major":
                # The first line is the document title. It is kept as a heading but
                # not attached to every passage, or its words would match everything.
                entries.append({"kind": "heading", "text": line, "where": ""})
                continue
        if kind == "rule":
            current, minor = None, ""
            continue
        if kind == "text" and current is not None and continues(current, line):
            current["text"] += " " + line
            if current["kind"] == "heading":
                major = current["text"].rstrip(":")
            continue
        if kind == "major":
            major, minor = line.rstrip(":"), ""
            current = {"kind": "heading", "text": line, "where": ""}
        elif kind == "minor":
            minor = line.rstrip(":")
            entries.append({"kind": "heading", "text": line, "where": major})
            current = None
            continue
        else:
            if kind == "label":
                minor = ""
            text = line
            if kind == "bullet":
                text = line[2:].strip()
            where = " > ".join(part for part in [major, minor] if part)
            current = {"kind": kind, "text": text, "where": where}
            if kind == "label":
                minor = line.split(":")[0]  # later plain lines belong to this label
        entries.append(current)
    return entries


def tokens(text):
    """Lower-case words in a text."""
    return re.findall(r"[a-z]+", text.lower())


def stem(word):
    """Crude word stem: the first six letters, so 'cultural' matches 'culture'."""
    return STEM_EXCEPTIONS.get(word, word[:6])


def is_passage(entry):
    """Headings and one-word fragments are not quoted as evidence."""
    return entry["kind"] != "heading" and len(entry["text"].split()) >= 2


def is_guidance(document, entry):
    """True for lines in the context document that sit under a framework's name.

    These lines say when to use a framework. They are shown in section 1 and
    are not quoted as evidence about the company.
    """
    if document["topic"] != CONTEXT_TOPIC:
        return False
    place = entry["where"].lower()
    return any(name.split()[0].lower() in place for name in FRAMEWORKS)


def load_knowledge():
    """Read the five knowledge documents.

    Returns {"documents": [...], "counts": {...}}. Each document has a status:
    Loaded, Missing, Unreadable or Empty. "counts" records in how many passages
    each word stem appears, so that rarer words can count for more.
    """
    documents = []
    for item in KNOWLEDGE_DOCUMENTS:
        document = {"file": item["file"], "topic": item["topic"], "status": "Loaded",
                    "message": "", "lines": [], "entries": []}
        path = find_document(item["file"])
        if not path:
            document["status"] = "Missing"
            document["message"] = ("File not found next to app.py. Check that the name matches "
                                   "exactly, including capital letters and spaces.")
        else:
            try:
                lines = read_docx_lines(path)
            except Exception as problem:   # a damaged file must not stop the app
                document["status"] = "Unreadable"
                document["message"] = ("The file could not be opened as a Word .docx file ("
                                       + type(problem).__name__ + "). Re-save it as .docx.")
            else:
                if not any(lines):
                    document["status"] = "Empty"
                    document["message"] = "The file opened but contains no text."
                else:
                    document["lines"] = lines
                    document["entries"] = parse_entries(lines)
        documents.append(document)

    counts = {}
    for document in documents:
        for entry in document["entries"]:
            together = entry["text"] + " " + entry["where"]
            entry["stems"] = {stem(word) for word in tokens(together) if len(word) >= 3}
            entry["tentative"] = bool(find_keywords(together.lower(), TENTATIVE_WORDS))
            if is_passage(entry):
                for key in entry["stems"]:
                    counts[key] = counts.get(key, 0) + 1
    return {"documents": documents, "counts": counts}


def search_terms(text, extra_words):
    """Words used to look for passages, as {stem: word}."""
    terms = {}
    words = tokens(text)
    for extra in extra_words:
        words.extend(tokens(extra))
    for word in words:
        if len(word) >= 3 and word not in STOP_WORDS:
            terms[stem(word)] = word
    return terms


def make_passage(document, entry, hits):
    return {"file": document["file"], "where": entry["where"], "text": entry["text"],
            "hits": hits, "tentative": entry["tentative"],
            "key": (document["file"], entry["text"])}


def find_passages(knowledge, topics, terms, limit, only=""):
    """Passages on the given topics that best match the search terms.

    A passage scores 1/n for each matching word, where n is the number of
    passages containing that word, so rarer words count for more.
    only = "statements" skips questions, "questions" keeps only questions and
    "risks" keeps only passages containing a word from RISK_WORDS.
    """
    found = []
    for document in knowledge["documents"]:
        if document["topic"] not in topics:
            continue
        for position, entry in enumerate(document["entries"]):
            if not is_passage(entry) or is_guidance(document, entry):
                continue
            is_question = "?" in entry["text"]
            if only == "statements" and is_question:
                continue
            if only == "questions" and not is_question:
                continue
            if only == "risks" and not find_keywords(entry["text"].lower(), RISK_WORDS):
                continue
            matched = [key for key in terms if key in entry["stems"]]
            if not matched:
                continue
            score = sum(1.0 / knowledge["counts"].get(key, 1) for key in matched)
            hits = sorted(terms[key] for key in matched)
            found.append((score, -position, len(found), make_passage(document, entry, hits)))
    found.sort(reverse=True)
    return [passage for _, _, _, passage in found[:limit]]


def framework_guidance(knowledge, name):
    """Lines in the context document that sit under a heading naming the framework."""
    key = name.split()[0].lower()           # "kotter", "pfeffer", "ritti", "schein"
    passages = []
    for document in knowledge["documents"]:
        for entry in document["entries"]:
            if (is_passage(entry) and is_guidance(document, entry)
                    and key in entry["where"].lower()):
                passages.append(make_passage(document, entry, []))
    return passages[:2]


def kotter_step_passage(knowledge, number):
    """The line in the Kotter document that starts 'Step <number>', if there is one."""
    for document in knowledge["documents"]:
        if document["topic"] != "Kotter":
            continue
        for entry in document["entries"]:
            if is_passage(entry) and re.match(r"step\s*" + str(number) + r"\b", entry["text"].lower()):
                return make_passage(document, entry, ["step " + str(number)])
    return None


def framework_search_terms(name, result):
    """Search terms for one framework: the challenge plus its matched keywords."""
    extra = []
    for key, info in result["themes"].items():
        if THEMES[key]["weights"].get(name, 0) > 0:
            extra.extend(info["matched"])
    return search_terms(result["text"], extra)


def gather_evidence(result):
    """Find every document passage the report will quote, in one place."""
    knowledge = result["knowledge"]
    all_topics = [item["topic"] for item in KNOWLEDGE_DOCUMENTS]
    challenge_terms = search_terms(result["text"], [])
    evidence = {
        "context": find_passages(knowledge, [CONTEXT_TOPIC], challenge_terms, 4, "statements"),
        "frameworks": {}, "questions": {}, "guidance": {},
        "recommendations": [], "risks": [], "uncovered": [],
    }
    for name in FRAMEWORKS:
        evidence["guidance"][name] = framework_guidance(knowledge, name)
    for name in result["selected"]:
        terms = framework_search_terms(name, result)
        evidence["frameworks"][name] = find_passages(knowledge, [name], terms, 4, "statements")
        evidence["questions"][name] = find_passages(knowledge, [name], terms, 2, "questions")

    # One supporting passage for each recommendation, without repeating a passage.
    used = set()
    for entry in result["recommendations"]:
        passage = None
        if entry.get("trigger") and result["readiness"]:
            passage = kotter_step_passage(knowledge, result["readiness"]["weakest"] + 1)
        else:
            keywords = THEMES[entry["theme"]]["keywords"] if entry["theme"] else []
            terms = search_terms(result["text"], keywords)
            candidates = (find_passages(knowledge, [entry["framework"]], terms, 8, "statements")
                          + find_passages(knowledge, [CONTEXT_TOPIC], terms, 8, "statements"))
            for candidate in candidates:
                if candidate["key"] not in used:
                    passage = candidate
                    break
        if passage:
            used.add(passage["key"])
        evidence["recommendations"].append(passage)

    matched_words = []
    for info in result["themes"].values():
        matched_words.extend(info["matched"])
    evidence["risks"] = find_passages(knowledge, all_topics,
                                      search_terms(result["text"], matched_words), 4, "risks")

    # Themes found in the challenge that no document passage mentions.
    for key, info in result["themes"].items():
        if info["matched"]:
            terms = search_terms("", info["matched"])
            if not find_passages(knowledge, all_topics, terms, 1):
                evidence["uncovered"].append(THEMES[key]["label"])
    return evidence


def clean(text):
    """Make text safe to show inside Markdown."""
    for symbol in ["\\", "*", "_", "`", "#", "$", "[", "]"]:
        text = text.replace(symbol, "\\" + symbol)
    return text


def show_passage(passage):
    """One document passage as a labelled, quoted line with its source."""
    tag = TAG_TENTATIVE if passage["tentative"] else TAG_DOCUMENT
    source = passage["file"]
    if passage["where"]:
        source += ", under '" + passage["where"] + "'"
    line = tag + ' "' + clean(passage["text"]) + '" (' + clean(source)
    if passage["hits"]:
        line += "; matched on: " + ", ".join(passage["hits"][:6])
    return line + ")"


def loaded_documents(knowledge, topic=None):
    """Documents that loaded successfully, optionally for one topic."""
    return [d for d in knowledge["documents"]
            if d["status"] == "Loaded" and (topic is None or d["topic"] == topic)]


# =============================================================================
# PART 4 - REPORT BUILDER (always the same six sections)
# =============================================================================

def fill(template, result):
    """Insert the detected stakeholders and change type into a template."""
    return template.format(who=result["who"], change=result["change"])


def explain_theme(key, result):
    """e.g. 'Resistance (matched words: resist, fear; resistance set to High)'"""
    info = result["themes"][key]
    parts = []
    if info["matched"]:
        parts.append("matched words: " + ", ".join(info["matched"]))
    parts.extend(info["context"])
    return THEMES[key]["label"] + " (" + "; ".join(parts) + ")"


def format_number(value):
    """7.0 -> '7' and 7.5 -> '7.5'"""
    return format(value, "g")


def theme_contributions(name, result):
    """Themes that added to one framework's score, largest first.

    Each line shows the real arithmetic: theme points x weight = contribution.
    The contributions add up to the framework's relevance score.
    """
    items = []
    for key, info in result["themes"].items():
        weight = THEMES[key]["weights"].get(name, 0)
        if info["score"] > 0 and weight > 0:
            contribution = info["score"] * weight
            items.append((contribution, explain_theme(key, result) + ": "
                          + str(info["score"]) + " theme point(s) x weight " + str(weight)
                          + " = " + str(contribution)))
    items.sort(reverse=True)
    return [text for _, text in items]


def missing_themes(name, result):
    """Themes that feed this framework but scored 0 in this run."""
    labels = []
    for key, theme in THEMES.items():
        weight = theme["weights"].get(name, 0)
        if weight > 0 and result["themes"][key]["score"] == 0:
            labels.append(theme["label"] + " (weight " + str(weight) + ")")
    return labels


def selection_status(name, result):
    """Return (status, reason) for one framework, using the real scores."""
    scores = result["scores"]
    score = scores[name]
    top = max(scores.values())
    threshold = 0.5 * top
    ranked = sorted(scores, key=lambda n: scores[n], reverse=True)
    rank = str(ranked.index(name) + 1)
    is_selected = name in result["selected"]
    limit = str(result["max_frameworks"])
    reference = ("For reference, its score is " + str(score) + " against a top score of "
                 + str(top) + ".")

    if name == "Kotter" and result["kotter_added"]:
        return ("Selected (added for the readiness check)",
                "You completed the Kotter readiness self-assessment, so Kotter was added "
                "although the selection rules alone did not choose it. " + reference)

    if result["how"] == "manual":
        if is_selected:
            return ("Selected (chosen manually by you)",
                    "You chose manual selection, so the score did not decide. " + reference)
        return ("Not selected (manual mode)",
                "You chose manual selection and did not include this framework. " + reference)

    if result["how"] == "fallback":
        intro = ("No keywords were matched and no optional context added points, so every "
                 "framework scored 0. ")
        if is_selected:
            return ("Selected (default)",
                    intro + "The app then defaults to Kotter (process) and Schein (culture).")
        return ("Not selected (not part of the default pair)",
                intro + "The default pair is Kotter and Schein, so this framework was left "
                "out. This reflects a lack of information, not a judgement that it is irrelevant.")

    threshold_text = (format_number(threshold) + " (half of the top score of " + str(top)
                      + ", held by " + ranked[0] + ")")
    if is_selected:
        return ("Selected",
                "Its score of " + str(score) + " meets the threshold of " + threshold_text
                + ". It ranked " + rank + " of 4, within the limit of " + limit + " framework(s).")
    if score >= threshold:
        reason = ("Excluded by the selection limit. Its score of " + str(score)
                  + " meets the threshold of " + threshold_text + ", but the maximum number "
                  "of frameworks was set to " + limit + " and it ranked " + rank + " of 4. "
                  "It does not necessarily lack relevance: raising the maximum would include it.")
        if any(scores[other] == score for other in result["selected"]):
            reason += (" It has the same score as a selected framework; ties are broken by "
                       "the fixed order Kotter, Pfeffer, Ritti & Levy, Schein.")
        return ("Not selected (excluded by the selection limit)", reason)
    return ("Not selected (below the threshold)",
            "Its score of " + str(score) + " is below the threshold of " + threshold_text + ".")


def report_key():
    """Explains the labels that separate document evidence from reasoning."""
    return "\n".join([
        "**How to read this report**",
        "",
        "- " + TAG_DOCUMENT + " quoted from your uploaded Word documents. The app has not "
        "checked these statements against any outside source.",
        "- " + TAG_TENTATIVE + " quoted from your documents, where the document's own "
        "wording is tentative (for example 'likely', 'may' or 'emerging').",
        "- " + TAG_HYPOTHESIS + " general framework reasoning from the app's built-in "
        "templates. It is not evidence about TMICC and needs testing.",
        "- " + TAG_QUESTION + " something to investigate before acting.",
        "- " + TAG_ASSUMPTION + " something the app takes as given.",
    ])


def section_frameworks(result):
    """Section 1: all four frameworks, selected or not, with the real scores."""
    knowledge = result["knowledge"]
    evidence = result["evidence"]
    if result["how"] == "manual":
        mode_text = "Manual (you chose the frameworks; the maximum does not apply)"
    else:
        mode_text = "Automatic, maximum of " + str(result["max_frameworks"]) + " framework(s)"
    context = []
    for info in result["themes"].values():
        context.extend(info["context"])
    not_loaded = [d["file"] + " (" + d["status"].lower() + ")"
                  for d in knowledge["documents"] if d["status"] != "Loaded"]
    documents_text = (str(len(loaded_documents(knowledge))) + " of "
                      + str(len(knowledge["documents"])) + " loaded")
    if not_loaded:
        documents_text += ". Not loaded: " + ", ".join(not_loaded)

    lines = [
        "#### Inputs and rules used in this run",
        "- **Type of change:** " + result["change_type"],
        "- **Urgency:** " + result["urgency"],
        "- **Level of resistance:** " + result["resistance"],
        "- **Stage of the change:** " + result["stage"],
        "- **Framework selection:** " + mode_text,
        "- **Context choices that added points:** "
        + ("; ".join(context) if context else "none")
        + ". Settings of 'Not specified' or 'Low' add no points.",
        "- **Knowledge documents:** " + documents_text + ".",
        "- **Scoring rule:** each matched keyword adds 1 point to its theme and optional "
        "context adds 1 or 2 points. A framework's score is the sum of theme points "
        "multiplied by that theme's weight for the framework.",
        "- **Selection rule:** in automatic mode, frameworks scoring at least half of the "
        "top score are selected, up to the maximum number chosen.",
        "- **Role of the documents:** scores come only from your text and context choices. "
        "The documents supply the quoted evidence; they do not change the scores.",
        "",
    ]

    for name in FRAMEWORKS:
        status, reason = selection_status(name, result)
        is_selected = name in result["selected"]
        lines.append("#### " + FRAMEWORKS[name]["title"])
        lines.append("- **Selection status:** " + status)
        lines.append("- **Relevance score:** " + str(result["scores"][name])
                     + " (highest score in this run: " + str(max(result["scores"].values())) + ")")
        lines.append("- **Why " + ("selected" if is_selected else "not selected") + ":** " + reason)

        factors = theme_contributions(name, result)
        if name == "Kotter" and result["readiness"]:
            factors.append("Readiness self-assessment completed (average "
                           + format(result["readiness"]["average"], ".1f")
                           + " out of 5). This does not change the score.")
        if factors:
            lines.append("- **Factors increasing relevance:**")
            for factor in factors:
                lines.append("  - " + factor)
        else:
            lines.append("- **Factors increasing relevance:** none detected in this run.")

        guidance = evidence["guidance"][name]
        if guidance:
            lines.append("- **Guidance on this framework in your context document:**")
            for passage in guidance:
                lines.append("  - " + show_passage(passage))
        else:
            lines.append("- **Guidance on this framework in your context document:** none found.")

        if is_selected:
            lines.append("- **When to reconsider:** it would become less relevant with "
                         + FRAMEWORK_NOTES[name]["lower"])
        else:
            reconsider = ("- **When to reconsider:** it would become more relevant with "
                          + FRAMEWORK_NOTES[name]["raise"])
            missing = missing_themes(name, result)
            if missing:
                reconsider += (" In this app, its score rises when the text or context "
                               "signals these themes, which scored 0 in this run: "
                               + "; ".join(missing) + ".")
            lines.append(reconsider)
        lines.append("")
    return "\n".join(lines)


def section_analysis(result):
    """Section 2: the challenge, the document evidence, then each framework."""
    knowledge = result["knowledge"]
    evidence = result["evidence"]
    selected = result["selected"]

    lines = ["#### Signals found in your challenge (from the text you typed)"]
    if result["stakeholders"]:
        lines.append("- **Stakeholder groups recognised:** "
                     + join_words(result["stakeholders"]) + ".")
    else:
        lines.append("- **Stakeholder groups recognised:** none. Naming the groups "
                     "involved will make the output more specific.")
    strongest = sorted(result["themes"], key=lambda key: result["themes"][key]["score"],
                       reverse=True)
    strongest = [key for key in strongest if result["themes"][key]["score"] > 0][:4]
    if strongest:
        for key in strongest:
            lines.append("- **Theme:** " + explain_theme(key, result) + ", "
                         + str(result["themes"][key]["score"]) + " point(s).")
    else:
        lines.append("- **Themes:** none detected, so the analysis below is general.")
    lines.append("")

    lines.append("#### Company context from your TMICC context document")
    if not loaded_documents(knowledge, CONTEXT_TOPIC):
        lines.append("- The TMICC context document was not loaded, so no company context "
                     "can be quoted. See the 'Knowledge base documents' tab.")
    elif evidence["context"]:
        for passage in evidence["context"]:
            lines.append("- " + show_passage(passage))
    else:
        lines.append("- No line in the context document shares a word with your challenge. "
                     "Try describing the challenge in more detail.")
    lines.append("")

    for name in selected:
        entries = entries_for(name, result["themes"])[:3] or [DEFAULT_CONTENT[name]]
        lines.append("#### " + name + " analysis")
        lines.append("**Evidence from your " + name + " document**")
        lines.append("")
        passages = evidence["frameworks"].get(name, [])
        if not loaded_documents(knowledge, name):
            lines.append("- The " + name + " document was not loaded, so this part uses "
                         "built-in reasoning only.")
        elif passages:
            for passage in passages:
                lines.append("- " + show_passage(passage))
        else:
            lines.append("- No line in the " + name + " document shares a word with your "
                         "challenge, so this part uses built-in reasoning only.")
        if name == "Kotter" and result["readiness"]:
            ready = result["readiness"]
            lines.append("- **Your readiness self-assessment:** average "
                         + format(ready["average"], ".1f") + " out of 5 (" + ready["level"]
                         + " readiness). Weakest step: " + KOTTER_STEPS[ready["weakest"]][0]
                         + " (" + str(ready["ratings"][ready["weakest"]]) + "/5).")
            step = kotter_step_passage(knowledge, ready["weakest"] + 1)
            if step:
                lines.append("- " + show_passage(step))
        lines.append("")
        lines.append("**Interpretation (general framework reasoning)**")
        lines.append("")
        for entry in entries:
            lines.append("- " + TAG_HYPOTHESIS + " " + fill(entry["insight"], result))
        lines.append("")
        lines.append("**Diagnostic questions**")
        lines.append("")
        for passage in evidence["questions"].get(name, []):
            lines.append("- **Question from your document:** \"" + clean(passage["text"])
                         + "\" (" + clean(passage["file"]) + ")")
        questions = []
        for entry in entries:
            questions.extend(entry["questions"])
        for question in questions[:4]:
            lines.append("- " + TAG_QUESTION + " " + fill(question, result))
        lines.append("")

    pairs = [(pair, notes) for pair, notes in PAIR_NOTES.items()
             if pair[0] in selected and pair[1] in selected]
    lines.append("#### How the selected frameworks fit together (general framework reasoning)")
    if pairs:
        for pair, notes in pairs:
            lines.append("- **" + pair[0] + " with " + pair[1] + ":** " + notes["complement"])
        for pair, notes in pairs:
            lines.append("- **Possible conflict, " + pair[0] + " versus " + pair[1] + ":** "
                         + notes["conflict"])
        lines.append("- **Implication:** where two frameworks point to different actions, "
                     "treat it as a choice to make with evidence, not as an error in either.")
    else:
        lines.append("- Only one framework was selected, so there is no combination to "
                     "compare. Raising the maximum number of frameworks, or choosing "
                     "manually, would add a second perspective.")
    return "\n".join(lines)


def trigger_text(entry, result):
    if entry.get("trigger"):
        return entry["trigger"]
    if entry["theme"]:
        return explain_theme(entry["theme"], result)
    return "general good practice (no specific signal detected)"


def action_details(entry, result):
    """Return (suggested owner, deliverable, timeframe) for one recommendation."""
    if entry.get("trigger") and result["readiness"]:
        # The recommendation that came from the Kotter readiness check.
        owner, deliverable = KOTTER_STEP_DETAILS[result["readiness"]["weakest"]]
    else:
        if entry["framework"] == "General":
            key = ("General", entry["phase"])
        else:
            key = (entry["framework"], entry["theme"])
        owner, deliverable = ACTION_DETAILS.get(
            key, ("Change lead", "Short written output agreed with the sponsor"))
    return owner, deliverable, PHASE_TIMEFRAMES[entry["phase"]]


def section_recommendations(result):
    """Section 3: 3-5 recommendations in sequence, each linked to document evidence."""
    lines = []
    for number, entry in enumerate(result["recommendations"], start=1):
        owner, deliverable, timeframe = action_details(entry, result)
        passage = result["evidence"]["recommendations"][number - 1]
        lines.append("**" + str(number) + ". " + PHASES[entry["phase"]] + " - "
                     + entry["framework"] + "**")
        lines.append("")
        lines.append("- **Action (a hypothesis to test):** " + fill(entry["rec"], result))
        lines.append("- **Suggested owner (generic role):** " + owner)
        lines.append("- **Deliverable:** " + deliverable)
        lines.append("- **Indicative timeframe:** " + timeframe)
        lines.append("- **Triggered by:** " + trigger_text(entry, result))
        if passage:
            lines.append("- **Related evidence:** " + show_passage(passage))
        else:
            lines.append("- **Related evidence:** no matching line was found in your documents. "
                         "This action rests on general framework reasoning only.")
        lines.append("")
    lines.append("- **Sequence:** recommendations are ordered Diagnose, Mobilise, Deliver, "
                 "Embed. Earlier steps provide the evidence and support that later steps rely on.")
    lines.append("- **How the documents are used here:** the action wording comes from built-in "
                 "templates. The quoted line is the closest match in your documents by shared "
                 "words; check that it is truly relevant before relying on it.")
    return "\n".join(lines)


def section_risks(result):
    """Section 4: risks of each recommendation, trade-offs, and risks in the documents."""
    lines = ["#### Risks attached to the recommendations"]
    for number, entry in enumerate(result["recommendations"], start=1):
        lines.append("- " + TAG_HYPOTHESIS + " Recommendation " + str(number) + ": " + entry["risk"])
    lines.append("")
    lines.append("#### Trade-offs to decide")
    for tradeoff in result["tradeoffs"]:
        lines.append("- " + tradeoff)
    lines.append("")
    lines.append("#### Risks and tensions stated in your documents")
    if result["evidence"]["risks"]:
        for passage in result["evidence"]["risks"]:
            lines.append("- " + show_passage(passage))
    else:
        lines.append("- No line in your documents both mentions a risk or tension and shares "
                     "a word with your challenge.")
    return "\n".join(lines)


def section_benefits(result):
    """Section 5: what the proposed approach offers."""
    selected = result["selected"]
    supported = sum(1 for passage in result["evidence"]["recommendations"] if passage)
    total = len(result["recommendations"])
    phases = []
    for entry in result["recommendations"]:
        if PHASES[entry["phase"]] not in phases:
            phases.append(PHASES[entry["phase"]])

    lines = ["#### Benefits of the combination of frameworks"]
    pairs = [(pair, notes) for pair, notes in PAIR_NOTES.items()
             if pair[0] in selected and pair[1] in selected]
    if pairs:
        lines.append("- **More than one lens:** " + join_words(selected) + " look at the same "
                     "challenge from different angles, which reduces the chance of a one-sided "
                     "diagnosis.")
        for pair, notes in pairs:
            lines.append("- **" + pair[0] + " with " + pair[1] + ":** " + notes["complement"])
    else:
        lines.append("- **Focus:** a single framework keeps the diagnosis simple and quick to "
                     "explain. The cost is a narrower view; see section 6.")
    lines.append("")

    lines.append("#### What each selected framework contributes (general framework reasoning)")
    for name in selected:
        for point in FRAMEWORK_NOTES[name]["strengths"]:
            lines.append("- **" + name + ":** " + point)
    lines.append("")

    lines.append("#### Benefits of the sequence and the evidence base")
    lines.append("- **Staged commitment:** the plan moves through " + join_words(phases)
                 + ", so early findings can change later steps before major effort is spent.")
    lines.append("- **Traceable reasoning:** every framework choice and recommendation shows "
                 "the words and rules that triggered it, so it can be challenged.")
    lines.append("- **Link to your documents:** " + str(supported) + " of " + str(total)
                 + " recommendations are paired with a line from your documents.")
    lines.append("- **Evidence kept separate:** document quotes, hypotheses and questions are "
                 "labelled, which makes clear what still needs to be tested.")
    return "\n".join(lines)


def section_limitations(result):
    """Section 6: limitations of the app, assumptions, and gaps in the evidence."""
    knowledge = result["knowledge"]
    evidence = result["evidence"]
    lines = [
        "#### Limitations of this app",
        "- **This is a rule-based prototype, not an AI model.** It matches keywords in your text, "
        "fills pre-written templates and quotes lines from your documents. It does not "
        "understand meaning.",
        "- **Keyword matching can misread text.** For example, 'there is no resistance' still "
        "triggers the resistance theme, and issues described in unusual words are missed.",
        "- **Document lines are found by shared words.** A quoted line shares words with your "
        "challenge; the app cannot judge whether it is truly relevant, and it can miss "
        "relevant lines that use different words.",
        "- **Templates are reused.** Similar challenges receive similar wording.",
    ]
    if result["keyword_hits"] < 3:
        lines.append("- **Low confidence for this run:** fewer than three keywords were matched, "
                     "so the selection rests on very little evidence.")
    if len(result["text"].split()) < 25:
        lines.append("- **Short description:** your challenge is under 25 words. More detail on "
                     "who is involved and what is going wrong will improve the output.")
    lines.append("")

    lines.append("#### Limitations of the selected frameworks (general framework reasoning)")
    for name in result["selected"]:
        for point in FRAMEWORK_NOTES[name]["limitations"]:
            lines.append("- **" + name + ":** " + point)
    lines.append("")

    lines.append("#### Assumptions")
    lines.append("- " + TAG_ASSUMPTION + " your inputs are taken as given: type of change '"
                 + result["change_type"] + "', urgency '" + result["urgency"]
                 + "', resistance '" + result["resistance"] + "', stage '" + result["stage"] + "'.")
    lines.append("- " + TAG_ASSUMPTION + " the Word documents are accurate and current. The app "
                 "quotes them as written and cannot check them.")
    lines.append("- " + TAG_ASSUMPTION + " every matched keyword counts once, however often or "
                 "however strongly the issue is described.")
    lines.append("- " + TAG_ASSUMPTION + " the theme weights and the half-of-top-score threshold "
                 "are design judgements. They are shown under 'How this app works' and have not "
                 "been validated against real cases.")
    lines.append("- " + TAG_ASSUMPTION + " owners, deliverables and timeframes are generic and "
                 "assume a typical programme with a sponsor, a programme director and HR support.")
    lines.append("")

    lines.append("#### Evidence gaps")
    gaps = []
    for document in knowledge["documents"]:
        if document["status"] != "Loaded":
            gaps.append("**" + document["file"] + "** was not loaded (" + document["status"].lower()
                        + "), so nothing from it could be used.")
    if evidence["uncovered"]:
        gaps.append("These themes appear in your challenge but no document line mentions the "
                    "matched words: " + "; ".join(evidence["uncovered"]) + ".")
    unsupported = [str(number) for number, passage
                   in enumerate(evidence["recommendations"], start=1) if not passage]
    if unsupported:
        gaps.append("Recommendation(s) " + ", ".join(unsupported) + " have no matching line in "
                    "your documents.")
    no_guidance = [name for name in FRAMEWORKS if not evidence["guidance"][name]]
    if no_guidance and loaded_documents(knowledge, CONTEXT_TOPIC):
        gaps.append("Your context document contains no guidance on when to use: "
                    + join_words(no_guidance) + ".")
    gaps.append("The app cannot tell whether a document line is a verified fact or the author's "
                "own judgement. Lines with tentative wording are flagged, but others may also "
                "be opinion.")
    gaps.append("The knowledge base is limited to the five documents. Views of employees, "
                "performance data and anything that happened after the documents were written "
                "are outside it unless the documents state them.")
    for gap in gaps:
        lines.append("- " + gap)
    lines.append("- **Use:** this output is for structuring thinking and discussion. Validate "
                 "it with interviews, data and professional judgement before acting.")
    return "\n".join(lines)


def build_sections(result):
    result["evidence"] = gather_evidence(result)
    return [
        ("1. Frameworks selected and why", section_frameworks(result)),
        ("2. Analysis grounded in the challenge and knowledge documents", section_analysis(result)),
        ("3. Sequenced recommendations", section_recommendations(result)),
        ("4. Risks and trade-offs", section_risks(result)),
        ("5. Benefits of the proposed approach", section_benefits(result)),
        ("6. Limitations, assumptions and evidence gaps", section_limitations(result)),
    ]


def build_download(result, sections):
    parts = ["# " + APP_TITLE, "",
             "*Generated by a rule-based prototype using locally extracted document text. "
             "No AI model was used.*", "",
             "## Challenge", result["text"], "", report_key(), ""]
    for title, body in sections:
        parts.extend(["## " + title, body, ""])
    return "\n".join(parts)


# =============================================================================
# PART 5 - STREAMLIT PAGES
# =============================================================================

def load_example():
    st.session_state["challenge"] = EXAMPLES[st.session_state["example_choice"]]


def page_analyse(knowledge):
    st.subheader("Describe the change challenge")

    problems = [d for d in knowledge["documents"] if d["status"] != "Loaded"]
    for document in problems:
        st.warning("Knowledge document not available: " + document["file"] + " ("
                   + document["status"] + "). " + document["message"])
    if not problems:
        st.caption("All " + str(len(knowledge["documents"])) + " knowledge documents loaded. "
                   "See the 'Knowledge base documents' tab to inspect them.")

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
    manual = mode_label.startswith("Manual")
    manual_choice = []
    max_frameworks = 3
    if manual:
        manual_choice = st.multiselect("Frameworks to apply", list(FRAMEWORKS),
                                       default=list(FRAMEWORKS))
    else:
        max_frameworks = st.slider("Maximum number of frameworks", 1, 4, 3)

    if st.button("Analyse challenge", type="primary"):
        if not text.strip():
            st.warning("Please describe the challenge first.")
        elif manual and not manual_choice:
            st.warning("Please choose at least one framework.")
        else:
            st.session_state["analysed"] = True

    # Once "Analyse challenge" has been clicked, the report is rebuilt from the
    # inputs currently on screen every time the page reruns. This keeps the
    # report (for example the resistance level it shows) in step with the inputs.
    inputs_ready = bool(text.strip()) and (bool(manual_choice) or not manual)
    if st.session_state.get("analysed") and inputs_ready:
        result = analyse(text.strip(), change_type, urgency, resistance, stage,
                         "manual" if manual else "auto", manual_choice,
                         max_frameworks, ratings)
        result["knowledge"] = knowledge
        sections = build_sections(result)
        st.divider()
        st.header("Consulting report")
        st.caption("Produced by transparent Python rules, templates and text extracted from "
                   "your Word documents. No AI model is used. The report always reflects the "
                   "inputs currently shown above.")
        st.info(report_key())
        for title, body in sections:
            st.subheader(title)
            st.markdown(body)
        st.download_button("Download report (Markdown)", build_download(result, sections),
                           file_name="tmicc_change_report.md", mime="text/markdown")


def page_knowledge(knowledge):
    st.subheader("Knowledge base documents")
    st.write("The app reads these five Word documents from the folder that contains app.py. "
             "Their text is extracted when the page loads and is quoted in the report when "
             "it shares words with your challenge.")
    rows = []
    for document in knowledge["documents"]:
        passages = [entry for entry in document["entries"] if is_passage(entry)]
        rows.append({"File": document["file"], "Used for": document["topic"],
                     "Status": document["status"],
                     "Lines read": len([line for line in document["lines"] if line]),
                     "Passages": len(passages)})
    st.table(rows)

    for document in knowledge["documents"]:
        with st.expander(document["file"] + " - " + document["status"]):
            if document["status"] != "Loaded":
                st.warning(document["message"])
                continue
            st.markdown("**Used for:** " + document["topic"])
            text_lines = [line for line in document["lines"] if line]
            st.markdown("**Last line read:** \"" + clean(text_lines[-1]) + "\" (if this looks "
                        "cut off, the Word file itself is incomplete)")
            st.markdown("**Extracted text**")
            st.text("\n".join(document["lines"]))
            if st.checkbox("Show how the app split this document into passages",
                           key="split_" + document["file"]):
                shown = []
                for entry in document["entries"]:
                    if entry["kind"] == "heading":
                        shown.append("")
                        shown.append("== " + entry["text"])
                    elif is_passage(entry):
                        note = "  [tentative wording]" if entry["tentative"] else ""
                        shown.append("  * " + entry["text"] + note)
                st.text("\n".join(shown))


def page_reference():
    st.subheader("Framework reference")
    st.write("A short guide to the four frameworks used in this app. The strengths and "
             "limitations are general points built into the app, not taken from your documents.")
    sources = {item["topic"]: item["file"] for item in KNOWLEDGE_DOCUMENTS}
    for name, framework in FRAMEWORKS.items():
        with st.expander(framework["title"]):
            st.markdown("**Focus:** " + framework["focus"])
            st.markdown(framework["summary"])
            st.markdown("**Your document for this framework:** " + sources[name])
            st.markdown("**Strengths**")
            for point in FRAMEWORK_NOTES[name]["strengths"]:
                st.markdown("- " + point)
            st.markdown("**Limitations**")
            for point in FRAMEWORK_NOTES[name]["limitations"]:
                st.markdown("- " + point)
            st.markdown("- General critique: " + framework["critique"])
            st.markdown("**General diagnostic questions**")
            for question in DEFAULT_CONTENT[name]["questions"]:
                st.markdown("- " + question.format(who="the people affected", change="the change"))
            if name == "Kotter":
                st.markdown("**The eight steps**")
                for index, (step_name, _, _) in enumerate(KOTTER_STEPS, start=1):
                    st.markdown(str(index) + ". " + step_name)


def page_method():
    st.subheader("How this app works")
    st.markdown(
        "This app is a **rule-based prototype**. It does not call a live AI model, an API or "
        "any external service, and it costs nothing to run. Everything it shows comes from "
        "three sources:\n\n"
        "- **Your text and context choices**, read by keyword rules.\n"
        "- **Built-in templates** written in advance for each framework and theme.\n"
        "- **Text extracted from five Word documents** stored next to `app.py`.\n")
    st.markdown("#### Steps")
    st.markdown(
        "1. **Reading the documents.** Each `.docx` file is opened with Python's built-in "
        "`zipfile` and `xml` modules. Wrapped lines are joined and each passage is linked to "
        "the heading above it. You can inspect the result in the 'Knowledge base documents' tab.\n"
        "2. **Theme detection.** Your text is searched for the keywords in the table below. "
        "Each match adds 1 point to its theme; optional context you select adds 1 or 2 points.\n"
        "3. **Framework scoring.** Each theme points to frameworks with a weight from 1 to 3. "
        "A framework's score is the sum of theme points multiplied by weight. The documents "
        "do not change the scores.\n"
        "4. **Selection.** Frameworks scoring at least half of the top score are selected, up "
        "to the maximum you set. You can also choose frameworks manually.\n"
        "5. **Finding document evidence.** Words from your challenge and the matched keywords "
        "are compared with every passage. Words are matched on their first six letters, and "
        "rarer words count for more. The best matches are quoted with their file and heading.\n"
        "6. **Templates.** Interpretations, questions, recommendations and risks are "
        "pre-written for each framework and theme, and filled in with the stakeholder groups "
        "and change type detected.\n"
        "7. **Sequencing.** Three to five recommendations are chosen and ordered: Diagnose, "
        "Mobilise, Deliver, Embed.")
    st.markdown("#### What the app cannot do")
    st.markdown(
        "- It does not understand your challenge or the documents; it matches words.\n"
        "- It cannot check whether a statement in a document is true or up to date.\n"
        "- It cannot write new analysis. Wording outside the quotes comes from fixed templates, "
        "which is why the report labels them as hypotheses.\n"
        "- It may quote a line that shares words with your challenge but is not relevant, "
        "and may miss a relevant line that uses different words.")
    st.markdown("#### Themes, keywords and weights")
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
               "to TMICC change challenges, using text extracted from five Word documents.")
    knowledge = load_knowledge()

    with st.sidebar:
        st.header("About")
        st.write("Describe a change challenge and the app selects the most relevant "
                 "frameworks, then produces a structured consulting-style report.")
        st.info("No live AI model is used. Results come from keyword rules, pre-written "
                "templates and lines quoted from your Word documents.")
        st.header("Knowledge base documents")
        for document in knowledge["documents"]:
            st.markdown("- " + document["file"] + ": **" + document["status"] + "**")

    tab_analyse, tab_knowledge, tab_reference, tab_method = st.tabs(
        ["Analyse a challenge", "Knowledge base documents", "Framework reference",
         "How this app works"])
    with tab_analyse:
        page_analyse(knowledge)
    with tab_knowledge:
        page_knowledge(knowledge)
    with tab_reference:
        page_reference()
    with tab_method:
        page_method()


main()        "focus": "How ready the organisation is and which step of the change process is weak.",
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
