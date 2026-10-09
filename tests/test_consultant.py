"""Tests for the TMICC Change Management Consultant.

Run from the repository folder with:

    python -m unittest discover -s tests -v

No extra packages are needed (Streamlit is not required for these tests).
"""

import os
import re
import sys
import unittest

REPOSITORY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPOSITORY)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from consultant import answers, documents, knowledge, questions, retrieval  # noqa: E402

KB = answers.build_knowledge_base()


def squash(text):
    """Lower-case and remove spacing/quote differences for comparisons."""
    text = text.replace('"', "'").replace("“", "'").replace("”", "'")
    return re.sub(r"\s+", " ", text).strip().lower()


RAW_TEXT = {doc["file"]: squash(doc["text"].replace("\n", " ")) for doc in KB["documents"]}
ALL_RAW_TEXT = " ".join(RAW_TEXT.values())


def ask(question, previous=None):
    return answers.answer_question(question, KB, previous)


def document_quotes(answer):
    """Every piece of text the answer presents as a quotation from the documents."""
    quotes = []

    def walk(item):
        if item["label"] == knowledge.LABEL_DOCUMENT:
            quotes.append(item["text"])
        for child in item["children"]:
            walk(child)

    for section in answer["sections"]:
        for item in section["items"]:
            walk(item)
        if section["table"]:
            for row in section["table"]["rows"]:
                for cell in row:
                    quotes.extend(re.findall(r"“[^”]+”", str(cell)))
    return quotes


class DocumentTests(unittest.TestCase):
    def test_all_five_documents_load(self):
        self.assertEqual(len(KB["documents"]), 5)
        for doc in KB["documents"]:
            self.assertIsNone(doc["error"], doc["file"])
            self.assertGreater(len(doc["passages"]), 5, doc["file"])

    def test_passages_only_regroup_the_original_text(self):
        """Rebuilding lines into passages must never add or change words."""
        for passage in KB["passages"]:
            self.assertIn(squash(passage["text"]), RAW_TEXT[passage["file"]], passage["text"])

    def test_wrapped_lines_are_joined(self):
        texts = [passage["text"] for passage in KB["passages"]]
        self.assertIn("Step 1 – Urgency: Activist investor Trian is watching. "
                      "Must prove standalone viability quickly.", texts)

    def test_section_labels(self):
        loser = next(p for p in KB["passages"] if p["text"].startswith("TMICC staff currently on Unilever systems"))
        self.assertTrue(loser["heading"].startswith("DECISION 2"))
        self.assertEqual(loser["subhead"], "LOSERS")
        self.assertEqual(documents.source_label(loser), "RITTI.docx > DECISION 2 > LOSERS")

    def test_cut_off_document_is_flagged_and_fragment_not_quoted(self):
        context = next(doc for doc in KB["documents"] if doc["topic"] == "TMICC context")
        if context["text"].rstrip().endswith("Bes"):
            self.assertIsNotNone(context["warning"])
            self.assertFalse(any(p["text"].rstrip().endswith("Bes") for p in context["passages"]))

    def test_missing_file_is_reported_not_raised(self):
        loaded = documents.load_documents([{"file": "DOES NOT EXIST.docx", "topic": "Kotter"}])
        self.assertIn("not found", loaded[0]["error"].lower())
        empty = answers.build_knowledge_base(loaded)
        answer = answers.answer_question("How should TMICC manage employee resistance?", empty)
        self.assertTrue(answer["markdown"])


