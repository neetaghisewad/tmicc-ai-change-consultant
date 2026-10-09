"""Assemble a structured, source-labelled answer.

Every statement in an answer carries one of three labels:

    document   - quoted word for word from one of the five Word files
    inference  - a rule linking a quoted passage to a framework idea
    general    - standard change-management guidance from knowledge.py

The app never writes its own sentences stating facts about TMICC. TMICC
content appears only as quotations, each with its file and section.

How an answer is built
----------------------
1. questions.analyse() works out the question type, frameworks and evidence.
2. One "build_..." function below is chosen for that question type. Each
   returns a list of sections, so different questions get different layouts.
3. render_markdown() turns the sections into text for the chat window.
"""

import re

from . import documents
from . import knowledge
from . import questions
from . import retrieval

DOC = knowledge.LABEL_DOCUMENT
INF = knowledge.LABEL_INFERENCE
GEN = knowledge.LABEL_GENERAL


# ---------------------------------------------------------------------------
# The knowledge base (documents + search index)
# ---------------------------------------------------------------------------

def build_knowledge_base(loaded_documents=None):
    """Load the documents once and prepare them for searching."""
    loaded = loaded_documents if loaded_documents is not None else documents.load_documents()
    passages = documents.all_passages(loaded)
    return {
        "documents": loaded,
        "passages": passages,
        "index": retrieval.build_index(passages),
    }


# ---------------------------------------------------------------------------
# Small building blocks
# ---------------------------------------------------------------------------

def make_item(label, text, source="", children=None):
    return {"label": label, "text": text, "source": source, "children": children or []}


def make_section(title, items=None, intro="", table=None, note=""):
    return {"title": title, "items": items or [], "intro": intro, "table": table, "note": note}


def passage_role(passage):
    """Say what kind of statement a passage is, from its heading and label.

    Examples: a bullet under "LOSERS" is a "loser"; a Pfeffer bullet starting
    "Controls:" is "controls". The role decides which inference rule applies.
    """
    topic = passage["topic"]
    heading = passage["heading"].upper()
    subhead = passage["subhead"].upper()
    label = passage["label"].lower()
    text = passage["text"].lower()

    if topic == "Ritti & Levy":
        if passage["kind"] == "heading":
            return "decision"
        if label == "strategy":
            return "strategy"
        if subhead.startswith("WINNER"):
            return "winner"
        if subhead.startswith("LOSER"):
            return "loser"
        if subhead.startswith("FENCE"):
            return "fence_sitter"
    if topic == "Pfeffer":
        if heading.startswith("BROKERAGE"):
            return "brokerage"
        if "structural hole" in label or "structural hole" in text:
            return "structural_hole"
        if label in ("controls", "control"):
            return "controls"
        if label.startswith("dependenc"):
            return "dependency"
        if label == "risk":
            return "risk"
        if label in ("incentive", "wants"):
            return "interest"
        if label == "power base":
            return "power_base"
        return "actor_fact"
    if topic == "Schein":
        if heading.startswith("ANOMALY"):
            return "probe"
        if "TENSION" in subhead:
            return "culture_gap"
        if passage["kind"] == "heading":
            return "level_heading"
        if heading.startswith("LEVEL 1"):
            return "artefact"
        if heading.startswith("LEVEL 2"):
            return "espoused_value"
        if heading.startswith("LEVEL 3"):
            return "assumption"
    if topic == "Kotter" and label.lower().startswith("step"):
        return "kotter_step"
    if topic == "TMICC context":
        if heading.startswith("KEY TENSION"):
            return "key_tension"
        if heading.startswith("FOUR FRAMEWORKS"):
            return "routing"
    return "context"


def quote(passage):
    """Return the passage as a quotation (the text itself is never altered)."""
    return "“" + passage["text"].replace('"', "'") + "”"


def document_item(passage, with_inference=True):
    """A quoted passage, optionally followed by the inference its role allows."""
    children = []
    if with_inference:
        rule = knowledge.INFERENCE_RULES.get(passage_role(passage))
        if rule:
            children.append(make_item(INF, rule))
    return make_item(DOC, quote(passage), documents.source_label(passage), children)


def general_item(text, framework=""):
    return make_item(GEN, text, framework)


def relevant(results, limit=6, ratio=0.35, exact_only=True):
    """Keep only the clearly relevant results (close to the best score)."""
    if not results:
        return []
    cut_off = results[0]["score"] * ratio
    kept = []
    for result in results:
        if result["score"] < cut_off:
            continue
        if exact_only and result["related"]:
            continue
        if passage_role(result["passage"]) == "routing":
            continue  # a note about which framework to use, not evidence about TMICC
        kept.append(result)
    return kept[:limit]


def evidence_items(results, limit=6, with_inference=True):
    return [document_item(result["passage"], with_inference) for result in relevant(results, limit)]


def passages_with_role(kb, roles, topic=None):
    return [
        passage for passage in kb["passages"]
        if passage_role(passage) in roles and (topic is None or passage["topic"] == topic)
    ]


# ---------------------------------------------------------------------------
# Looking up whole blocks of a document
# ---------------------------------------------------------------------------

def find_decision(kb, analysis):
    """Return the Ritti & Levy decision matched for this question (found once)."""
    return analysis.get("decision", [])


def match_decision(kb, analysis):
    """Find the Ritti & Levy decision the question is about, if any.

    Returns the list of passages for that decision (heading, winners, losers,
    fence-sitters, strategy) or [] when no decision clearly matches.
    """
    results = retrieval.search(kb["index"], analysis["search_text"], max_results=60,
                               topics=["Ritti & Levy"])
    headings = [
        result for result in results
        if result["passage"]["kind"] == "heading" and not result["related"]
        and retrieval.distinctive_matches(kb["index"], [result], minimum_idf=1.6) >= 1
        and result["score"] >= 3
    ]
    if not headings:
        return []
    heading_text = headings[0]["passage"]["text"]
    return documents.passages_under_heading(kb["passages"], headings[0]["passage"]["file"], heading_text)


def find_actors(kb, analysis):
    """Find Pfeffer network-map actors named in the question.

    Returns a list of (heading, passages). An actor matches when a word of
    its heading (name or role) appears in the question.
    """
    question_stems = set(retrieval.query_terms(analysis["search_text"]))
    blocks = []
    seen = set()
    for passage in kb["passages"]:
        heading = passage["heading"]
        if passage["topic"] != "Pfeffer" or not heading or heading in seen:
            continue
        if heading.upper().startswith("BROKERAGE"):
            continue
        seen.add(heading)
        heading_stems = set(retrieval.query_terms(heading))
        if question_stems & heading_stems:
            blocks.append((heading, documents.passages_under_heading(kb["passages"], passage["file"], heading)))
    return blocks


