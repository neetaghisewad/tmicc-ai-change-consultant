"""Search the document passages for text relevant to a question.

This is a keyword search, not an AI model. It works in four small steps:

1. clean_text()   - lower-case the text and replace known aliases
                    (for example "TSA" -> "transitional service agreement").
2. tokenize()     - split into words, drop filler words, and cut word endings
                    so "stakeholders" matches "stakeholder" and "cultural"
                    matches "culture".
3. expand_query() - add closely related words (for example "staff" for
                    "employee") with a lower weight.
4. search()       - score every passage with the BM25 formula, a standard
                    search-engine calculation that rewards rare words more
                    than common ones.
"""

import math
import re

# ---------------------------------------------------------------------------
# Word lists
# ---------------------------------------------------------------------------

# Filler words that carry no topic information.
STOPWORDS = set("""
a an the and or but if then than so of to in on at by for from with without into onto over under
about as is are was were be been being am do does did doing have has had having will would shall
should can could may might must i me my we us our you your he him his she her it its they them
their this that these those there here what which who whom whose when where why how not no nor
only very too also just more most less least some any each every all both either neither such
own same other another again further once during before after above below between through up
down out off while because until against per via etc please tell give show let want need like
get got make made one two
""".split())

# Everyday "question words". They describe what the user wants done, not the
# topic, so they are left out of the search ("manage", "main", "challenge").
GENERIC_QUESTION_WORDS = set("""
manage managed managing handle handled handling deal dealing address addressing improve improving
improved main biggest key major important facing face faced challenge challenges issue issues
problem problems change changes changing management best better good right appropriate suitable
recommend recommended recommendation recommendations suggest suggested advice advise approach
approaches way ways thing things use used using apply applied applying work works working help
helps explain describe discuss consider think about question answer particular specific proposed
overall general current currently new different likely possible effectively effective successful
successfully company organisation organization organisational organizational business develop
developing create creating build building ensure during expected implications implication
intervention interventions measure measures happen happens look looks mean means say says said
know going go take taken first next why how compare comparison fit fits suit suits
roadmap implementation implement implementing plan plans action actions timeline exit exiting
stand stands ai hello hi strategy strategies programme programmes program project
""".split())

# Every document is about TMICC, so the name itself does not help to tell
# passages apart and is left out of the search.
GENERIC_QUESTION_WORDS.add("tmicc")

# Words whose normal stem would wrongly match a different word.
STEM_EXCEPTIONS = {
    "government": "government", "governments": "government",
    "former": "former", "formal": "formal",
    "employment": "employment",
}

# Aliases: different ways of writing the same thing. Every alias below is
# either ordinary English or a name/abbreviation used in the five documents.
# Format: (pattern to find, text to use instead).
ALIASES = [
    (r"ben\s*(?:&|and|n)\s*jerry(?:'s|s)?", "benjerrys"),
    (r"\bb\s*&\s*j(?:'s)?\b", "benjerrys"),
    (r"\btsas?\b", "transitional service agreement"),
    (r"\btransitional services?\b", "transitional service"),
    (r"\bspin[\s-]?offs?\b|\bspun[\s-]off\b|\bde-?mergers?\b", "separation"),
    (r"\bstand[\s-]alone\b", "standalone"),
    (r"\bwall'?s\b", "walls"),
    (r"\bthe magnum ice cream company\b|\bmagnum ice cream company\b", "tmicc"),
    (r"\bp\s*&\s*l\b", "profit"),
    (r"\bhq\b", "headquarters"),
    (r"\bhuman resources\b", "hr"),
    (r"\binformation technology\b", "infotech"),
    (r"\bfence[\s-]?sitters?\b", "fencesitter"),
    (r"\bshort[\s-]term\b", "shortterm"),
    (r"\bquick wins?\b", "shortterm win"),
    (r"\bdecision[\s-]making\b", "decision making"),
    (r"\bstands? for\b", "identity values"),
]

