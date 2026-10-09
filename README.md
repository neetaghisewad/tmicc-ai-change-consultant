# TMICC Change Management Consultant

A free, rule-based change management consulting tool for The Magnum Ice Cream Company (TMICC) case, built with Python and Streamlit.

It is a rule-based rebuild of a multi-agent consultant originally designed in Copilot. It uses **no AI model, no paid API and no API key**. It matches the words of a question against rules and against five Word documents, then assembles a structured answer.

## What it does

- **Ask the consultant** – ask a question in your own words and get a structured answer. Follow-up questions such as "what are the risks of that?" keep the topic of the previous question.
- **Analyse a challenge** – the original form: describe a challenge, choose a change type and stage, and get a framework-based diagnosis.
- **Knowledge base documents** – shows that each Word file loaded, and previews it.
- **Framework reference** – general summaries of the four frameworks.
- **How this app works** – the method and its limits.

The four frameworks are Kotter (change readiness), Pfeffer (power and networks), Ritti & Levy (winners, losers and political strategy) and Schein (culture).

## Where every statement comes from

Every answer opens with a short direct answer. Each line of an answer is one of three kinds:

| Label | Meaning |
|---|---|
| 📄 From your documents | Quoted word for word from one of the five Word files, with file and section. |
| 🔎 Inference | A rule linking a quoted passage to a framework idea. Plausible, not proven. |
| 📘 General guidance | Standard change-management practice. Not stated in the documents. |

By default the chat shows a clean reading view without these labels. Tick **Show source labels** in the sidebar to see them.

The app never writes its own statements about TMICC. If the documents do not cover a question, it says so. Timelines, owners and success measures in roadmaps are always general guidance, because the documents contain none.

## Files

| File | Purpose |
|---|---|
| `app.py` | The screens (Streamlit). Start here. |
| `consultant/documents.py` | Reads the Word files and rebuilds them into labelled passages. |
| `consultant/retrieval.py` | Keyword search across all five documents. |
| `consultant/knowledge.py` | General framework content and rules. Edit wording here. |
| `consultant/questions.py` | Question type, framework routing, follow-ups, scope checks. |
| `consultant/answers.py` | Builds the source-labelled answer. |
| `tests/` | Automated checks. |
| `*.docx` | The five knowledge documents. Keep them beside `app.py`. |
| `requirements.txt` | Only `streamlit`. |

## Run it

```
pip install -r requirements.txt
streamlit run app.py
```

On Streamlit Community Cloud, the main file is `app.py`. No secrets are needed.

## Test it

```
python -m unittest discover -s tests -v
```

The tests need no extra packages. Among other things they check that every "From your documents" quotation exists word for word in the Word files, and that the built-in general guidance contains no TMICC names.

Questions to try by hand:

1. What is the main change management challenge facing TMICC?
2. How should TMICC manage employee resistance?
3. Which framework fits the Ben & Jerry's governance dispute, and why?
4. Compare Kotter, Schein, Pfeffer and Ritti & Levy.
5. Build a roadmap for exiting the Unilever transitional service agreements.
6. What are the risks of that? *(ask straight after question 5)*
7. Who is Trian and what do they want?
8. What is TMICC's revenue? *(should say the documents give no figure)*
9. What's the weather in Coventry? *(should be declined as out of scope)*

## Changing the documents

Edit or replace the Word files and redeploy; nothing else needs to change. The app works best when documents keep their current style: headings in capitals or ending with a colon, and bullet points starting with `-`.

## Limitations

- This is a rule-based tool, not a chatbot. It matches words and cannot understand a question the way a person or a large language model can. Unusual wording can be misclassified.
- The five documents are short, so many answers rely mainly on general guidance.
- The documents have not been checked against outside sources.
- `TMICC ORCHESTRATOR CONTEXT DOCUMENT.docx` currently stops mid-sentence. The app flags this and ignores the cut-off fragment.
- Review every answer before relying on it.
