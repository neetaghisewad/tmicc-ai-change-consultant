"""Work out what was asked: the type of question, the frameworks that apply,
the general topics involved, and whether the documents contain evidence.

Everything here is a transparent rule (word and phrase matching). There is no
AI model, so the app can always show why it made a choice.
"""

import re

from . import knowledge
from . import retrieval

# ---------------------------------------------------------------------------
# Question types
# ---------------------------------------------------------------------------
# Each type has patterns (regular expressions). The first type whose pattern
# is found in the question wins, so the order of this list matters.

QUESTION_TYPES = [
    ("greeting", [
        r"^\s*(hi|hello|hey|good (morning|afternoon|evening)|thanks|thank you)\b[\s!.,]*$",
        r"^\s*(help|what can you do|what can i ask|how do you work|how does this work)\b",
    ]),
    ("about_tool", [
        r"\b(are you|is this|is it)\b.*\b(ai|a\.i\.|chatbot|chatgpt|gpt|llm|copilot|human|robot|real person)\b",
        r"\bwho (are|made|built) you\b",
    ]),
    ("compare", [
        r"\bcompar", r"\bversus\b", r"\bvs\.?\b", r"\bdifference", r"\bdiffer\b", r"\bcontrast",
        r"\bstrengths and (weaknesses|limitations)\b", r"\bpros and cons of (the )?(frameworks|models|kotter|schein|pfeffer|ritti)",
    ]),
    ("framework_choice", [
        r"\bwhich\b.{0,40}\b(framework|model|lens|theory|approach)s?\b",
        r"\bwhat\b.{0,25}\b(framework|model|lens|theory)\b.{0,40}\b(use|apply|fit|suit|appropriate|best|relevant)",
        r"\b(best|right|most (appropriate|suitable|relevant|useful))\b.{0,20}\b(framework|model|lens|theory)\b",
        r"\bshould (i|we|peter|tmicc) use\b.{0,30}\b(kotter|schein|pfeffer|ritti|levy)\b",
    ]),
    ("diagnose", [
        r"\b(main|biggest|key|core|central|greatest|primary|major|top)\b.{0,40}\b(challenge|problem|issue|tension|obstacle|barrier)s?\b",
        r"\bwhat\b.{0,30}\b(challenge|problem|issue|tension)s?\b.{0,20}\b(facing|face|faces|for|at|in)\b",
        r"\bdiagnos", r"\bwhat is going wrong\b", r"\broot cause",
        r"\bwhy\b.{0,60}\b(stall|fail|struggl|slow|stuck|difficult|hard|resist)",
    ]),
    ("plan", [
        r"\broad\s?map\b", r"\baction plan\b", r"\bimplementation plan\b", r"\bchange plan\b",
        r"\bstrategy\b", r"\btimeline\b", r"\bnext steps?\b", r"\bstep[- ]by[- ]step\b",
        r"\b(first|next) (30|60|90|100) days\b", r"\b(develop|build|create|design|draft|write|give me|propose)\b.{0,30}\bplan\b",
        r"\bhow (do|should|can|would) (we|i|peter|tmicc)\b.{0,20}\b(implement|roll out|sequence|phase|exit)\b",
    ]),
    ("risk_benefit", [
        r"\brisks?\b", r"\bdanger", r"\bdownside", r"\bwhat could go wrong\b", r"\bbenefits?\b",
        r"\badvantage", r"\bupside", r"\boutcomes?\b", r"\bimplications?\b", r"\bimpact\b",
        r"\bconsequence", r"\bpros and cons\b", r"\btrade-?offs?\b",
    ]),
    ("stakeholder", [
        r"\bwho (wins|loses|gains|benefits|has|holds|controls|should|can|could|will|might|are the|is likely|stands to)\b",
        r"\bwinners?\b", r"\blosers?\b", r"\bfence[- ]?sitters?\b", r"\bkey stakeholders\b",
        r"\bstakeholder (map|analysis|strategy)\b", r"\ballies\b", r"\balliances?\b",
        r"\bwho\b.{0,30}\b(power|influence|support|oppose|resist|block)",
    ]),
    ("explain_framework", [
        r"\b(what (is|are)|explain|describe|tell me about|how does|summari[sz]e|outline)\b.{0,40}\b(kotter|schein|pfeffer|ritti|levy|8[- ]step|eight[- ]step|three[- ]level)",
    ]),
    ("fact", [
        r"^\s*(tell me about|what do (we|you|i) know about|background on|summari[sz]e|give me (the )?(facts|background))\b",
        r"^\s*what (do|does) (the|my|your|these) (documents?|notes|files) say\b",
        r"^\s*(what|how) about\b",
        r"^\s*(who|when|where)\b",
        r"^\s*(what|which)\b.{0,12}\b(is|are|was|were|did|does|do)\b",
        r"^\s*(how many|how much)\b",
        r"^\s*(is|are|was|were|did|does|do|has|have)\b",
    ]),
]

