"""Rule-based engine behind the TMICC Change Management Consultant.

The package is split into small files so each job is easy to find:

    documents.py  - reads the five Word documents and rebuilds them into passages
    retrieval.py  - searches those passages for text relevant to a question
    knowledge.py  - general change-management content and rules (data only)
    questions.py  - works out what kind of question was asked and which
                    frameworks apply
    answers.py    - assembles the structured, source-labelled answer

Nothing in this package imports Streamlit, calls an AI model or uses the
internet, so every function can be tested with plain Python.
"""