class SearchTests(unittest.TestCase):
    def topics(self, query, count=8):
        return {r["passage"]["topic"] for r in retrieval.search(KB["index"], query, max_results=count)}

    def test_word_endings_match(self):
        self.assertEqual(retrieval.stem("stakeholders"), retrieval.stem("stakeholder"))
        self.assertEqual(retrieval.stem("cultural"), retrieval.stem("culture"))
        self.assertEqual(retrieval.stem("centralised"), retrieval.stem("centralisation"))

    def test_tsa_abbreviation_finds_several_documents(self):
        found = self.topics("We depend on Unilever for IT and HR under the TSA. How do we exit?")
        self.assertTrue({"Pfeffer", "Ritti & Levy", "TMICC context"} <= found)

    def test_ben_and_jerrys_abbreviation(self):
        results = retrieval.search(KB["index"], "B&J governance dispute", max_results=6)
        self.assertTrue(any("DECISION 3" in r["passage"]["text"] + r["passage"]["heading"] for r in results))

    def test_unrelated_question_finds_nothing(self):
        self.assertEqual(retrieval.search(KB["index"], "What's the weather in Coventry?"), [])

    def test_missing_words_are_reported(self):
        self.assertIn("engagement", retrieval.words_not_in_documents(KB["index"], "employee engagement"))


class QuestionRuleTests(unittest.TestCase):
    def test_question_types(self):
        expected = {
            "What is the main change management challenge facing TMICC?": "diagnose",
            "How should TMICC manage employee resistance?": "advice",
            "Which framework fits the Ben & Jerry's governance dispute, and why?": "framework_choice",
            "Compare Kotter, Schein, Pfeffer, and Ritti & Levy.": "compare",
            "Develop a change management strategy, implementation roadmap, or action plan for TMICC.": "plan",
            "What are the risks, stakeholder implications, and expected benefits of a proposed intervention?": "risk_benefit",
            "Who wins and who loses if brand decisions are centralised?": "stakeholder",
            "Who is Trian and what do they want?": "fact",
            "Explain Schein's three levels": "explain_framework",
            "What's the weather in Coventry?": "out_of_scope",
            "How do I bake a cake?": "out_of_scope",
            "Hello": "greeting",
            "Are you an AI?": "about_tool",
        }
        for question, question_type in expected.items():
            self.assertEqual(questions.analyse(question, KB["index"])["type"], question_type, question)

    def test_framework_routing(self):
        cases = {
            "Which framework fits the Ben & Jerry's governance dispute, and why?": "Ritti & Levy",
            "How should Peter build a relationship with investors?": "Pfeffer",
            "What should TMICC stand for?": "Schein",
            "Why is the change programme stalling?": "Kotter",
        }
        for question, framework in cases.items():
            self.assertIn(framework, questions.analyse(question, KB["index"])["frameworks"], question)

    def test_no_framework_is_forced(self):
        self.assertEqual(questions.analyse("How do I motivate my team?", KB["index"])["frameworks"], [])

    def test_follow_up_keeps_the_topic(self):
        first = ask("Build a roadmap for exiting the Unilever transitional service agreements.")
        second = ask("What are the risks of that?", first["analysis"])
        self.assertTrue(second["analysis"]["follow_up"])
        self.assertIn("DECISION 2", second["markdown"])
        fresh = ask("Who is Trian?", first["analysis"])
        self.assertFalse(fresh["analysis"]["follow_up"])