# A question that looks like a fact question but contains one of these words
# is really asking for advice.
ADVICE_WORDS = (
    r"\b(should|how (can|do|could|would|might|to)|manage|handle|deal with|address|overcome|"
    r"improve|reduce|increase|build|strengthen|advice|recommend|best way|what to do)\b"
)

# Extra sections the user asked for, whatever the question type.
EXTRA_REQUESTS = {
    "plan": r"\b(road\s?map|action plan|implementation plan|timeline|step[- ]by[- ]step|next steps?|plan)\b",
    "risks": r"\b(risks?|danger|downside|what could go wrong|limitation|dependenc|mitigat)",
    "benefits": r"\b(benefits?|advantage|upside|outcomes?|success measure|kpi|metric|measure)",
    "stakeholders": r"\b(stakeholders?|winners?|losers?|who (wins|loses|gains))\b",
}

# Words that point back to an earlier answer.
FOLLOW_UP_PATTERNS = [
    r"^\s*(and|but|so|also|ok|okay)\b",
    r"^\s*(what|how) about\b",
    r"^\s*(tell me more|more detail|go on|expand|elaborate|continue|why\??\s*$)",
    r"\b(that|this|those|these|it|them|they)\s*([?.!,]|$)",
    r"\b(that|this|those|these|it|them|they)\s+(is|are|was|will|would|should|could|can|be|work|mean|affect|happen|take|fail|go)\b",
    r"\b(of|for|about|with|on|to|in) (that|this|it|them|those|these)\b(?!\s+[a-z])",
    r"\b(the same|previous answer|you (just )?said|you mentioned|above|earlier|your (recommendation|plan|answer|suggestion)s?)\b",
    r"\b(that|this|the|those|these) (plan|roadmap|approach|strategy|recommendation|recommendations|decision|intervention|option|framework|answer|action|actions|risk|risks)\b",
]

FIGURE_PATTERN = (
    r"\b(how much|how many|revenue|profit|sales|turnover|share price|valuation|market share|"
    r"headcount|number of|budget|percent|percentage|market cap|earnings|salary|cost of)\b|%"
)


def classify_question(text):
    """Return the question type, e.g. "plan", "compare", "fact" or "advice"."""
    lowered = str(text or "").lower()
    for question_type, patterns in QUESTION_TYPES:
        for pattern in patterns:
            if re.search(pattern, lowered):
                if question_type == "fact" and re.search(ADVICE_WORDS, lowered):
                    return "advice"
                return question_type
    return "advice"


def extra_requests(text):
    """Return the set of extra sections requested: plan, risks, benefits, stakeholders."""
    lowered = str(text or "").lower()
    return {name for name, pattern in EXTRA_REQUESTS.items() if re.search(pattern, lowered)}


def is_follow_up(text):
    """True if the wording points back to an earlier answer ("what about that?")."""
    lowered = str(text or "").lower()
    return any(re.search(pattern, lowered) for pattern in FOLLOW_UP_PATTERNS)


# ---------------------------------------------------------------------------
# Frameworks and themes
# ---------------------------------------------------------------------------

def mentioned_frameworks(text):
    """Return frameworks the user named directly, in a fixed order."""
    lowered = str(text or "").lower()
    found = []
    for name in knowledge.FRAMEWORK_ORDER:
        if any(alias in lowered for alias in knowledge.FRAMEWORKS[name]["names"]):
            found.append(name)
    return found