def decision_sections(decision):
    """Lay out a Ritti & Levy decision as winners / losers / fence-sitters / strategy."""
    if not decision:
        return []
    heading = decision[0]
    groups = [("winner", "Winners"), ("loser", "Losers"), ("fence_sitter", "Fence-sitters"),
              ("strategy", "Sequence proposed in your notes")]
    items = [make_item(DOC, quote(heading), heading["file"])]
    for role, title in groups:
        members = [passage for passage in decision if passage_role(passage) == role]
        if not members:
            continue
        children = [make_item(DOC, quote(passage), "") for passage in members]
        children.append(make_item(INF, knowledge.INFERENCE_RULES[role]))
        items.append(make_item("", f"**{title}**", "", children))
    return [make_section("Payoff map from your documents (Ritti & Levy)", items)]


def pace_tension(kb, analysis):
    """Surface one contradiction the documents themselves contain.

    If a relevant passage calls for speed, and the Schein document records an
    inherited assumption about consensus or lengthy approval, show both.
    """
    fast = None
    candidates = [result["passage"] for result in relevant(analysis["results"], limit=5)]
    candidates += analysis.get("extra_passages", [])
    for passage in candidates:
        if passage["topic"] != "Schein" and re.search(r"\b(quickly|fast|early|urgency)\b", passage["text"].lower()):
            fast = passage
            break
    if not fast:
        return None
    slow = None
    for pattern in (r"consensus before", r"lengthy approval"):
        for passage in kb["passages"]:
            if passage["topic"] == "Schein" and re.search(pattern, passage["text"].lower()):
                slow = passage
                break
        if slow:
            break
    if not slow:
        return None
    text = (
        f"Your notes call for speed here ({quote(fast)}, {fast['file']}) while {slow['file']} records "
        f"{quote(slow)} under “{slow['section']}”. If that holds, moving fast may meet quiet "
        "resistance, so the two lenses pull in different directions on pace."
    )
    return make_item(INF, text)


# ---------------------------------------------------------------------------
# Sections shared by several question types
# ---------------------------------------------------------------------------

def routing_note(kb, name, analysis):
    """Return the documents' own "use this framework for..." note, if it matches."""
    question_stems = set(retrieval.tokenize(analysis["search_text"]))
    for passage in kb["passages"]:
        if passage_role(passage) == "routing" and passage["subhead"].upper().startswith(name.upper()):
            if question_stems & set(retrieval.tokenize(passage["text"])):
                return passage
    return None


def framework_section(kb, analysis):
    """Which frameworks were used and why (or an honest 'none fit')."""
    chosen = analysis["frameworks"]
    if not chosen:
        return make_section(
            "Frameworks",
            [general_item(
                "No single framework clearly fits this question, so none has been forced onto it. "
                "The guidance below is general change-management practice."
            )],
        )
    items = []
    for name in chosen:
        framework = knowledge.FRAMEWORKS[name]
        reasons = analysis["framework_reasons"].get(name) or ["selected by the rules"]
        score = round(analysis["framework_scores"].get(name, 0), 1)
        children = [make_item("", f"Why chosen (rule score {score}): " + "; ".join(reasons))]
        note = routing_note(kb, name, analysis)
        if note:
            children.append(make_item(DOC, quote(note), documents.source_label(note)))
        items.append(make_item("", f"**{framework['title']}** — {framework['focus']}", "", children))
    return make_section("Frameworks used and why", items)


def tension_section(kb, analysis):
    """Where the chosen frameworks disagree. Never hidden."""
    chosen = analysis["frameworks"]
    items = []
    for first_index, first in enumerate(chosen):
        for second in chosen[first_index + 1:]:
            text = knowledge.FRAMEWORK_TENSIONS.get((first, second)) or knowledge.FRAMEWORK_TENSIONS.get((second, first))
            if text:
                items.append(general_item(text, f"{first} vs {second}"))
    document_tension = pace_tension(kb, analysis)
    if document_tension:
        items.insert(0, document_tension)
    if not items:
        return None
    return make_section("Where the frameworks pull in different directions", items[:4])


def collect_actions(analysis, per_source=5):
    """Gather general actions from the matched themes and chosen frameworks."""
    actions = []
    seen = set()
    chosen = analysis["frameworks"]
    for key in analysis["themes"]:
        for action in knowledge.THEMES[key]["actions"][: per_source + 1]:
            if action["text"] not in seen:
                seen.add(action["text"])
                actions.append(dict(action))
    for name in chosen:
        for action in knowledge.FRAMEWORKS[name]["actions"][:per_source]:
            if action["text"] not in seen:
                seen.add(action["text"])
                actions.append(dict(action, framework=name))
    return actions


def kotter_step_section(kb):
    """Table pairing each Kotter step (general) with the note in the Kotter document."""
    steps = passages_with_role(kb, ["kotter_step"], topic="Kotter")
    if not steps:
        return None, []
    concepts = knowledge.FRAMEWORKS["Kotter"]["concepts"]
    rows = []
    for position, step in enumerate(steps):
        meaning = concepts[position][1] if position < len(concepts) else ""
        rows.append([meaning, quote(step)])
    section = make_section(
        "Where your documents place TMICC on Kotter's eight steps",
        intro=(f"{knowledge.LABEL_TEXT[GEN]} — left column: the standard meaning of each step. "
               f"{knowledge.LABEL_TEXT[DOC]} — right column: quoted from {steps[0]['file']}."),
        table={"headers": ["Kotter step (general)", "Your document says"], "rows": rows},
    )
    return section, steps


# The kind of passage that best represents each framework's document.
HIGHLIGHT_ROLES = {
    "Kotter": ["kotter_step"],
    "Pfeffer": ["structural_hole", "dependency"],
    "Ritti & Levy": ["decision"],
    "Schein": ["culture_gap"],
}


def lens_highlights(kb, name, limit=4):
    """Central passages of a framework's document, used when nothing matched the wording."""
    return passages_with_role(kb, HIGHLIGHT_ROLES.get(name, []), topic=name)[:limit]


def topic_terms(analysis):
    """Topic words of the question, leaving out framework names and their parts."""
    skip = {"level", "levels", "step", "steps", "three", "eight", "model", "framework", "frameworks",
            "map", "network", "payoff", "8"}
    skip.update({"kotter", "pfeffer", "ritti", "levy", "schein"})
    return [word for word in retrieval.query_terms(analysis["search_text"]).values() if word not in skip]