# Groups of closely related words. If a question uses one of them, the others
# are also searched for, at a lower weight. These are general-language links,
# not facts about TMICC.
RELATED_WORD_GROUPS = [
    ["employee", "staff", "workforce", "people", "team", "worker", "colleague", "manager"],
    ["resistance", "resist", "opposition", "pushback", "reluctance", "loser", "disruption", "dissent"],
    ["investor", "shareholder", "activist"],
    ["culture", "cultural", "value", "assumption", "dna", "identity", "norm", "belief", "artefact", "mindset"],
    ["power", "influence", "control", "dependency", "leverage", "authority"],
    ["politics", "political", "winner", "loser", "fencesitter", "payoff", "coalition"],
    ["risk", "threat", "tension", "dispute", "litigation", "uncertainty", "lawsuit"],
    ["benefit", "gain", "advantage", "winner", "outcome"],
    ["stakeholder", "actor", "partner", "board", "investor", "retailer", "government", "ngo"],
    ["communication", "communicate", "message", "narrative", "vocabulary", "language", "statement"],
    ["leadership", "leader", "ceo", "chair", "cfo", "board"],
    ["urgency", "urgent", "quickly", "fast", "pressure", "momentum"],
    ["independence", "independent", "standalone", "autonomy"],
    ["governance", "govern", "authority", "board"],
    ["system", "infotech", "technology", "service"],
    ["engagement", "empowerment", "involvement", "morale", "motivation"],
    ["relationship", "network", "alliance", "brokerage", "bridge"],
    ["sequence", "step", "timeline", "roadmap", "phase"],
    ["agile", "agility", "speed", "bureaucratic", "bureaucracy", "process"],
    ["conflict", "clash", "dispute", "tension"],
    ["mission", "purpose", "activism", "social"],
    ["customer", "retailer", "retail", "consumer"],
]

# Word endings removed by stem(), longest first.
SUFFIXES = [
    "isations", "izations", "isation", "ization", "encies", "ations", "ments",
    "ising", "izing", "ised", "ized",
    "ation", "ities", "ships", "ency", "ence", "ance", "ment", "ness", "ship",
    "ings", "ally", "ity", "ies", "ing", "ise", "ize", "ent", "ers", "ors",
    "ed", "es", "er", "or", "al", "ly", "s",
]

RELATED_WEIGHT = 0.4   # weight of a related word compared with an exact word
HEADING_WEIGHT = 0.5   # weight of a word found in the passage's heading
MIN_SCORE = 1.0        # passages scoring below this are ignored


# ---------------------------------------------------------------------------
# Step 1 and 2: cleaning, splitting and stemming
# ---------------------------------------------------------------------------

def clean_text(text):
    """Lower-case the text and apply the alias list."""
    text = str(text or "")
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    # "IT" in capitals means information technology; "it" is just a pronoun.
    text = re.sub(r"\bIT\b", "infotech", text)
    text = text.lower()
    for pattern, replacement in ALIASES:
        text = re.sub(pattern, replacement, text)
    text = re.sub(r"'s\b", "", text)  # possessives: "unilever's" -> "unilever"
    return text


def stem(word):
    """Cut common endings so related word forms match.

    "stakeholders" -> "stakeholder", "cultural" -> "cultur", "culture" -> "cultur".
    The result does not need to be a real word; it only needs to be the same
    for related forms.
    """
    if word in STEM_EXCEPTIONS:
        return STEM_EXCEPTIONS[word]
    for _ in range(2):  # two passes: "leaderships" -> "leadership" -> "leader"
        changed = False
        for suffix in SUFFIXES:
            if word.endswith(suffix) and len(word) - len(suffix) >= 4:
                word = word[: -len(suffix)]
                changed = True
                break
        if not changed:
            break
    while word.endswith("e") and len(word) > 4:  # "culture" -> "cultur", "employee" -> "employ"
        word = word[:-1]
    return word


def tokenize(text, keep_original=False):
    """Split text into stemmed search words.

    With keep_original=True the result is a list of (stem, original_word).
    """
    words = re.findall(r"[a-zà-ÿ0-9]+", clean_text(text))
    result = []
    for word in words:
        if word in STOPWORDS or (len(word) < 2 and not word.isdigit()):
            continue
        result.append((stem(word), word) if keep_original else stem(word))
    return result


# ---------------------------------------------------------------------------
# Step 3: related words
# ---------------------------------------------------------------------------

def _build_related_lookup():
    lookup = {}
    for group in RELATED_WORD_GROUPS:
        stems = {stem(word) for word in group}
        for item in stems:
            lookup.setdefault(item, set()).update(stems - {item})
    return lookup