class AnswerTests(unittest.TestCase):
    QUESTIONS = [
        "What is the main change management challenge facing TMICC?",
        "How should TMICC manage employee resistance?",
        "Which change management framework is most appropriate for a particular challenge, and why?",
        "Which framework fits the Ben & Jerry's governance dispute, and why?",
        "Compare Kotter, Schein, Pfeffer, and Ritti & Levy.",
        "Develop a change management strategy, implementation roadmap, or action plan for TMICC.",
        "What are the risks, stakeholder implications, and expected benefits of a proposed intervention?",
        "How can leadership, organisational culture, employee engagement, communication, and "
        "stakeholder relationships be managed during the separation?",
        "Build a roadmap for exiting the Unilever transitional service agreements.",
        "Who wins and who loses if brand decisions are centralised?",
        "Who are the key stakeholders?",
        "Who is Trian and what do they want?",
        "When was TMICC listed?",
        "What is TMICC's revenue?",
        "Explain Schein's three levels",
        "What are Kotter's 8 steps?",
        "Is Kotter better than Schein for culture?",
        "Why is the change programme stalling?",
        "What should TMICC stand for?",
        "How do I motivate my team?",
        "What is change management?",
        "What's the weather in Coventry?",
        "Hello",
        "Are you an AI?",
        "",
        "???",
        "a" * 3000,
    ]

    def test_every_question_gets_an_answer_without_errors(self):
        for question in self.QUESTIONS:
            answer = ask(question)
            self.assertTrue(answer["markdown"].strip(), question)
            self.assertTrue(answer["sections"], question)

    def test_no_invented_document_quotes(self):
        """Anything labelled 'From your documents' must exist word for word in the files."""
        checked = 0
        for question in self.QUESTIONS:
            for text in document_quotes(ask(question)):
                for quoted in re.findall(r"“([^”]+)”", text):
                    self.assertIn(squash(quoted), ALL_RAW_TEXT, f"{question!r} quoted: {quoted!r}")
                    checked += 1
        self.assertGreater(checked, 100)

    def test_general_knowledge_contains_no_tmicc_names(self):
        """The built-in general guidance must not state facts about TMICC."""
        names = ["tmicc", "unilever", "magnum", "ben & jerry", "trian", "kulve", "boxmeer",
                 "bhattacharya", "fernandez", "wall's", "cornetto"]
        texts = []
        for framework in knowledge.FRAMEWORKS.values():
            texts += [framework["summary"], framework["focus"], framework["best_for"], framework["key_question"]]
            texts += framework["benefits"] + framework["limitations"] + framework["outcomes"] + framework["measures"]
            texts += [action["text"] for action in framework["actions"]]
            texts += [entry["risk"] + entry["mitigation"] for entry in framework["risks"]]
        for theme in knowledge.THEMES.values():
            texts += [theme["diagnosis"]] + theme["measures"] + theme["outcomes"]
            texts += [action["text"] for action in theme["actions"]]
            texts += [entry["risk"] + entry["mitigation"] for entry in theme["risks"]]
        texts += list(knowledge.INFERENCE_RULES.values()) + list(knowledge.FRAMEWORK_TENSIONS.values())
        for text in texts:
            for name in names:
                self.assertNotIn(name, text.lower(), text)

    def test_main_challenge_quotes_the_key_tensions(self):
        markdown = ask("What is the main change management challenge facing TMICC?")["markdown"]
        self.assertIn("Transitional service agreements with Unilever (IT, HR, legal) create dependency", markdown)
        self.assertIn("without ranking them", markdown)

    def test_payoff_map_for_centralising_brands(self):
        markdown = ask("Who wins and who loses if brand decisions are centralised?")["markdown"]
        for expected in ("DECISION 1", "Local market managers (loss of autonomy)", "Fence-sitters"):
            self.assertIn(expected, markdown)

    def test_roadmap_is_labelled_as_general_guidance(self):
        answer = ask("Build a roadmap for exiting the Unilever transitional service agreements.")
        roadmap = next(s for s in answer["sections"] if s["title"] == "Implementation roadmap")
        self.assertIn("General guidance", roadmap["intro"])
        self.assertIn("illustrative", roadmap["intro"])
        phases = {row[0] for row in roadmap["table"]["rows"]}
        self.assertGreaterEqual(len(phases), 3)

    def test_revenue_question_gives_no_figure(self):
        markdown = ask("What is TMICC's revenue?")["markdown"]
        self.assertIn("No figures in your documents", markdown)
        body = markdown.split("\n---\n")[0]   # the part before the legend
        self.assertNotIn("General guidance", body)

    def test_out_of_scope_is_declined(self):
        answer = ask("What's the weather in Coventry?")
        self.assertEqual(answer["type"], "out_of_scope")
        self.assertEqual(document_quotes(answer), [])

    def test_uncovered_topic_is_declared(self):
        markdown = ask("How do I motivate my team?")["markdown"]
        self.assertIn("No passage in the five documents matched", markdown)
        self.assertIn("General guidance", markdown)

    def test_tool_never_claims_to_be_ai(self):
        markdown = ask("Are you an AI?")["markdown"]
        self.assertIn("not an AI model", markdown)

    def test_contradictions_between_frameworks_are_shown(self):
        markdown = ask("How should TMICC manage employee resistance?")["markdown"]
        self.assertIn("pull in different directions", markdown)