def roadmap_section(analysis, max_rows=12):
    """A phased roadmap. Timings and owners are illustrative general guidance."""
    actions = collect_actions(analysis)
    if not actions:
        return None
    rows = []
    per_phase = max(2, max_rows // len(knowledge.PHASES))
    for number, phase in enumerate(knowledge.PHASES):
        in_phase = [action for action in actions if action["phase"] == number]
        # Prefer a mix of lenses within each phase: take one action per
        # framework in turn until the phase is full.
        picked, used = [], set()
        while len(picked) < per_phase and len(picked) < len(in_phase):
            for action in in_phase:
                if action in picked:
                    continue
                if action["framework"] in used and len(used) < len({a["framework"] for a in in_phase}):
                    continue
                picked.append(action)
                used.add(action["framework"])
                if len(picked) >= per_phase:
                    break
            else:
                used = set()
        for action in picked:
            rows.append([phase["name"], phase["timing"], action["text"], action["owner"], action["framework"]])
    return make_section(
        "Implementation roadmap",
        intro=(
            f"{knowledge.LABEL_TEXT[GEN]} — your documents contain no timeline or named owners for "
            "these actions, so the phases, timings and owner roles below are illustrative."
        ),
        table={"headers": ["Phase", "Illustrative timing", "Action", "Suggested owner", "Lens"], "rows": rows},
    )


def risk_items(kb, analysis, decision=None, limit=5, already_shown=()):
    """Risks: first those found in the documents, then general ones."""
    items = []
    seen = {passage["text"] for passage in (decision or [])}
    seen.update(already_shown)
    if decision:
        items.append(make_item(INF, "The losers and fence-sitters in the payoff map above are the main "
                                    "document-based risks for this decision: each is a possible source of "
                                    "resistance or delay."))
    candidates = [
        result["passage"] for result in relevant(analysis["results"], limit=10)
        if passage_role(result["passage"]) in knowledge.RISK_ROLES
    ]
    for passage in candidates:
        if passage["text"] not in seen and len(items) < limit:
            seen.add(passage["text"])
            items.append(document_item(passage))
    general = []
    for key in analysis["themes"]:
        general.extend(knowledge.THEMES[key]["risks"])
    for name in analysis["frameworks"]:
        general.extend(knowledge.FRAMEWORKS[name]["risks"])
    for entry in general[:4]:
        items.append(general_item(f"Risk: {entry['risk']} Mitigation: {entry['mitigation']}"))
    return items


def outcome_items(analysis, decision=None):
    """Expected benefits and success measures."""
    items = []
    if any(passage_role(passage) == "winner" for passage in (decision or [])):
        items.append(make_item(INF, "The gains shown in brackets beside each winner in the payoff map above are "
                                    "the benefits your notes expect. They are expectations, not results."))
    outcomes, measures = [], []
    for key in analysis["themes"]:
        outcomes.extend(knowledge.THEMES[key]["outcomes"])
        measures.extend(knowledge.THEMES[key]["measures"])
    for name in analysis["frameworks"]:
        outcomes.extend(knowledge.FRAMEWORKS[name]["outcomes"])
        measures.extend(knowledge.FRAMEWORKS[name]["measures"])
    for text in _unique(outcomes)[:3]:
        items.append(general_item("Expected outcome: " + text))
    for text in _unique(measures)[:3]:
        items.append(general_item("Suggested measure: " + text))
    return items


def _unique(values):
    result = []
    for value in values:
        if value not in result:
            result.append(value)
    return result


def gaps_section(analysis):
    """Say plainly what the documents do not cover, and what to validate."""
    items = []
    if analysis["missing_words"]:
        words = ", ".join(f"“{word}”" for word in analysis["missing_words"][:6])
        items.append(make_item("", f"These words from your question appear nowhere in the five documents: {words}. "
                                   "Anything said about them above is general guidance."))
    if analysis.get("evidence_shown"):
        pass
    elif analysis["evidence"] == "none":
        items.append(make_item("", "No passage in the five documents matched this question directly."))
    elif analysis["evidence"] == "limited":
        items.append(make_item("", "The documents touch on this only briefly, so most of the answer is general guidance."))
    items.append(general_item("Before acting, check: " + knowledge.VALIDATION_QUESTIONS[0]))
    return make_section("Limits of this answer", items)


def opening_line(analysis, description):
    name = knowledge.ADVISEE_NAME
    start = f"{name}, " if name else ""
    topics = [knowledge.THEMES[key]["label"] for key in analysis["themes"]]
    about = f" (topic: **{', '.join(topics)}**)" if topics else ""
    line = f"{start}I read this as {description}{about}."
    if analysis["follow_up"]:
        line += f" I treated it as a follow-up to your earlier question: “{analysis['previous_question']}”"
    return line


# ---------------------------------------------------------------------------
# The "Short answer" that opens every reply
# ---------------------------------------------------------------------------
# Each function returns a few items that answer the question directly, before
# any detail about frameworks. They follow the same rules as everything else:
# TMICC content is quoted, general advice is labelled as general guidance.

def _joined_quotes(passages, limit=4):
    return "; ".join(quote(passage) for passage in passages[:limit])


def _sentence_list(texts):
    """Turn ["Do a.", "Do b."] into "(1) Do a; (2) Do b." """
    parts = [f"({number}) {text.rstrip('.')}" for number, text in enumerate(texts, start=1)]
    return "; ".join(parts) + "."


def decision_summary_items(decision):
    """Who gains, who loses and who is undecided, quoted from the payoff map."""
    items = []
    groups = [("loser", "Most likely to resist (listed as losers)"),
              ("fence_sitter", "Undecided (listed as fence-sitters)"),
              ("winner", "Expected to gain (listed as winners)"),
              ("strategy", "Approach proposed in your notes")]
    for role, title in groups:
        members = [passage for passage in decision if passage_role(passage) == role]
        if members:
            items.append(make_item(DOC, f"{title}: {_joined_quotes(members)}", members[0]["file"]))
    return items


def short_answer_advice(kb, analysis):
    items = []
    themes = analysis["themes"]
    if len(themes) >= 2:
        # Several topics: one leading action for each.
        for key in themes:
            theme = knowledge.THEMES[key]
            items.append(general_item(f"{theme['label'].capitalize()}: {theme['actions'][0]['text']}"))
        return items
    for key in themes[:1]:
        items.append(general_item("In general: " + knowledge.THEMES[key]["diagnosis"]))
    top = relevant(analysis["results"], limit=1)
    if top:
        passage = top[0]["passage"]
        items.append(make_item(DOC, "Most relevant statement: " + quote(passage), documents.source_label(passage)))
    actions = [action["text"] for action in collect_actions(analysis, per_source=3)[:3]]
    if actions:
        items.append(general_item("Recommended first steps: " + _sentence_list(actions)))
    return items


def short_answer_diagnosis(kb, analysis, tensions, specific):
    items = []
    if specific:
        top = relevant(analysis["results"], limit=2)
        for result in top:
            items.append(make_item(DOC, quote(result["passage"]), documents.source_label(result["passage"])))
    elif tensions:
        labels = ", ".join("“" + tension["label"] + "”" for tension in tensions if tension["label"])
        items.append(make_item(
            DOC, f"Your context document names {len(tensions)} key tensions: {labels}. It does not rank them.",
            tensions[0]["file"]))
    for key in analysis["themes"][:1]:
        items.append(general_item("In general: " + knowledge.THEMES[key]["diagnosis"]))
    return items


def short_answer_plan(kb, analysis, decision):
    items = []
    strategy = [passage for passage in decision if passage_role(passage) == "strategy"]
    if strategy:
        items.append(make_item(DOC, "Approach proposed in your notes: " + quote(strategy[0]),
                               documents.source_label(strategy[0])))
    actions = collect_actions(analysis)
    steps = []
    for number, phase in enumerate(knowledge.PHASES):
        first = next((action for action in actions if action["phase"] == number), None)
        if first:
            steps.append(f"{phase['name'].split('. ', 1)[-1]} ({phase['timing'].lower()}): {first['text'].rstrip('.')}")
    if steps:
        items.append(general_item("The plan in outline: " + "; ".join(steps) + "."))
    return items


def short_answer_risks(kb, analysis, decision, actors):
    items = decision_summary_items(decision)
    if not items:
        items = short_answer_items(analysis, actors, [])
    general = []
    for key in analysis["themes"]:
        general.extend(knowledge.THEMES[key]["risks"])
    for name in analysis["frameworks"]:
        general.extend(knowledge.FRAMEWORKS[name]["risks"])
    if general and (decision or actors):
        items.append(general_item(f"A common risk with this kind of change: {general[0]['risk']} "
                                  f"Usual mitigation: {general[0]['mitigation']}"))
    return items


def short_answer_stakeholders(kb, analysis, decision, actors, headings):
    items = decision_summary_items(decision)
    if not items:
        items = short_answer_items(analysis, actors, [])
    if not items and headings:
        names = "; ".join("“" + heading + "”" for heading in headings)
        items.append(make_item(DOC, f"The network map lists {len(headings)} actors: {names}",
                               questions._file_for("Pfeffer")))
    return items


def short_answer_compare(chosen):
    items = [general_item("No single framework is best overall. Each answers a different question:")]
    for name in chosen:
        items.append(general_item(f"{name}: {knowledge.FRAMEWORKS[name]['key_question']}"))
    return items


def short_answer_framework_choice(chosen):
    items = []
    for name in chosen:
        framework = knowledge.FRAMEWORKS[name]
        items.append(make_item(INF, f"Use {name}. It is best suited to: {framework['best_for'].rstrip('.').lower()}."))
    return items


def with_short_answer(sections, items):
    """Put the short answer first (only if there is something to say)."""
    if items:
        return [make_section("Short answer", items)] + sections
    return sections


# ---------------------------------------------------------------------------
# One builder per question type
# ---------------------------------------------------------------------------

def build_advice(kb, analysis):
    """'How should we manage X?' - diagnosis, evidence, recommendations, risks."""
    sections = []
    themes = analysis["themes"]

    evidence = evidence_items(analysis["results"], limit=5)
    shown_texts = [result["passage"]["text"] for result in relevant(analysis["results"], limit=5)]
    if evidence and len(themes) < 2:
        sections.append(make_section("What your documents say", evidence))
    elif not evidence:
        for name in analysis["frameworks"][:2]:
            highlights = lens_highlights(kb, name)
            if highlights:
                sections.append(make_section(
                    f"Central passages in {questions._file_for(name)}",
                    [document_item(passage) for passage in highlights],
                    intro="No passage matched the wording of your question, so these are the main points this framework's document makes.",
                ))

    if len(themes) >= 2:
        # Several topics were asked about: answer topic by topic.
        for key in themes:
            theme = knowledge.THEMES[key]
            items = [general_item("Diagnosis: " + theme["diagnosis"])]
            found = retrieval.search(kb["index"], theme["search_words"], max_results=4)
            for result in relevant(found, limit=2, ratio=0.5):
                if result["score"] >= 4:
                    items.append(document_item(result["passage"]))
            for action in theme["actions"][:3]:
                items.append(general_item(action["text"], action["framework"]))
            sections.append(make_section("Managing " + theme["label"], items))
    else:
        items = []
        for key in themes:
            items.append(general_item("Diagnosis: " + knowledge.THEMES[key]["diagnosis"]))
        for action in collect_actions(analysis, per_source=3)[:6]:
            items.append(general_item(action["text"], action["framework"]))
        if not items:
            items = [general_item(text) for text in knowledge.VALIDATION_QUESTIONS]
        sections.append(make_section("Recommendations", items))

    if "plan" in analysis["extras"]:
        sections.append(roadmap_section(analysis))
    risks = risk_items(kb, analysis, already_shown=shown_texts if len(themes) < 2 else ())
    if risks:
        sections.append(make_section("Risks and mitigations", risks))
    outcomes = outcome_items(analysis)
    if outcomes:
        sections.append(make_section("Expected outcomes and success measures", outcomes))
    sections.append(framework_section(kb, analysis))
    sections.append(tension_section(kb, analysis))
    sections.append(gaps_section(analysis))
    sections = with_short_answer(sections, short_answer_advice(kb, analysis))
    return opening_line(analysis, "a request for advice"), sections


def build_diagnosis(kb, analysis):
    """'What is the main challenge?' - start from the tensions the documents name."""
    sections = []
    tensions = passages_with_role(kb, ["key_tension"])
    specific = analysis["evidence"] != "none" and analysis["has_topic"]

    if specific:
        sections.append(make_section("What your documents say about this", evidence_items(analysis["results"], limit=6)))
        sections.append(framework_section(kb, analysis))
    elif tensions:
        rows = []
        for tension in tensions:
            found_all = retrieval.search(kb["index"], tension["text"], max_results=8)
            found_all = [result for result in found_all if result["passage"]["text"] != tension["text"]]
            scores, _, _ = questions.score_frameworks(tension["text"], found_all)
            best = max(knowledge.FRAMEWORK_ORDER, key=lambda name: scores[name])
            if scores[best] >= 2:
                lens = best
            elif scores[best] >= 1:
                lens = best + " (by document match only; no routing rule matched)"
            else:
                lens = "No clear fit"
            related = ""
            if lens != "No clear fit":
                found = retrieval.search(kb["index"], tension["text"], max_results=1, topics=[best])
                if found and not found[0]["related"]:
                    related = f"{quote(found[0]['passage'])} ({found[0]['passage']['file']})"
            rows.append([quote(tension), lens, related or "—"])
        sections.append(make_section(
            "Key tensions named in your documents",
            intro=(
                f"{knowledge.LABEL_TEXT[DOC]} — the first and third columns are quoted from your files "
                f"(first column: {tensions[0]['file']}, section “{tensions[0]['section']}”). "
                f"{knowledge.LABEL_TEXT[INF]} — the middle column is the lens the routing rules suggest for each tension."
            ),
            table={"headers": ["Tension (quoted)", "Lens suggested by the rules", "Related passage in that framework's document"],
                   "rows": rows},
        ))
        analysis = dict(analysis, evidence_shown=True)
        sections.append(make_section("Which one is the main challenge?", [
            make_item("", "Your documents list these five tensions without ranking them, and a rule-based tool "
                          "cannot judge which matters most. It therefore does not name one as 'the' main challenge."),
            general_item("A common way to prioritise is to ask which tension, if left unresolved, would block "
                         "progress on the others, and which has an external deadline."),
        ]))
    else:
        sections.append(framework_section(kb, analysis))

    if "Kotter" in analysis["frameworks"]:
        step_section, steps = kotter_step_section(kb)
        if step_section:
            sections.append(step_section)
            analysis = dict(analysis, evidence_shown=True, extra_passages=steps)

    items = []
    for key in analysis["themes"]:
        items.append(general_item("Diagnosis: " + knowledge.THEMES[key]["diagnosis"]))
    lenses = analysis["frameworks"] or (knowledge.FRAMEWORK_ORDER if not specific else [])
    for name in lenses:
        items.append(general_item(knowledge.FRAMEWORKS[name]["actions"][0]["text"], name))
    if items:
        sections.append(make_section("Suggested first moves", items))

    probes = passages_with_role(kb, ["probe"])
    if probes and (not specific or "Schein" in analysis["frameworks"]):
        sections.append(make_section("Questions from your documents to test the diagnosis",
                                     [document_item(probe, with_inference=False) for probe in probes[:4]],
                                     note=knowledge.INFERENCE_RULES["probe"]))
    sections.append(tension_section(kb, analysis))
    sections.append(gaps_section(analysis))
    sections = with_short_answer(sections, short_answer_diagnosis(kb, analysis, tensions, specific))
    return opening_line(analysis, "a diagnostic question"), sections


def build_plan(kb, analysis):
    """'Build a roadmap / strategy / action plan.'"""
    sections = []
    decision = find_decision(kb, analysis)
    original_analysis = analysis

    anchors = []
    if decision:
        sections.extend(decision_sections(decision))
    else:
        anchors = evidence_items(analysis["results"], limit=6)
    if "Kotter" in analysis["frameworks"] and not analysis["themes"]:
        # A whole-programme plan: use the notes the documents hold for each Kotter step.
        step_section, steps = kotter_step_section(kb)
        if step_section:
            sections.append(step_section)
            anchors = []
            analysis = dict(analysis, evidence_shown=True, extra_passages=steps)
    if anchors:
        sections.append(make_section("Document points this plan must respect", anchors))

    sections.append(roadmap_section(analysis))

    dependencies = [
        document_item(result["passage"]) for result in relevant(analysis["results"], limit=12)
        if passage_role(result["passage"]) in ("dependency", "controls", "structural_hole")
    ][:4]
    if dependencies:
        sections.append(make_section("Dependencies named in your documents", dependencies))
    sections.append(make_section("Risks and mitigations", risk_items(kb, analysis, decision)))
    sections.append(make_section("Expected outcomes and success measures", outcome_items(analysis, decision)))
    sections.append(framework_section(kb, analysis))
    sections.append(tension_section(kb, analysis))
    sections.append(gaps_section(analysis))
    sections = with_short_answer(sections, short_answer_plan(kb, original_analysis, decision))
    return opening_line(analysis, "a request for a plan"), sections


def build_risk_benefit(kb, analysis):
    """'What are the risks, stakeholder implications and benefits of X?'"""
    sections = []
    decision = find_decision(kb, analysis)
    actors = find_actors(kb, analysis)

    if decision:
        sections.extend(decision_sections(decision))
    elif not actors:
        headings = passages_with_role(kb, ["decision"])
        items = [make_item("", "You have not named a specific intervention that I can match, so document-based "
                               "winners and losers cannot be given. Your documents analyse these decisions; "
                               "ask about one of them for a document-based answer:")]
        items += [make_item(DOC, quote(heading), heading["file"]) for heading in headings]
        sections.append(make_section("Which intervention?", items))

    risk_section = make_section("Risks and mitigations", risk_items(kb, analysis, decision, limit=6))
    if not decision and not actors:
        risk_section["intro"] = ("No intervention was named, so any document passages below are simply "
                                 "those that match the words in your question, not risks of a specific action.")
    sections.append(risk_section)

    stakeholder_items = []
    for heading, block in actors[:3]:
        children = [document_item(passage) for passage in block[:4]]
        stakeholder_items.append(make_item("", f"**{heading}**", block[0]["file"], children))
    if stakeholder_items:
        sections.append(make_section("Stakeholder implications (from the network map)", stakeholder_items))
    elif not decision:
        sections.append(make_section("Stakeholder implications", [
            general_item("For any intervention, list who gains, who loses and who is undecided, then decide the order of engagement.", "Ritti & Levy"),
            general_item("Check which actors control resources the intervention needs, and whether a direct relationship exists with each.", "Pfeffer"),
        ]))

    sections.append(make_section("Expected benefits and success measures", outcome_items(analysis, decision)))
    sections.append(framework_section(kb, analysis))
    sections.append(tension_section(kb, analysis))
    sections.append(gaps_section(analysis))
    sections = with_short_answer(sections, short_answer_risks(kb, analysis, decision, actors))
    return opening_line(analysis, "a question about risks, stakeholder implications and benefits"), sections


def build_stakeholder(kb, analysis):
    """'Who wins, who loses, who has power?'"""
    sections = []
    decision = find_decision(kb, analysis)
    actors = find_actors(kb, analysis)
    sections.extend(decision_sections(decision))
    all_headings = []

    for heading, block in actors[:4]:
        sections.append(make_section(f"Network map: {heading}", [document_item(passage) for passage in block]))

    if not decision and not actors:
        headings = _unique([passage["heading"] for passage in kb["passages"]
                            if passage["topic"] == "Pfeffer" and passage["heading"]
                            and not passage["heading"].upper().startswith("BROKERAGE")])
        all_headings = headings
        if headings:
            sections.append(make_section(
                "Actors in your network map",
                [make_item(DOC, "“" + heading + "”", questions._file_for("Pfeffer")) for heading in headings],
                intro="Your question did not name a specific actor or decision, so here is everyone the network map lists. Ask about any of them for detail.",
            ))
        strong = [result for result in relevant(analysis["results"], limit=5) if result["score"] >= 4]
        if len(strong) >= 2:
            sections.append(make_section("Other passages matching your question",
                                         [document_item(result["passage"]) for result in strong]))

    brokerage = passages_with_role(kb, ["brokerage"])
    if brokerage and ("Pfeffer" in analysis["frameworks"] or actors):
        sections.append(make_section("Brokerage opportunities listed in your documents",
                                     [document_item(passage, with_inference=False) for passage in brokerage],
                                     note=knowledge.INFERENCE_RULES["brokerage"]))
    sections.append(framework_section(kb, analysis))
    actions = [general_item(action["text"], action["framework"]) for action in collect_actions(analysis, per_source=3)[:5]]
    if actions:
        sections.append(make_section("Recommended actions", actions))
    sections.append(tension_section(kb, analysis))
    sections.append(gaps_section(analysis))
    sections = with_short_answer(
        sections, short_answer_stakeholders(kb, analysis, decision, actors, all_headings))
    return opening_line(analysis, "a question about stakeholders, power and political support"), sections


def build_compare(kb, analysis):
    """'Compare the frameworks.'"""
    chosen = analysis["frameworks"]
    rows = []
    for name in chosen:
        framework = knowledge.FRAMEWORKS[name]
        count = len([passage for passage in kb["passages"] if passage["topic"] == name])
        rows.append([name, framework["focus"], framework["key_question"], framework["best_for"],
                     framework["limitations"][0], f"{questions._file_for(name)} ({count} passages)"])
    sections = [make_section(
        "Side-by-side comparison",
        intro=f"{knowledge.LABEL_TEXT[GEN]} — framework descriptions are general knowledge; the last column shows which of your files applies each framework to TMICC.",
        table={"headers": ["Framework", "Focus", "Key question", "Best used when", "Main limitation", "In your documents"],
               "rows": rows},
    )]

    # If the question also names a topic, show how each framework's document treats it.
    terms = topic_terms(analysis)
    if terms:
        items = []
        for name in chosen:
            found = retrieval.search(kb["index"], " ".join(terms), max_results=2, topics=[name])
            found = [result for result in found if not result["related"]]
            if found:
                items.append(make_item("", f"**{name}**", "", [document_item(result["passage"]) for result in found]))
            else:
                items.append(make_item("", f"**{name}** — its document has no passage matching “{' '.join(terms)}”."))
        sections.append(make_section("How each framework's document treats your topic", items))

    if len(chosen) == len(knowledge.FRAMEWORK_ORDER):
        sections.append(make_section("How they complement each other", [
            general_item("Kotter gives the sequence of a change; the other three explain why a step may fail."),
            general_item("Pfeffer shows the lasting structure of power and dependence; Ritti & Levy apply political analysis to one decision at a time."),
            general_item("Schein explains resistance that persists even when interests are satisfied, because it rests on beliefs."),
        ]))
    tensions = tension_section(kb, dict(analysis, results=[]))
    if tensions:
        tensions["items"] = tensions["items"][:6]
        sections.append(tensions)
    sections.append(make_section("Limits of this answer", [
        make_item("", "This comparison uses general descriptions built into the app. Your documents apply each "
                      "framework to TMICC but do not compare the frameworks with each other."),
    ]))
    sections = with_short_answer(sections, short_answer_compare(chosen))
    return opening_line(analysis, "a request to compare frameworks"), sections


def build_framework_choice(kb, analysis):
    """'Which framework fits, and why?'"""
    chosen = analysis["frameworks"]
    sections = []
    if not chosen:
        rows = [[name, knowledge.FRAMEWORKS[name]["best_for"], knowledge.FRAMEWORKS[name]["key_question"],
                 ", ".join(knowledge.FRAMEWORKS[name]["triggers"][:6])] for name in knowledge.FRAMEWORK_ORDER]
        sections.append(make_section(
            "It depends on the challenge",
            intro=(f"{knowledge.LABEL_TEXT[GEN]} — no specific challenge was named, so no single framework can be "
                   "recommended. Use this guide, or describe the challenge and ask again."),
            table={"headers": ["Framework", "Best used when", "Key question it answers", "Typical topics"], "rows": rows},
        ))
        return opening_line(analysis, "a question about which framework to use"), sections

    rows = []
    for name in knowledge.FRAMEWORK_ORDER:
        score = round(analysis["framework_scores"][name], 1)
        reasons = "; ".join(analysis["framework_reasons"][name]) or "no rule matched"
        rows.append([name, str(score), "Selected" if name in chosen else "Not selected", reasons])
    sections.append(make_section(
        "Recommended: " + " and ".join(chosen),
        intro=(f"{knowledge.LABEL_TEXT[INF]} — the choice comes from routing rules (topics each framework is suited to) "
               "and from where matching passages were found. The scores are a transparent heuristic, not a measurement."),
        table={"headers": ["Framework", "Rule score", "Result", "Why"], "rows": rows},
    ))
    items = []
    for name in chosen:
        framework = knowledge.FRAMEWORKS[name]
        items.append(general_item(f"{name} is best used for: {framework['best_for']} {framework['not_for']}"))
    sections.append(make_section("Why this fits, and what it will not cover", items))

    decision = find_decision(kb, analysis) if "Ritti & Levy" in chosen else []
    if decision:
        sections.extend(decision_sections(decision))
    else:
        evidence = [document_item(result["passage"]) for result in relevant(analysis["results"], limit=10)
                    if result["passage"]["topic"] in chosen + ["TMICC context"]][:5]
        if evidence:
            sections.append(make_section("Supporting passages", evidence))
    first_moves = [general_item(knowledge.FRAMEWORKS[name]["actions"][0]["text"], name) for name in chosen]
    sections.append(make_section("What this framework would have you do first", first_moves))
    sections.append(tension_section(kb, analysis))
    sections.append(gaps_section(analysis))
    sections = with_short_answer(sections, short_answer_framework_choice(chosen))
    return opening_line(analysis, "a question about which framework to use"), sections


def build_explain_framework(kb, analysis):
    """'Explain Schein's three levels.'"""
    sections = []
    for name in analysis["named_frameworks"] or analysis["frameworks"]:
        framework = knowledge.FRAMEWORKS[name]
        items = [general_item(framework["summary"])]
        items += [general_item(f"{title}: {meaning}") for title, meaning in framework["concepts"]]
        items.append(general_item("Best used for: " + framework["best_for"]))
        items.append(general_item("Limitation: " + framework["limitations"][0]))
        sections.append(make_section(framework["title"], items))

        terms = topic_terms(analysis)
        chosen = []
        if terms:
            found = retrieval.search(kb["index"], " ".join(terms), max_results=6, topics=[name])
            chosen = [result["passage"] for result in found if not result["related"]]
        if name == "Kotter" and not chosen:
            step_section, _ = kotter_step_section(kb)
            if step_section:
                sections.append(step_section)
                continue
        if not chosen:  # nothing specific asked: show the document's central points
            chosen = lens_highlights(kb, name, limit=6)
        sections.append(make_section(f"How your documents apply it ({questions._file_for(name)})",
                                     [document_item(passage) for passage in chosen[:6]]))
    return opening_line(analysis, "a request to explain a framework"), sections


# Words in a factual question, and the kind of passage that answers them.
FACT_ASPECTS = [
    (r"\b(want|wants|wanted|aim|aims|goal|goals|interest|interests|incentive|after|looking for)\b",
     ["interest"], "What they want"),
    (r"\b(control|controls|power|influence|leverage|hold|holds)\b",
     ["controls", "power_base"], "What they control"),
    (r"\b(depend|depends|dependent|dependency|dependencies|rely|relies|need|needs)\b",
     ["dependency"], "Dependencies"),
    (r"\b(risk|risks|danger|threat|gap|gaps|missing|hole)\b",
     ["risk", "structural_hole"], "Risks and gaps"),
]


def _after_label(passage):
    """Return the text after a leading label: "Wants: margin ..." -> "margin ..."."""
    text = passage["text"]
    if passage["label"] and text.startswith(passage["label"] + ":"):
        return text[len(passage["label"]) + 1:].strip()
    return text


def short_answer_items(analysis, actors, results):
    """A direct answer at the top of a factual reply, made only of quotations.

    For a named actor it states how the documents describe them and, if the
    question asks what they want, control, depend on or risk, quotes that
    line. Otherwise it quotes the single closest passage.
    """
    question = analysis["question"].lower()
    items = []
    for heading, block in actors[:2]:
        source = block[0]["file"]
        items.append(make_item(DOC, f"Listed in the network map as “{heading}”", source))
        for pattern, roles, title in FACT_ASPECTS:
            if not re.search(pattern, question):
                continue
            for passage in block:
                if passage_role(passage) in roles:
                    items.append(make_item(DOC, f"{title}: “{_after_label(passage)}”",
                                           documents.source_label(passage)))
    if not items and results:
        best = results[0]["passage"]
        # A "when" or "how many" question is best answered by a passage with a number in it.
        if re.search(r"^\s*(when|what year|what date|how many|how much|how long)\b", question):
            dated = [result["passage"] for result in results if re.search(r"\d", result["passage"]["text"])]
            if dated:
                best = dated[0]
        items.append(make_item(DOC, "Closest statement: " + quote(best), documents.source_label(best)))
    return items


def build_fact(kb, analysis):
    """'Who is ...?', 'When was ...?' - answered from the documents only."""
    sections = []
    results = relevant(analysis["results"], limit=7, ratio=0.5)
    has_figure = any(re.search(r"\d", result["passage"]["text"]) for result in results)
    actors = find_actors(kb, analysis)

    if analysis["evidence"] == "none" or not results:
        items = [make_item("", "The five documents do not contain an answer to this question, and this tool "
                               "does not look anything up elsewhere, so I cannot answer it.")]
        if questions.uses_change_vocabulary(analysis["question"]):
            items.append(general_item(
                "In general terms, change management is the structured work of moving people and an "
                "organisation from a current way of working to a new one. This app looks at it through four lenses: "
                + "; ".join(f"{name} ({knowledge.FRAMEWORKS[name]['focus'].rstrip('.').lower()})"
                            for name in knowledge.FRAMEWORK_ORDER) + "."
            ))
        sections.append(make_section("Not covered by your documents", items))
        return opening_line(analysis, "a factual question"), sections

    if analysis["asks_for_figures"] and not has_figure:
        sections.append(make_section("No figures in your documents", [
            make_item("", "You asked for a figure. The passages that match your words contain no numbers, "
                          "so the documents do not appear to give it. I will not estimate one."),
        ]))
        closest = [document_item(result["passage"], with_inference=False) for result in results[:3]]
        sections.append(make_section("Closest passages (they do not answer the question)", closest))
        return opening_line(analysis, "a factual question"), sections

    short = short_answer_items(analysis, actors, results)
    if short:
        sections.append(make_section("Short answer", short))

    shown = set()
    for heading, block in actors[:2]:
        sections.append(make_section(f"From the network map: {heading}",
                                     [document_item(passage, with_inference=False) for passage in block]))
        shown.update(passage["text"] for passage in block)
    others = [document_item(result["passage"], with_inference=False) for result in results
              if result["passage"]["text"] not in shown]
    if others:
        title = "Elsewhere in your documents" if actors else "What your documents say"
        sections.append(make_section(title, others[:6]))
    sections.append(make_section("Limits of this answer", [
        make_item("", "These are the passages that match the words in your question. The app cannot judge "
                      "whether they answer it completely, and the documents have not been checked against outside sources."),
    ]))
    return opening_line(analysis, "a factual question"), sections


def build_greeting(kb, analysis):
    examples = [make_item("", f"“{text}”") for text in knowledge.EXAMPLE_QUESTIONS]
    sections = [
        make_section("What I can do", [
            make_item("", "Answer questions about the change challenges described in your five documents."),
            make_item("", "Suggest which of the four frameworks fits a question, and explain why."),
            make_item("", "Draft recommendations, roadmaps, risks and success measures, each labelled by source."),
        ]),
        make_section("Questions you could ask", examples),
    ]
    name = knowledge.ADVISEE_NAME
    return (f"Hello{' ' + name if name else ''}. I am a rule-based change management consultant for TMICC."), sections


def build_about_tool(kb, analysis):
    sections = [make_section("What this tool is", [
        make_item("", "This is a rule-based tool, not an AI model. It matches the words in your question against "
                      "rules and against five Word documents, then assembles an answer from quoted passages and "
                      "built-in general guidance."),
        make_item("", "It uses no external AI service, no API key and no internet access."),
        make_item("", "It cannot understand a question the way a person or a large language model can, "
                      "so always review its output before relying on it."),
    ])]
    return "I am not an AI model.", sections


def build_out_of_scope(kb, analysis):
    examples = [make_item("", f"“{text}”") for text in knowledge.EXAMPLE_QUESTIONS[:4]]
    sections = [
        make_section("Outside what this tool covers", [
            make_item("", "I could not connect this question to change management or to anything in the five "
                          "TMICC documents, so I will not attempt an answer."),
            make_item("", "This tool covers the TMICC separation and four change-management frameworks: "
                          "Kotter, Pfeffer, Ritti & Levy and Schein."),
        ]),
        make_section("Questions I can help with", examples),
    ]
    return "This question is outside my scope.", sections


BUILDERS = {
    "advice": build_advice,
    "diagnose": build_diagnosis,
    "plan": build_plan,
    "risk_benefit": build_risk_benefit,
    "stakeholder": build_stakeholder,
    "compare": build_compare,
    "framework_choice": build_framework_choice,
    "explain_framework": build_explain_framework,
    "fact": build_fact,
    "greeting": build_greeting,
    "about_tool": build_about_tool,
    "out_of_scope": build_out_of_scope,
}

# Question types whose answers include a source-label legend at the end.
TYPES_WITH_LEGEND = {"advice", "diagnose", "plan", "risk_benefit", "stakeholder", "compare",
                     "framework_choice", "explain_framework", "fact"}


# ---------------------------------------------------------------------------
# Main entry point and rendering
# ---------------------------------------------------------------------------

def answer_question(question, kb, previous=None):
    """Answer one question.

    `previous` is the "analysis" of the last answer in the conversation, so a
    follow-up such as "what are the risks of that?" keeps its topic.
    Returns a dictionary with the opening line, sections, markdown text and
    the analysis (store the analysis and pass it back in as `previous`).
    """
    analysis = questions.analyse(question, kb["index"], previous)
    analysis["decision"] = []
    if analysis["type"] in ("advice", "plan", "risk_benefit", "stakeholder", "framework_choice"):
        analysis["decision"] = match_decision(kb, analysis)
        if analysis["decision"] and "Ritti & Levy" not in analysis["frameworks"]:
            # The documents analyse this as a decision with winners and losers,
            # so the Ritti & Levy lens is being used and must be declared.
            analysis["frameworks"] = analysis["frameworks"] + ["Ritti & Levy"]
            analysis["framework_reasons"]["Ritti & Levy"].append(
                "your documents analyse this as a decision with winners and losers (RITTI.docx)")
    builder = BUILDERS.get(analysis["type"], build_advice)
    opening, sections = builder(kb, analysis)
    sections = [section for section in sections if section and (section["items"] or section["table"])]
    answer = {
        "question": question,
        "type": analysis["type"],
        "frameworks": analysis["frameworks"],
        "opening": opening,
        "sections": sections,
        "analysis": analysis,
        "show_legend": analysis["type"] in TYPES_WITH_LEGEND,
    }
    answer["markdown"] = render_markdown(answer)                          # with source labels
    answer["plain_markdown"] = render_markdown(answer, show_sources=False)  # clean reading view
    return answer


def _without_quote_marks(text):
    return str(text).replace("“", "").replace("”", "")


def _render_item(item, indent=0, seen=None, show_sources=True):
    """Render one item (and its children) as Markdown bullet lines.

    `seen` collects inference texts already shown in the section, so the same
    explanation is not printed under every bullet.
    With show_sources=False the source label, quotation marks and file
    reference are left out, so the answer reads as plain statements.
    """
    seen = seen if seen is not None else set()
    if item["label"] == INF:
        if item["text"] in seen:
            return []
        seen.add(item["text"])
    prefix = "  " * indent + "- "
    if show_sources:
        label = knowledge.LABEL_TEXT.get(item["label"], "")
        text = f"{label} — {item['text']}" if label else item["text"]
        if item["source"]:
            text += f" *({item['source']})*"
    else:
        text = _without_quote_marks(item["text"])
        # "1. Cultural: ..." would otherwise turn into a nested numbered list.
        text = re.sub(r"^(\d+)\.", r"\1\\.", text)
        # Keep the framework name beside general advice, but not file references.
        if item["source"] and item["label"] == GEN:
            text += f" *({item['source']})*"
    lines = [prefix + text]
    for child in item["children"]:
        lines.extend(_render_item(child, indent + 1, seen, show_sources))
    return lines


def _render_table(table, show_sources=True):
    def clean(cell):
        text = str(cell).replace("|", "/").replace("\n", " ")
        return text if show_sources else _without_quote_marks(text)
    lines = ["| " + " | ".join(table["headers"]) + " |",
             "|" + "|".join(["---"] * len(table["headers"])) + "|"]
    for row in table["rows"]:
        lines.append("| " + " | ".join(clean(cell) for cell in row) + " |")
    return lines


def render_markdown(answer, show_sources=True):
    """Turn an answer into Markdown text for the chat window or a download.

    show_sources=True  - every statement carries its source label
                         (document / inference / general guidance).
    show_sources=False - a clean reading view without labels or file names.
    """
    label_marks = tuple(knowledge.LABEL_TEXT.values())
    lines = [answer["opening"], ""]
    for section in answer["sections"]:
        lines.append(f"#### {section['title']}")
        intro = section["intro"]
        if intro and not show_sources and intro.startswith(label_marks):
            intro = ""  # this introduction only explains the labels
        if intro:
            lines.extend([intro, ""])
        if section["table"]:
            lines.extend(_render_table(section["table"], show_sources))
            lines.append("")
        seen_inferences = set()
        for item in section["items"]:
            lines.extend(_render_item(item, 0, seen_inferences, show_sources))
        if section["note"]:
            if show_sources:
                lines.extend(["", f"{knowledge.LABEL_TEXT[INF]} — {section['note']}"])
            else:
                lines.extend(["", section["note"]])
        lines.append("")
    if answer["show_legend"] and show_sources:
        lines.extend(["---", knowledge.LEGEND])
    return "\n".join(lines).strip()


def conversation_to_markdown(history):
    """Turn the whole conversation into one Markdown document for download.

    `history` is a list of {"question": ..., "markdown": ...} dictionaries.
    """
    parts = ["# TMICC Change Management Consultant - conversation", "",
             "_Rule-based output. No AI model was used. Review before relying on it._", ""]
    for number, turn in enumerate(history, start=1):
        parts.extend([f"## Question {number}: {turn['question']}", "", turn["markdown"], ""])
    return "\n".join(parts)