RELATED_LOOKUP = _build_related_lookup()


def expand_query(query_stems):
    """Return {stem: weight}. Exact words weigh 1.0, related words less."""
    weights = {}
    for item in query_stems:
        weights[item] = 1.0
    for item in query_stems:
        for related in RELATED_LOOKUP.get(item, ()):
            weights.setdefault(related, RELATED_WEIGHT)
    return weights


# ---------------------------------------------------------------------------
# Step 4: the search index and BM25 scoring
# ---------------------------------------------------------------------------

def build_index(passages):
    """Prepare the passages for searching.

    Each passage is indexed on its own text plus its headings and framework
    name, so a bullet under "TRIAN PARTNERS" can be found by asking about
    Trian even though the bullet itself does not repeat the name.
    """
    entries = []
    document_frequency = {}
    for passage in passages:
        stems = tokenize(passage["text"])
        heading_stems = tokenize(passage["section"] + " " + passage["topic"])
        counts = {}
        for item in stems:
            counts[item] = counts.get(item, 0) + 1
        for item in set(heading_stems):
            # A word found only in the heading counts for less than a word
            # in the passage itself.
            counts[item] = counts.get(item, 0) + HEADING_WEIGHT
        for item in counts:
            document_frequency[item] = document_frequency.get(item, 0) + 1
        entries.append({"passage": passage, "counts": counts, "length": len(stems)})

    total = len(entries)
    average_length = sum(entry["length"] for entry in entries) / total if total else 0
    # Rare words get a high weight (idf), common words a low one.
    idf = {
        item: math.log(1 + (total - frequency + 0.5) / (frequency + 0.5))
        for item, frequency in document_frequency.items()
    }
    return {"entries": entries, "idf": idf, "average_length": average_length, "total": total}


def query_terms(query):
    """Return {stem: original_word} for the topic words of a question."""
    terms = {}
    for item, original in tokenize(query, keep_original=True):
        if original in GENERIC_QUESTION_WORDS:
            continue
        terms.setdefault(item, original)
    return terms


def search(index, query, max_results=8, topics=None):
    """Return the passages most relevant to the query.

    Each result is a dictionary:
        passage  - the passage found
        score    - relevance score (higher is more relevant)
        matched  - words from the question found in the passage
        related  - True if it was found only through related words
    `topics` can limit the search to certain documents, e.g. ["Schein"].
    """
    original_for = query_terms(query)
    weights = expand_query(list(original_for))

    k1, b = 1.4, 0.6  # standard BM25 settings
    results = []
    for entry in index["entries"]:
        passage = entry["passage"]
        if topics and passage["topic"] not in topics:
            continue
        score = 0.0
        matched = []
        exact_hit = False
        for item, weight in weights.items():
            frequency = entry["counts"].get(item, 0)
            if not frequency:
                continue
            length_factor = 1 - b + b * entry["length"] / (index["average_length"] or 1)
            term_score = index["idf"].get(item, 0) * frequency * (k1 + 1) / (frequency + k1 * length_factor)
            score += weight * term_score
            if weight == 1.0:
                exact_hit = True
                matched.append(original_for[item])
        if score >= MIN_SCORE:
            results.append({
                "passage": passage, "score": round(score, 2),
                "matched": matched, "related": not exact_hit,
            })
    results.sort(key=lambda result: result["score"], reverse=True)
    return results[:max_results]


def words_not_in_documents(index, query):
    """Return topic words from the question that appear nowhere in the documents.

    This is used to tell the user honestly when the documents do not mention
    something they asked about.
    """
    missing = []
    for item, original in query_terms(query).items():
        if item in index["idf"] or original.isdigit():
            continue
        if original not in missing:
            missing.append(original)
    return missing


def distinctive_matches(index, results, minimum_idf=2.0):
    """Count distinct question words matched that are reasonably rare.

    Matching only very common words ("tmicc", "unilever") is weak evidence;
    matching a rarer word ("litigation", "retailers") is stronger.
    """
    found = set()
    for result in results:
        for word in result["matched"]:
            if index["idf"].get(stem(word), 0) >= minimum_idf:
                found.add(stem(word))
    return len(found)