def _phrase_in(phrase, stems):
    """True if every word of the phrase appears in the question."""
    phrase_stems = retrieval.tokenize(phrase)
    return bool(phrase_stems) and all(item in stems for item in phrase_stems)


def score_frameworks(text, results=None):
    """Score each framework for a question.

    Points:  named directly = 10, routing trigger = 2, keyword = 1,
             plus up to 2 points when the best-matching document passages
             come from that framework's own document.
    Returns (scores, reasons, rule_scores). `reasons` explains every point
    awarded; `rule_scores` holds only the points from rules (not from where
    passages were found), because a framework is never selected on document
    location alone.
    """
    stems = set(retrieval.tokenize(text))
    scores = {name: 0.0 for name in knowledge.FRAMEWORK_ORDER}
    reasons = {name: [] for name in knowledge.FRAMEWORK_ORDER}

    for name in mentioned_frameworks(text):
        scores[name] += 10
        reasons[name].append("named in the question")

    for name in knowledge.FRAMEWORK_ORDER:
        framework = knowledge.FRAMEWORKS[name]
        counted = set()   # so one word is not counted twice for the same framework
        triggers = []
        for phrase in framework["triggers"]:
            key = tuple(retrieval.tokenize(phrase))
            if key not in counted and _phrase_in(phrase, stems):
                counted.add(key)
                counted.update((item,) for item in key)
                triggers.append(phrase)
                scores[name] += 2
        keywords = []
        for word in framework["keywords"]:
            key = tuple(retrieval.tokenize(word))
            if key not in counted and _phrase_in(word, stems):
                counted.add(key)
                keywords.append(word)
                scores[name] += 1
        if triggers:
            reasons[name].append("routing topics matched: " + ", ".join(triggers[:5]))
        if keywords:
            reasons[name].append("keywords matched: " + ", ".join(keywords[:5]))

    rule_scores = dict(scores)

    # Evidence from the documents: where did the best passages come from?
    if results:
        top_score = results[0]["score"]
        evidence = {name: 0.0 for name in knowledge.FRAMEWORK_ORDER}
        for result in results[:6]:
            topic = result["passage"]["topic"]
            if topic in evidence and not result["related"]:
                evidence[topic] += result["score"] / top_score
        for name, value in evidence.items():
            if value > 0:
                points = round(min(2.0, value), 1)
                scores[name] += points
                reasons[name].append(
                    f"relevant passages found in {_file_for(name)} (+{points})"
                )
    return scores, reasons, rule_scores


def _file_for(framework_name):
    from .documents import KNOWLEDGE_DOCUMENTS
    for item in KNOWLEDGE_DOCUMENTS:
        if item["topic"] == framework_name:
            return item["file"]
    return framework_name


def select_frameworks(scores, question_type, named, many_topics=False, rule_scores=None):
    """Choose which frameworks to use, following the original routing rules.

    1. One clear fit  -> use that framework only.
    2. Two fit        -> use both and say so.
    3. No fit         -> use none and say so honestly (never force a fit).
    """
    if question_type == "compare":
        return named if len(named) >= 2 else list(knowledge.FRAMEWORK_ORDER)
    ranked = sorted(knowledge.FRAMEWORK_ORDER, key=lambda name: scores[name], reverse=True)
    best = scores[ranked[0]]
    if best < 2:
        return []
    limit = 3 if question_type in ("plan", "diagnose", "risk_benefit") or many_topics else 2
    chosen = [name for name in ranked if scores[name] >= max(2, 0.5 * best)]
    if rule_scores is not None:  # at least one rule must have matched
        chosen = [name for name in chosen if rule_scores[name] > 0]
    if question_type == "plan" and scores["Kotter"] >= 2 and "Kotter" not in chosen:
        chosen.append("Kotter")  # a plan needs sequencing, which is Kotter's subject
    if named:  # frameworks the user asked for always come first
        chosen = named + [name for name in chosen if name not in named]
        limit = max(limit, len(named))
    return chosen[:limit]


