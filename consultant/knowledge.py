"""General change-management knowledge and rules used by the consultant.

IMPORTANT: this file contains DATA ONLY, and none of it is a fact about
TMICC. Everything here is general framework knowledge or a general
recommendation. The app always labels text taken from this file as
"General guidance" (or "Inference" when a rule links it to a document
passage). Facts about TMICC come only from the five Word documents.

To change what the consultant says, edit the text in this file. No other
file needs to change.
"""

# Name used when addressing the user. The documents name the user as
# Peter ter Kulve, CEO. Set to "" to remove the personal address.
ADVISEE_NAME = "Peter"

# Labels shown in front of every statement so the reader can tell where it
# came from.
LABEL_DOCUMENT = "document"
LABEL_INFERENCE = "inference"
LABEL_GENERAL = "general"

LABEL_TEXT = {
    LABEL_DOCUMENT: "📄 **From your documents**",
    LABEL_INFERENCE: "🔎 **Inference**",
    LABEL_GENERAL: "📘 **General guidance**",
}

LEGEND = (
    "📄 **From your documents** = quoted from one of the five Word files.  \n"
    "🔎 **Inference** = a rule linking a quoted passage to a framework idea; plausible, not proven.  \n"
    "📘 **General guidance** = standard change-management practice, not stated in your documents."
)

# Illustrative phases for roadmaps. The documents contain no timeline, so
# these timings are always shown as general suggestions.
PHASES = [
    {"name": "1. Mobilise", "timing": "Weeks 0-4"},
    {"name": "2. Engage and design", "timing": "Months 1-3"},
    {"name": "3. Deliver and prove", "timing": "Months 3-6"},
    {"name": "4. Embed", "timing": "Months 6-12"},
]

# ---------------------------------------------------------------------------
# The four frameworks
# ---------------------------------------------------------------------------
# "names"    - words that mean the user mentioned the framework directly
# "triggers" - topics that route a question to this framework. They follow
#              the routing rules of the original Copilot design.
# "keywords" - single words that add a little weight
# "actions"  - general actions; "phase" is an index into PHASES (0-3)

