"""Read the five Word documents and rebuild them into labelled passages.

Why this file exists
--------------------
The Word documents are "hard-wrapped": every visual line is stored as its own
paragraph, so one sentence is often spread over two or three paragraphs.
Searching those raw lines returns fragments such as "standalone viability
quickly." with no hint of where they came from.

This file therefore:
1. reads the raw lines from each .docx (using only Python's built-in libraries);
2. joins wrapped lines back into whole statements ("passages");
3. remembers which heading each passage sits under, for example
   "DECISION 2: Renegotiate transitional service agreements ... > LOSERS".

The text of the documents is never changed or added to - only regrouped.
"""

import os
import re
import zipfile
import xml.etree.ElementTree as ET

# Folder that contains app.py and the five Word documents (one level above
# this file).
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Keep these five Word documents in the SAME GitHub folder as app.py.
KNOWLEDGE_DOCUMENTS = [
    {"file": "KOTTER 8.docx", "topic": "Kotter"},
    {"file": "PFEFFER NETWORK MAP.docx", "topic": "Pfeffer"},
    {"file": "RITTI.docx", "topic": "Ritti & Levy"},
    {"file": "SCHEIN THREE.docx", "topic": "Schein"},
    {"file": "TMICC ORCHESTRATOR CONTEXT DOCUMENT.docx", "topic": "TMICC context"},
]

WORD_NAMESPACE = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

# Patterns used to recognise the role of each line.
BULLET_PATTERN = re.compile(r"^[-•*]\s+(.*)$")              # "- Role: CEO"
NUMBERED_PATTERN = re.compile(r"^(\d+)[.)]\s+(.*)$")         # "1. Cultural: ..."
LABEL_PATTERN = re.compile(r"^([A-Z][^:.!?]{0,70}):\s*(.*)$")  # "Step 1 - Urgency: ..."
SEPARATOR_PATTERN = re.compile(r"^[-–—_\s]{3,}$")           # "---"


def normalise(text):
    """Collapse repeated spaces and trim the ends."""
    return re.sub(r"\s+", " ", str(text or "")).strip()


# ---------------------------------------------------------------------------
# Step 1: read raw lines from a .docx file
# ---------------------------------------------------------------------------

def resolve_path(file_name):
    """Return the full path of a document stored beside app.py."""
    if os.path.isabs(file_name):
        return file_name
    return os.path.join(BASE_DIR, file_name)


def read_docx_lines(path):
    """Return (list_of_lines, error_message) for one .docx file.

    A .docx file is a zip archive; the text lives in word/document.xml.
    """
    try:
        with zipfile.ZipFile(resolve_path(path), "r") as archive:
            xml_bytes = archive.read("word/document.xml")
        root = ET.fromstring(xml_bytes)
        lines = []
        for paragraph in root.findall(".//w:p", WORD_NAMESPACE):
            parts = [node.text or "" for node in paragraph.findall(".//w:t", WORD_NAMESPACE)]
            line = normalise("".join(parts))
            if line:
                lines.append(line)
        return lines, None
    except FileNotFoundError:
        return [], "File not found in the same folder as app.py."
    except (zipfile.BadZipFile, KeyError, ET.ParseError, OSError) as exc:
        return [], f"Could not read this Word file: {exc}"


def extract_docx_text(path):
    """Return (text, error_message). Kept so older code keeps working."""
    lines, error = read_docx_lines(path)
    return "\n".join(lines), error


# ---------------------------------------------------------------------------
# Step 2: rebuild lines into passages with section labels
# ---------------------------------------------------------------------------

def _without_brackets(text):
    """Remove "(...)" parts, e.g. "PETER TER KULVE (user)" -> "PETER TER KULVE"."""
    return normalise(re.sub(r"\([^)]*\)", " ", text))


def _is_capitals(text):
    """True when the text (ignoring brackets) is written in CAPITALS."""
    letters = [ch for ch in _without_brackets(text) if ch.isalpha()]
    return len(letters) >= 3 and all(ch.isupper() for ch in letters)


def _word_count(text):
    """Count words separated by spaces ("FENCE-SITTERS" counts as one word)."""
    return len(_without_brackets(text).split())


def find_incomplete_ending(lines):
    """Return the last line if the document seems to stop mid-word.

    Example: the TMICC context document currently ends with the fragment
    "Bes". A very short final line with no punctuation is treated as a sign
    that the document was cut off.
    """
    if not lines:
        return None
    last = lines[-1]
    if len(last) <= 4 and last.isalpha():
        return last
    return None