class AppScreenTests(unittest.TestCase):
    """Runs app.py from top to bottom with a stand-in for Streamlit."""

    @classmethod
    def setUpClass(cls):
        import fake_streamlit
        cls.real_streamlit = sys.modules.get("streamlit")
        cls.st = fake_streamlit.install()
        sys.modules.pop("app", None)
        import app
        cls.app = app

    @classmethod
    def tearDownClass(cls):
        sys.modules.pop("app", None)
        if cls.real_streamlit is not None:
            sys.modules["streamlit"] = cls.real_streamlit
        else:
            sys.modules.pop("streamlit", None)

    def setUp(self):
        self.st.session_state.clear()
        self.st.inputs.clear()
        self.st.clicked.clear()
        self.st.reset_output()

    def test_app_opens_with_all_tabs(self):
        self.app.main()
        tabs = self.st.shown("tabs")
        for name in ("Ask the consultant", "Analyse a challenge", "Knowledge base documents",
                     "Framework reference", "How this app works"):
            self.assertIn(name, tabs)
        self.assertEqual(self.st.shown("error"), "")

    def test_typed_question_is_answered_and_kept_in_history(self):
        self.st.inputs["Your question"] = "Who is Trian and what do they want?"
        self.st.clicked.add("Ask")
        self.app.main()
        history = self.st.session_state["chat_history"]
        self.assertEqual(len(history), 1)
        self.assertIn("Wants: margin improvement, portfolio focus", self.st.shown("markdown"))

    def test_example_button_and_follow_up(self):
        self.st.clicked.add(knowledge.EXAMPLE_QUESTIONS[4])   # the roadmap example
        self.app.main()
        self.st.clicked.clear()
        self.st.inputs["Your question"] = "What are the risks of that?"
        self.st.clicked.add("Ask")
        self.app.main()
        history = self.st.session_state["chat_history"]
        self.assertEqual(len(history), 2)
        self.assertTrue(history[1]["analysis"]["follow_up"])

    def test_clear_conversation(self):
        self.st.session_state["chat_history"] = [{"question": "q", "markdown": "m", "analysis": None}]
        self.st.clicked.add("Clear conversation")
        self.app.main()
        self.assertEqual(self.st.session_state["chat_history"], [])

    def test_existing_analyse_tab_still_works(self):
        self.st.inputs["What is happening, and what is the main change-management problem?"] = (
            "As TMICC becomes standalone, teams are uncertain about decision rights, "
            "legacy systems and the new culture."
        )
        self.st.clicked.add("Analyse challenge")
        self.app.main()
        shown = self.st.shown()
        for heading in ("1. Frameworks selected and why", "3. Recommended actions",
                        "6. Relevant passages from the knowledge documents"):
            self.assertIn(heading, shown)
        self.assertIn("Source:", self.st.shown("caption"))

    def test_older_rule_functions_are_unchanged(self):
        selected, scores, reasons = self.app.select_frameworks(
            "Culture and legacy values are blocking adoption", "Other / not sure", "Not sure", None, 3)
        self.assertIn("Schein", selected)
        manual, _, _ = self.app.select_frameworks("anything at all here", "Other / not sure", "Not sure", ["Pfeffer"], 3)
        self.assertEqual(manual, ["Pfeffer"])
        self.assertEqual(len(self.app.build_actions(["Kotter", "Schein"], "x", "Planning")), 6)


if __name__ == "__main__":
    unittest.main()