FRAMEWORKS = {
    "Kotter": {
        "title": "Kotter — change readiness and the 8-step model",
        "focus": "Whether the organisation is ready for change and which stage needs attention.",
        "summary": (
            "Kotter's model moves from creating urgency and building a guiding coalition "
            "through communicating a vision, enabling action, generating wins, sustaining "
            "acceleration and anchoring change in culture."
        ),
        "key_question": "Which step of the change is weakest, and what must happen next?",
        "best_for": "Sequencing a change, building momentum, and finding where a programme is stalling.",
        "not_for": "It does not explain power, political payoffs or cultural assumptions.",
        "names": ["kotter", "8-step", "8 step", "eight step", "eight-step"],
        "triggers": [
            "change readiness", "momentum", "next step", "stalling", "stall", "urgency",
            "guiding coalition", "sequencing", "sequence", "vision", "short-term wins",
            "removing barriers", "anchoring", "roadmap", "implementation", "action plan",
            "resistance to change", "resistance", "communication", "strategy",
        ],
        "keywords": [
            "urgency", "resistance", "communication", "vision", "leadership",
            "coalition", "milestone", "momentum", "readiness", "adoption",
            "training", "change fatigue", "buy-in", "implementation", "engagement",
            "plan", "barrier", "wins", "embed", "sustain", "timeline",
        ],
        "concepts": [
            ("Step 1", "Create a sense of urgency"),
            ("Step 2", "Build a guiding coalition"),
            ("Step 3", "Form a strategic vision"),
            ("Step 4", "Communicate the vision and enlist support"),
            ("Step 5", "Enable action by removing barriers"),
            ("Step 6", "Generate short-term wins"),
            ("Step 7", "Sustain acceleration"),
            ("Step 8", "Anchor the change in culture"),
        ],
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
        "actions": [
            {"text": "Clarify why the change is necessary now and what happens if it is delayed.",
             "phase": 0, "owner": "CEO and executive team"},
            {"text": "Identify the weakest change step: leadership alignment, communication, removing barriers, short-term wins or embedding the change.",
             "phase": 0, "owner": "Change lead"},
            {"text": "Form a guiding coalition with enough authority, credibility and reach to lead the change.",
             "phase": 0, "owner": "CEO"},
            {"text": "Set one visible near-term milestone and communicate progress consistently.",
             "phase": 2, "owner": "Change lead and communications lead"},
            {"text": "Build successful new practices into routines, role expectations and recognition so they outlast the programme.",
             "phase": 3, "owner": "Executive team and HR lead"},
        ],
        "risks": [
            {"risk": "Declaring success after early wins, so later steps are never completed.",
             "mitigation": "Keep reporting against all eight steps until new behaviours are routine."},
            {"risk": "Treating the steps as a rigid checklist when the change is moving unevenly across teams.",
             "mitigation": "Review each step by business area and revisit earlier steps where needed."},
        ],
        "outcomes": [
            "A shared, sequenced view of what happens next.",
            "Visible early progress that sustains confidence.",
        ],
        "measures": [
            "Share of leaders who describe the reason for change consistently.",
            "Milestones delivered on time against the plan.",
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
        "key_question": "Who depends on whom, who controls scarce resources, and where is a relationship missing?",
        "best_for": "Board and investor dynamics, alliances, and dependence on another party's resources or systems.",
        "not_for": "It does not sequence a change or explain cultural assumptions.",
        "names": ["pfeffer", "network map", "power map"],
        "triggers": [
            "power", "influence", "relationships", "alliances", "board dynamics",
            "investor relationships", "investor relations", "dependency", "dependence",
            "resources", "structural hole", "brokerage", "network", "decision rights",
            "retailers", "transitional service agreement", "service agreements",
            "shared services", "systems",
        ],
        "keywords": [
            "power", "influence", "stakeholder", "dependency", "dependencies",
            "approval", "resources", "network", "sponsor", "blocker",
            "decision", "authority", "politics", "informal", "control",
            "board", "investor", "alliance", "relationship", "access",
        ],
        "concepts": [
            ("Power base", "What gives an actor influence: expertise, position, control of resources or information."),
            ("Dependence", "An actor who needs something another controls is in the weaker position."),
            ("Structural hole", "A missing direct relationship between two actors who need to work together."),
            ("Brokerage", "Using an existing relationship to bridge a structural hole."),
        ],
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
        "actions": [
            {"text": "Map the stakeholders who control approvals, resources, information and operational access.",
             "phase": 0, "owner": "CEO office"},
            {"text": "Identify dependencies and informal influencers, then agree how each will be engaged.",
             "phase": 1, "owner": "Executive team"},
            {"text": "Bridge missing relationships through introductions from people who are already trusted on both sides.",
             "phase": 1, "owner": "CEO and Chair"},
            {"text": "Make decision rights explicit so teams know who can decide, advise and unblock work.",
             "phase": 1, "owner": "Executive team"},
            {"text": "Reduce the most critical dependencies by building alternatives or agreeing clear exit terms.",
             "phase": 2, "owner": "Functional leads"},
        ],
        "risks": [
            {"risk": "Relationship-building is seen as manoeuvring and damages trust.",
             "mitigation": "Be open about purpose and make sure the other party also gains."},
            {"risk": "Attention goes to senior actors while operational dependencies are missed.",
             "mitigation": "Map dependencies at working level as well as at board level."},
        ],
        "outcomes": [
            "Fewer decisions blocked by an unmanaged dependency.",
            "Direct relationships with the actors who control critical resources.",
        ],
        "measures": [
            "Number of critical dependencies with an agreed owner and exit or mitigation plan.",
            "Number of key external actors with a direct senior relationship.",
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
        "key_question": "For this decision, who wins, who loses, who is undecided, and in what order should they be approached?",
        "best_for": "A specific decision where support has to be built and opposition anticipated.",
        "not_for": "It does not map network structure, sequence a whole programme or surface cultural assumptions.",
        "names": ["ritti", "levy", "payoff map", "payoff matrix"],
        "triggers": [
            "winners", "losers", "wins or loses", "who wins", "who loses", "fence-sitters",
            "political support", "politics", "payoff", "governance dispute", "dispute",
            "stakeholder strategy", "coalition", "interests", "concession", "neutralise",
            "resistance", "conflict",
        ],
        "keywords": [
            "winners", "losers", "unwritten", "rules", "politics", "conflict",
            "interests", "incentives", "status", "identity", "territory",
            "resistance", "informal", "fairness", "competition", "political",
            "opposition", "support", "compromise", "negotiate",
        ],
        "concepts": [
            ("Winners", "Those who gain from a decision and how."),
            ("Losers", "Those who lose and what they stand to lose."),
            ("Fence-sitters", "Those who are undecided and what would move them."),
            ("Sequenced strategy", "Who to bring on board first, who to neutralise, and who to manage rather than convert."),
        ],
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
        "actions": [
            {"text": "For the decision in question, list which groups expect to gain, lose or carry extra work.",
             "phase": 0, "owner": "Change lead"},
            {"text": "Secure the undecided but influential stakeholders before announcing the decision widely.",
             "phase": 1, "owner": "CEO"},
            {"text": "Use confidential listening sessions to surface unwritten rules and concerns without assuming motives.",
             "phase": 1, "owner": "HR lead and line managers"},
            {"text": "Address perceived unfairness with transparent criteria, involvement and feedback routes.",
             "phase": 2, "owner": "Executive team"},
            {"text": "Decide openly which opponents can be won over and which must be managed rather than converted.",
             "phase": 1, "owner": "CEO and executive team"},
        ],
        "risks": [
            {"risk": "Labelling a group as 'losers' becomes self-fulfilling and hardens opposition.",
             "mitigation": "Test each assumed loss with the group concerned and look for ways to reduce it."},
            {"risk": "Concessions offered to one group create a sense of unfairness in another.",
             "mitigation": "Apply visible, consistent criteria for any concession."},
        ],
        "outcomes": [
            "Opposition anticipated before a decision is announced, not after.",
            "A clear order in which to build support.",
        ],
        "measures": [
            "Number of formal objections or escalations after each major decision.",
            "Share of previously undecided stakeholders who now support the decision.",
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
        "key_question": "What do people really assume, and where does that contradict what the organisation says?",
        "best_for": "Culture, identity and values questions, and clashes between groups with different assumptions.",
        "not_for": "It does not sequence a change or analyse power and political payoffs.",
        "names": ["schein", "three-level", "three level", "culture map"],
        "triggers": [
            "culture", "organisational culture", "identity", "values", "assumptions",
            "stand for", "culture clash", "clash", "how things are done", "beliefs",
            "norms", "behaviour", "bureaucratic", "agile", "mission", "purpose",
        ],
        "keywords": [
            "culture", "values", "assumptions", "beliefs", "identity",
            "norms", "rituals", "artefacts", "artifacts", "behaviour",
            "behavior", "trust", "psychological safety", "legacy", "subculture",
            "cultural", "mindset", "dna",
        ],
        "concepts": [
            ("Level 1: Artefacts", "What can be seen and heard: rituals, language, structures, offices."),
            ("Level 2: Espoused values", "What the organisation officially says it believes."),
            ("Level 3: Underlying assumptions", "Unspoken beliefs that actually drive behaviour."),
            ("Anomalies", "Gaps between levels 1 and 2 that point to a hidden level-3 assumption."),
        ],
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
        "actions": [
            {"text": "Compare visible practices and leadership messages with the values the organisation says it holds.",
             "phase": 0, "owner": "Executive team and HR lead"},
            {"text": "Explore assumptions behind resistance through interviews, observation and team discussion.",
             "phase": 1, "owner": "HR lead"},
            {"text": "Name the few assumptions that must change and the ones worth keeping, and say so publicly.",
             "phase": 1, "owner": "CEO"},
            {"text": "Pilot new behaviours and reinforce them through leadership role-modelling and everyday routines.",
             "phase": 2, "owner": "Line managers"},
            {"text": "Align promotion, recognition and approval processes with the behaviours being asked for.",
             "phase": 3, "owner": "HR lead"},
        ],
        "risks": [
            {"risk": "New values are announced while old approval and reward processes stay the same.",
             "mitigation": "Change at least one visible process early so the message is believed."},
            {"risk": "One group's culture is treated as the problem, which deepens the divide.",
             "mitigation": "Describe each group's assumptions neutrally and look for shared ones."},
        ],
        "outcomes": [
            "Fewer contradictions between what leaders say and what processes reward.",
            "A shared identity people can describe in their own words.",
        ],
        "measures": [
            "Pulse-survey agreement that leaders act in line with stated values.",
            "Time taken for routine decisions that the new culture is meant to speed up.",
        ],
    },
}

FRAMEWORK_ORDER = ["Kotter", "Pfeffer", "Ritti & Levy", "Schein"]

# Where two frameworks tend to give different advice. Shown whenever both
# are used, because the original design asks for contradictions to be
# surfaced rather than hidden.
FRAMEWORK_TENSIONS = {
    ("Kotter", "Schein"): (
        "Kotter pushes for urgency and early wins; Schein warns that underlying assumptions "
        "change slowly. Moving fast can produce compliance on the surface while the old "
        "assumptions continue underneath."
    ),
    ("Kotter", "Ritti & Levy"): (
        "Kotter asks for a broad coalition and open communication of the vision; Ritti & Levy "
        "suggest approaching stakeholders selectively and in sequence. Broadcasting too early "
        "can alert opponents before support is secured."
    ),
    ("Kotter", "Pfeffer"): (
        "Kotter assumes leaders can drive the change once a coalition exists; Pfeffer points "
        "out that the pace is set by whoever controls the resources the change depends on."
    ),
    ("Pfeffer", "Schein"): (
        "Pfeffer treats relationships as sources of leverage; Schein treats trust and shared "
        "assumptions as the foundation. Using leverage openly may win a decision but damage "
        "the trust a new culture needs."
    ),
    ("Pfeffer", "Ritti & Levy"): (
        "Both are political lenses, but Pfeffer looks at lasting structure (who depends on whom) "
        "while Ritti & Levy look at one decision at a time. An ally on one decision may be a "
        "loser on the next."
    ),
    ("Ritti & Levy", "Schein"): (
        "Ritti & Levy explain opposition through interests (what people stand to lose); Schein "
        "explains it through beliefs. A concession that satisfies an interest will not settle "
        "a disagreement that is really about values."
    ),
}

# ---------------------------------------------------------------------------
# General topics ("themes")
# ---------------------------------------------------------------------------
# A theme is a common change-management subject. When a question mentions
# one, its general diagnosis, actions, risks and measures can be used.
# Each action names the framework it comes from.
# "search_words" are plain words used to look for related document passages.

THEMES = {
    "resistance": {
        "search_words": "resistance losers loss autonomy disruption retraining",
        "label": "resistance to change",
        "keywords": ["resistance", "resist", "resisting", "resistant", "opposition", "pushback",
                     "reluctant", "reluctance", "sceptical", "cynical", "fear", "anxiety", "oppose"],
        "diagnosis": (
            "Resistance usually signals a perceived loss (status, autonomy, security or competence) "
            "or a clash with existing assumptions, more often than simple unwillingness."
        ),
        "actions": [
            {"text": "Find out what each resisting group believes it will lose, and check that belief with them directly.",
             "framework": "Ritti & Levy", "phase": 0, "owner": "Line managers and HR lead"},
            {"text": "Explain why the change is needed now, in terms that matter to the group concerned.",
             "framework": "Kotter", "phase": 1, "owner": "CEO and communications lead"},
            {"text": "Involve affected teams in designing how the change is implemented in their area.",
             "framework": "Kotter", "phase": 1, "owner": "Line managers"},
            {"text": "Test whether resistance reflects an assumption about 'how things are done here' and address that assumption openly.",
             "framework": "Schein", "phase": 1, "owner": "HR lead"},
            {"text": "Provide retraining and practical support where the change creates new skill demands.",
             "framework": "Kotter", "phase": 2, "owner": "HR lead"},
        ],
        "risks": [
            {"risk": "Resistance goes quiet but continues as slow compliance.",
             "mitigation": "Track behaviour and adoption, not only stated agreement."},
            {"risk": "All resistance is treated as obstruction and valid concerns are missed.",
             "mitigation": "Give every concern a named owner and a visible response."},
        ],
        "measures": [
            "Adoption rate of the new way of working by team.",
            "Voluntary turnover and absence in the most affected groups.",
            "Number of concerns raised and closed through feedback routes.",
        ],
        "outcomes": ["Earlier warning of problems.", "Faster, steadier adoption."],
    },
    "communication": {
        "search_words": "communication employees language vocabulary narrative",
        "label": "communication",
        "keywords": ["communication", "communicate", "communicating", "message", "messaging",
                     "narrative", "inform", "transparency", "announce", "announcement"],
        "diagnosis": (
            "Communication problems in change are rarely about volume; they are usually about "
            "consistency between leaders, relevance to each audience, and whether actions match words."
        ),
        "actions": [
            {"text": "Agree one short change story (why, what, what it means for you) and have every leader use it.",
             "framework": "Kotter", "phase": 0, "owner": "CEO and executive team"},
            {"text": "Adapt the message for each audience and deliver it through line managers, not only central channels.",
             "framework": "Kotter", "phase": 1, "owner": "Communications lead and line managers"},
            {"text": "Create two-way channels so questions and objections reach decision-makers.",
             "framework": "Kotter", "phase": 1, "owner": "Communications lead"},
            {"text": "Check that visible symbols and leadership behaviour match the message being given.",
             "framework": "Schein", "phase": 2, "owner": "Executive team"},
        ],
        "risks": [
            {"risk": "Leaders give different versions of the story.",
             "mitigation": "Brief leaders together and test the message before wider release."},
            {"risk": "Messages promise more than the organisation can deliver.",
             "mitigation": "Only announce commitments with an owner and a date."},
        ],
        "measures": [
            "Share of employees who can state the reason for the change.",
            "Questions received and answered through two-way channels.",
        ],
        "outcomes": ["A consistent understanding of the change.", "Fewer rumours and less uncertainty."],
    },
    "leadership": {
        "search_words": "leaders leadership empowerment hierarchy coalition board",
        "label": "leadership",
        "keywords": ["leadership", "leader", "leaders", "lead", "ceo", "executive", "executives",
                     "sponsor", "sponsorship", "role-model", "top team"],
        "diagnosis": (
            "Change stalls when the leadership team is not visibly aligned, or when leaders ask "
            "for behaviour they do not show themselves."
        ),
        "actions": [
            {"text": "Confirm the top team is aligned on the purpose, priorities and pace of the change before going wider.",
             "framework": "Kotter", "phase": 0, "owner": "CEO"},
            {"text": "Give each major workstream a named executive sponsor with clear decision rights.",
             "framework": "Pfeffer", "phase": 0, "owner": "CEO"},
            {"text": "Have leaders role-model the specific behaviours being asked of others.",
             "framework": "Schein", "phase": 1, "owner": "Executive team"},
            {"text": "Build direct relationships with the stakeholders whose support the leadership depends on.",
             "framework": "Pfeffer", "phase": 1, "owner": "CEO and Chair"},
        ],
        "risks": [
            {"risk": "Disagreements within the top team become visible and undermine confidence.",
             "mitigation": "Resolve disagreements privately and communicate one position."},
            {"risk": "The change is seen as one leader's project.",
             "mitigation": "Share visible ownership across the leadership team."},
        ],
        "measures": [
            "Leadership team alignment checked through structured review.",
            "Employee confidence in leadership, from pulse surveys.",
        ],
        "outcomes": ["Consistent direction from the top.", "Faster decisions."],
    },
    "culture": {
        "search_words": "culture cultural dna agile assumptions espouses",
        "label": "organisational culture",
        "keywords": ["culture", "cultural", "values", "assumptions", "beliefs", "identity", "norms",
                     "mindset", "dna", "behaviour", "behaviours", "subculture", "bureaucratic", "agile"],
        "diagnosis": (
            "Culture issues appear as a gap between what an organisation says it values and what "
            "its everyday processes actually reward."
        ),
        "actions": [
            {"text": "Identify where stated values and everyday practice contradict each other.",
             "framework": "Schein", "phase": 0, "owner": "Executive team and HR lead"},
            {"text": "Decide which inherited practices to keep, which to change and which to stop, and explain why.",
             "framework": "Schein", "phase": 1, "owner": "Executive team"},
            {"text": "Change one or two visible processes early to show the new culture is real.",
             "framework": "Schein", "phase": 2, "owner": "Executive team"},
            {"text": "Anchor new behaviours in recruitment, promotion and recognition.",
             "framework": "Kotter", "phase": 3, "owner": "HR lead"},
        ],
        "risks": [
            {"risk": "Culture change is reduced to a values statement and a campaign.",
             "mitigation": "Tie each value to a specific process or decision that will change."},
            {"risk": "Distinct sub-cultures are forced into one model too quickly.",
             "mitigation": "Agree which differences are acceptable and which are not."},
        ],
        "measures": [
            "Survey gap between stated values and experienced behaviour.",
            "Speed and level at which routine decisions are taken.",
        ],
        "outcomes": ["Closer match between words and practice.", "A clearer shared identity."],
    },
    "engagement": {
        "search_words": "employees staff empowerment identity",
        "label": "employee engagement",
        "keywords": ["engagement", "engage", "engaged", "morale", "motivation", "motivate",
                     "commitment", "involvement", "involve", "retention", "wellbeing"],
        "diagnosis": (
            "Engagement during change depends on people understanding what it means for them, "
            "having a say in how it is implemented, and seeing their concerns acted on."
        ),
        "actions": [
            {"text": "Tell people early what will change for them, what will not, and what is still undecided.",
             "framework": "Kotter", "phase": 0, "owner": "Line managers"},
            {"text": "Involve employees in implementation choices through working groups and local pilots.",
             "framework": "Kotter", "phase": 1, "owner": "Line managers"},
            {"text": "Recognise and publicise early contributions and wins from across the organisation.",
             "framework": "Kotter", "phase": 2, "owner": "Executive team"},
            {"text": "Listen for the informal concerns that do not surface in formal channels.",
             "framework": "Ritti & Levy", "phase": 1, "owner": "HR lead"},
        ],
        "risks": [
            {"risk": "Engagement activity is high but nothing changes as a result of feedback.",
             "mitigation": "Publish what was heard and what was done about it."},
            {"risk": "Key people leave during prolonged uncertainty.",
             "mitigation": "Identify critical roles early and give those people clarity first."},
        ],
        "measures": [
            "Engagement or pulse-survey scores over time.",
            "Retention of people in critical roles.",
            "Participation in change working groups.",
        ],
        "outcomes": ["Higher commitment to the change.", "Retention of critical knowledge."],
    },
    "stakeholders": {
        "search_words": "stakeholder relationships network investor dependencies structural hole",
        "label": "stakeholder relationships",
        "keywords": ["stakeholder", "stakeholders", "relationship", "relationships", "alliance",
                     "alliances", "partner", "partners", "investor", "investors", "board",
                     "retailer", "retailers", "government", "regulator", "network", "power", "influence"],
        "diagnosis": (
            "Stakeholder problems usually come from an unmanaged dependency, a missing direct "
            "relationship, or a stakeholder who expects to lose from the change."
        ),
        "actions": [
            {"text": "Map each key stakeholder: what they control, what they want and how the change affects them.",
             "framework": "Pfeffer", "phase": 0, "owner": "CEO office"},
            {"text": "Sort stakeholders into likely winners, losers and undecided for each major decision.",
             "framework": "Ritti & Levy", "phase": 0, "owner": "Change lead"},
            {"text": "Assign a senior relationship owner to each critical stakeholder.",
             "framework": "Pfeffer", "phase": 1, "owner": "CEO"},
            {"text": "Engage undecided but influential stakeholders before those who are firmly opposed.",
             "framework": "Ritti & Levy", "phase": 1, "owner": "Relationship owners"},
        ],
        "risks": [
            {"risk": "A stakeholder with control over a critical resource is engaged too late.",
             "mitigation": "Prioritise engagement by dependency, not by seniority alone."},
            {"risk": "Different leaders make inconsistent commitments to the same stakeholder.",
             "mitigation": "Keep one relationship owner and a shared record of commitments."},
        ],
        "measures": [
            "Stakeholder position (supportive, undecided, opposed) reviewed regularly.",
            "Critical stakeholders with a named relationship owner.",
        ],
        "outcomes": ["Fewer surprises from key stakeholders.", "Support secured before major decisions."],
    },
    "separation": {
        "search_words": "transitional service agreements dependency shared services standalone",
        "label": "separation and dependency on the former parent",
        "keywords": ["separation", "standalone", "independence", "independent", "transition",
                     "transitional", "dependency", "dependence", "systems", "shared", "services",
                     "exit", "parent", "carve-out", "infotech", "hr", "legal"],
        "diagnosis": (
            "In a separation, operational dependence on the former parent limits how independently "
            "the new organisation can act until each shared service has a clear exit path."
        ),
        "actions": [
            {"text": "List every shared service with its owner, end date, exit plan and the risk if it slips.",
             "framework": "Pfeffer", "phase": 0, "owner": "Functional leads (IT, HR, legal)"},
            {"text": "Agree priorities and a realistic exit sequence with the former parent, framed around what both sides gain.",
             "framework": "Ritti & Levy", "phase": 1, "owner": "CEO and CFO"},
            {"text": "Prepare the people who must move to new systems with training and support before each cut-over.",
             "framework": "Kotter", "phase": 2, "owner": "Functional leads and HR lead"},
            {"text": "Mark each completed exit as a visible step towards independence.",
             "framework": "Kotter", "phase": 2, "owner": "Communications lead"},
        ],
        "risks": [
            {"risk": "Exit dates slip and dependence continues longer than planned.",
             "mitigation": "Track each service to a dated milestone with a named owner."},
            {"risk": "Cut-over disrupts day-to-day operations.",
             "mitigation": "Phase cut-overs, rehearse them and keep a fallback."},
        ],
        "measures": [
            "Number of shared services exited against plan.",
            "Operational incidents during and after each cut-over.",
        ],
        "outcomes": ["Greater freedom to act independently.", "A clearer standalone identity."],
    },
    "governance": {
        "search_words": "governance dispute litigation authority charter",
        "label": "governance and disputes",
        "keywords": ["governance", "dispute", "litigation", "lawsuit", "autonomy", "charter",
                     "conflict", "disagreement", "negotiate", "negotiation", "compromise", "mission"],
        "diagnosis": (
            "A governance dispute is both a contest of interests (who decides) and often a contest "
            "of values (what the organisation is for), and each needs a different response."
        ),
        "actions": [
            {"text": "Separate the issues that are about decision rights from those that are about values.",
             "framework": "Schein", "phase": 0, "owner": "CEO and General Counsel"},
            {"text": "Identify what each side must protect and where a trade is possible.",
             "framework": "Ritti & Levy", "phase": 0, "owner": "CEO"},
            {"text": "Secure the support of influential undecided parties before negotiating.",
             "framework": "Ritti & Levy", "phase": 1, "owner": "CEO and Chair"},
            {"text": "Record any agreement in a clear document that states who decides what.",
             "framework": "Pfeffer", "phase": 2, "owner": "General Counsel"},
        ],
        "risks": [
            {"risk": "The dispute becomes public and shapes external perception.",
             "mitigation": "Agree communication rules with the other party early."},
            {"risk": "A settlement on decision rights leaves the values disagreement unresolved.",
             "mitigation": "Address the values question explicitly, not only the legal one."},
        ],
        "measures": [
            "Open disputed issues, tracked to resolution.",
            "Management time spent on the dispute.",
        ],
        "outcomes": ["Less distraction for leadership.", "Clearer decision rights."],
    },
    "momentum": {
        "search_words": "urgency quickly momentum wins distraction",
        "label": "urgency and momentum",
        "keywords": ["urgency", "urgent", "momentum", "stall", "stalling", "stalled", "slow",
                     "pace", "speed", "delay", "fatigue", "readiness", "quickly"],
        "diagnosis": (
            "Momentum is lost when the reason for change stops feeling pressing, early results are "
            "not visible, or barriers are left in place."
        ),
        "actions": [
            {"text": "Restate the case for change using current external and internal evidence.",
             "framework": "Kotter", "phase": 0, "owner": "CEO"},
            {"text": "Choose two or three results achievable within months and make them visible.",
             "framework": "Kotter", "phase": 1, "owner": "Change lead"},
            {"text": "Remove the specific processes or approvals that slow the change down.",
             "framework": "Kotter", "phase": 2, "owner": "Executive team"},
            {"text": "Check which actors outside the leadership team control the pace, and engage them.",
             "framework": "Pfeffer", "phase": 1, "owner": "CEO"},
        ],
        "risks": [
            {"risk": "Urgency turns into pressure that exhausts people.",
             "mitigation": "Limit the number of simultaneous priorities."},
            {"risk": "Quick wins are chosen for visibility, not relevance.",
             "mitigation": "Select wins that prove the central case for the change."},
        ],
        "measures": [
            "Short-term wins delivered and communicated.",
            "Barriers logged and removed.",
        ],
        "outcomes": ["Sustained confidence in the change.", "Earlier evidence that the change works."],
    },
}

# Inference rules: what a passage of a given kind usually implies under its
# framework. The "role" of a passage is worked out in answers.passage_role().
INFERENCE_RULES = {
    "winner": "Listed as a winner from this decision, so a likely source of support (Ritti & Levy).",
    "loser": ("Listed as a loser from this decision, so a likely source of resistance unless the loss "
              "is reduced, compensated or openly managed (Ritti & Levy)."),
    "fence_sitter": ("Listed as undecided. Under Ritti & Levy, fence-sitters are usually worth early "
                     "effort because their position can still move."),
    "strategy": ("This is the sequence your own notes propose for this decision. Treat it as a "
                 "hypothesis to test, not a confirmed plan."),
    "structural_hole": ("A structural hole is a missing direct relationship. Under Pfeffer it limits "
                        "access to information and influence until someone bridges it."),
    "controls": ("Under Pfeffer, whoever controls a resource that others need holds power over them, "
                 "so progress on anything needing this resource depends on this actor."),
    "dependency": ("Under Pfeffer, a dependency is a source of the other party's power. Reducing it, "
                   "or building alternatives, strengthens the dependent party."),
    "risk": "Flagged as a risk in your own notes.",
    "interest": ("States what this actor wants. Proposals framed around this interest are more likely "
                 "to win their support (Pfeffer; Ritti & Levy)."),
    "power_base": "A source of influence that can be drawn on (Pfeffer).",
    "brokerage": ("A brokerage move: using an existing relationship to reach someone not yet "
                  "directly connected (Pfeffer)."),
    "probe": ("A diagnostic question from your notes for surfacing hidden assumptions (Schein). "
              "It is a question to ask, not a finding."),
    "culture_gap": ("A gap between what is said and what is assumed. Under Schein, behaviour follows "
                    "the assumption, so announcements alone are unlikely to close the gap."),
    "artefact": ("A visible artefact (Schein Level 1). Artefacts are easy to observe but hard to "
                 "interpret without knowing the assumptions behind them."),
    "espoused_value": ("An espoused value (Schein Level 2): what is officially claimed, which may or "
                       "may not match everyday behaviour."),
    "assumption": ("Recorded in your notes as a likely underlying assumption (Schein Level 3). "
                   "It is a hypothesis to test, not an established fact."),
    "kotter_step": ("Your notes place this issue at this step of Kotter's model. Under Kotter, an "
                    "unresolved earlier step tends to undermine the steps that follow."),
    "key_tension": "Named in your context document as one of the key tensions.",
}

# Roles that describe a risk, a benefit or a way of reducing risk. Used when
# a question asks about risks, benefits and stakeholder implications.
RISK_ROLES = ["loser", "risk", "structural_hole", "dependency", "key_tension", "culture_gap", "fence_sitter"]
BENEFIT_ROLES = ["winner"]
MITIGATION_ROLES = ["strategy", "brokerage"]

# General questions worth asking before acting on any recommendation.
VALIDATION_QUESTIONS = [
    "What evidence, beyond these documents, confirms that this is the real problem?",
    "Which affected groups have been asked directly, and what did they say?",
    "What would have to be true for this recommendation to be wrong?",
]

# Words that show a question is about organisations and change. A question
# with none of these words and no matching document passage is treated as
# outside the tool's scope.
CHANGE_VOCABULARY = """
change changes transformation transition restructure restructuring reorganisation reorganization
organisation organization organisational organizational management manager managers leadership
leader leaders employee employees staff workforce team teams culture cultural stakeholder
stakeholders resistance communication engagement strategy roadmap implementation plan framework
frameworks model intervention merger acquisition separation demerger spin-off governance board
investor investors coalition vision urgency momentum values assumptions power influence politics
political morale motivation training adoption sponsor readiness consulting consultant company
business ceo executive executives hr integration project programme program
""".split()

EXAMPLE_QUESTIONS = [
    "What is the main change management challenge facing TMICC?",
    "How should TMICC manage employee resistance?",
    "Which framework fits the Ben & Jerry's governance dispute, and why?",
    "Compare Kotter, Schein, Pfeffer and Ritti & Levy.",
    "Build a roadmap for exiting the Unilever transitional service agreements.",
    "Who wins and who loses if brand decisions are centralised?",
    "Who is Trian and what do they want?",
]