def build_passages(lines, file_name, topic):
    """Turn raw lines into passages.

    Each passage is a dictionary:
        file     - the Word file it came from
        topic    - Kotter / Pfeffer / Ritti & Levy / Schein / TMICC context
        title    - first line of the document
        heading  - main heading above the passage (may be "")
        subhead  - sub-heading above the passage (may be "")
        section  - readable label, e.g. "DECISION 2: ... > LOSERS"
        label    - short label at the start of the passage, e.g. "Controls"
        text     - the passage itself, exactly as written in the document
        kind     - "bullet", "numbered", "statement" or "heading"
    """
    passages = []
    if not lines:
        return passages

    title = lines[0]
    body = lines[1:]
    if find_incomplete_ending(lines):
        body = body[:-1]  # drop the cut-off fragment so it is never quoted

    heading = {"text": ""}     # dictionaries so a wrapped heading can grow
    subhead = {"text": ""}
    current = None             # the passage that wrapped lines are added to
    growing_heading = None     # set while a heading continues on the next line

    def start_passage(text, kind, label=""):
        passage = {
            "file": file_name, "topic": topic, "title": title,
            "_heading": heading, "_subhead": subhead,
            "label": label, "text": text, "kind": kind,
        }
        passages.append(passage)
        return passage

    for line in body:
        # A separator such as "---" closes the current section.
        if SEPARATOR_PATTERN.match(line):
            heading, subhead = {"text": ""}, {"text": ""}
            current, growing_heading = None, None
            continue

        bullet = BULLET_PATTERN.match(line)
        numbered = NUMBERED_PATTERN.match(line)
        label = LABEL_PATTERN.match(line)

        # Bullets and numbered items always start a new passage.
        if bullet or numbered:
            content = bullet.group(1) if bullet else line
            inner = LABEL_PATTERN.match(bullet.group(1) if bullet else numbered.group(2))
            inner_label = inner.group(1) if inner and inner.group(2) else ""
            current = start_passage(content, "bullet" if bullet else "numbered", inner_label)
            growing_heading = None
            continue

        # A line in CAPITALS without a colon is a main heading,
        # e.g. "TRIAN PARTNERS (activist investor)".
        if _is_capitals(line) and not label:
            heading, subhead = {"text": line}, {"text": ""}
            current, growing_heading = None, None
            continue

        if label:
            name, rest = label.group(1), label.group(2)
            if not rest:
                # A heading that ends with a colon, e.g. "WINNERS:".
                if _is_capitals(name) and _word_count(name) > 1:
                    heading, subhead = {"text": name}, {"text": ""}
                else:
                    subhead = {"text": name}
                current, growing_heading = None, None
                continue
            if _is_capitals(name) and re.search(r"\d", name):
                # A numbered main heading with its own text,
                # e.g. "DECISION 1: Centralise brand decisions ...".
                heading, subhead = {"text": line}, {"text": ""}
                current = start_passage(line, "heading", name)
                current["_heading"] = {"text": ""}  # do not repeat itself as its own heading
                growing_heading = heading
                continue
            # An ordinary labelled statement, e.g. "STRATEGY: Secure ...".
            if _is_capitals(name):
                subhead = {"text": ""}
            current = start_passage(line, "statement", name)
            growing_heading = None
            continue

        # Anything else continues the previous line (a wrapped sentence).
        if current is not None:
            current["text"] = normalise(current["text"] + " " + line)
            if growing_heading is not None:
                growing_heading["text"] = current["text"]
        else:
            current = start_passage(line, "statement")

    # Turn the heading references into plain text labels.
    for passage in passages:
        passage["heading"] = passage.pop("_heading")["text"]
        passage["subhead"] = passage.pop("_subhead")["text"]
        parts = [part for part in (passage["heading"], passage["subhead"]) if part]
        passage["section"] = " > ".join(parts)
    return passages


# ---------------------------------------------------------------------------
# Step 3: load everything
# ---------------------------------------------------------------------------

def load_documents(document_list=None):
    """Load every knowledge document.

    Returns a list with one dictionary per document:
        file, topic, text, error, characters  (same keys the app always used)
        passages  - list of passages built by build_passages()
        warning   - message if the document looks incomplete, else None
    """
    documents = []
    for item in document_list or KNOWLEDGE_DOCUMENTS:
        lines, error = read_docx_lines(item["file"])
        text = "\n".join(lines)
        fragment = find_incomplete_ending(lines)
        warning = None
        if fragment:
            warning = (
                f"This document appears to stop mid-sentence (it ends with \"{fragment}\"). "
                "Anything after that point is missing and cannot be used."
            )
        documents.append({
            "file": item["file"],
            "topic": item["topic"],
            "text": text,
            "error": error,
            "characters": len(text),
            "passages": build_passages(lines, item["file"], item["topic"]),
            "warning": warning,
        })
    return documents


def all_passages(documents):
    """Return one flat list containing the passages of every document."""
    passages = []
    for document in documents:
        passages.extend(document["passages"])
    return passages


def passages_under_heading(passages, file_name, heading):
    """Return every passage of one document that sits under a main heading."""
    return [
        passage for passage in passages
        if passage["file"] == file_name
        and (passage["heading"] == heading or (passage["kind"] == "heading" and passage["text"] == heading))
    ]


def source_label(passage):
    """Readable source reference, e.g. "RITTI.docx > DECISION 2 ... > LOSERS"."""
    parts = [passage["file"]]
    heading = passage["heading"]
    numbered = re.match(r"^([A-Z]+ \d+):", heading)
    if numbered and len(heading) > 45:
        heading = numbered.group(1)  # "DECISION 2: Renegotiate ..." -> "DECISION 2"
    parts.extend(part for part in (heading, passage["subhead"]) if part)
    return " > ".join(parts)