def match_themes(text, limit=5):
    """Return the general topics (themes) mentioned, in the order they appear."""
    ordered_stems = retrieval.tokenize(text)
    stems = set(ordered_stems)
    found = []
    for key, theme in knowledge.THEMES.items():
        positions = []
        for word in theme["keywords"]:
            if _phrase_in(word, stems):
                positions.append(ordered_stems.index(retrieval.tokenize(word)[0]))
        if positions:
            found.append((min(positions), key))
    found.sort()
    return [key for _, key in found[:limit]]


# ---------------------------------------------------------------------------
# Scope and evidence
# ---------------------------------------------------------------------------

def uses_change_vocabulary(text):
    stems = set(retrieval.tokenize(text))
    vocabulary = {retrieval.stem(word) for word in knowledge.CHANGE_VOCABULARY}
    return bool(stems & vocabulary)


def evidence_level(index, results):
    """Describe how well the documents cover the question: good, limited or none."""
    exact = [result for result in results if not result["related"]]
    if not exact:
        return "none"
    distinctive = retrieval.distinctive_matches(index, exact)
    if distinctive >= 2 or (distinctive >= 1 and exact[0]["score"] >= 3):
        return "good"
    return "limited"


# ---------------------------------------------------------------------------
# Putting it together
# ---------------------------------------------------------------------------

def analyse(question, index, previous=None):
    """Analyse a question and return everything the answer builder needs.

    `previous` is the analysis of the last question in the conversation (or
    None). It is used only when the new question is worded as a follow-up.
    """
    question = str(question or "").strip()
    question_type = classify_question(question)
    named = mentioned_frameworks(question)
    # "Is Kotter better than Schein for culture?" is really a comparison.
    if len(named) >= 2 and question_type in ("fact", "advice", "framework_choice"):
        if re.search(r"\b(better|or|than|between|rather)\b", question.lower()):
            question_type = "compare"

    # Follow-up handling: reuse the topic of the previous question.
    follow_up = bool(previous) and question_type not in ("greeting", "about_tool") and is_follow_up(question)
    search_text = question
    if follow_up:
        search_text = question + " " + previous["topic_text"]

    results = retrieval.search(index, search_text, max_results=14)
    scores, reasons, rule_scores = score_frameworks(search_text, results)
    if follow_up and not named:
        # Keep the lenses already in use so the conversation stays coherent.
        for name in previous["frameworks"]:
            scores[name] += 2
            rule_scores[name] += 2
            reasons[name].append("carried over from your previous question")
    themes = match_themes(search_text)
    frameworks = select_frameworks(scores, question_type, named, many_topics=len(themes) >= 3,
                                   rule_scores=rule_scores)
    # A request for an overall strategy with no specific topic draws on all
    # four lenses, with Kotter (sequencing) first.
    if question_type == "plan" and not themes and not named and not follow_up:
        frameworks = list(knowledge.FRAMEWORK_ORDER)
        for name in frameworks:
            reasons[name].append("a whole-programme plan draws on all four lenses")

    # A stakeholder question with no clear lens uses the two political lenses.
    if question_type == "stakeholder" and not frameworks:
        frameworks = ["Pfeffer", "Ritti & Levy"]
        reasons["Pfeffer"].append("stakeholder questions are covered by the power and dependency lens")
        reasons["Ritti & Levy"].append("stakeholder questions are covered by the winners-and-losers lens")

    evidence = evidence_level(index, results)
    in_scope = bool(
        uses_change_vocabulary(search_text) or named or themes or frameworks
        or evidence == "good" or (evidence == "limited" and retrieval.query_terms(search_text))
    )
    if question_type in ("greeting", "about_tool"):
        in_scope = True

    return {
        "question": question,
        "type": question_type if in_scope else "out_of_scope",
        "extras": extra_requests(question),
        "follow_up": follow_up,
        "previous_question": previous["question"] if follow_up else None,
        "search_text": search_text,
        # What a later follow-up should inherit as "the topic".
        "topic_text": search_text if follow_up else question,
        "results": results,
        "evidence": evidence,
        "missing_words": retrieval.words_not_in_documents(index, question),
        "named_frameworks": named,
        "frameworks": frameworks,
        "framework_scores": scores,
        "framework_reasons": reasons,
        "themes": themes,
        "asks_for_figures": bool(re.search(FIGURE_PATTERN, question.lower())),
        "has_topic": bool(retrieval.query_terms(search_text)),
    }
