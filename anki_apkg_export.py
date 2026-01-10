import genanki
import tempfile
import time
import os

def export_quiz_to_apkg(quiz_title, rows):
    """
    rows = list of dicts with keys:
      - question_text
      - choices (list of strings, already formatted)
      - correct_text (string or list)
    """

    model = genanki.Model(
        model_id=1607392319,
        name="AutoQuiz MCQ Model",
        fields=[
            {"name": "Question"},
            {"name": "Choices"},
            {"name": "Answer"},
        ],
        templates=[
            {
                "name": "Card 1",
                "qfmt": """
                    <div style="font-size:18px;">
                        {{Question}}
                    </div>
                    <hr>
                    <div>
                        {{Choices}}
                    </div>
                """,
                "afmt": """
                    {{FrontSide}}
                    <hr>
                    <b>Correct Answer</b><br>
                    {{Answer}}
                """,
            }
        ],
    )

    deck = genanki.Deck(
        int(time.time()),
        quiz_title
    )

    for r in rows:
        note = genanki.Note(
            model=model,
            fields=[
                r["question_text"],
                "<br>".join(r["choices"]),
                r["correct_text"],
            ],
        )
        deck.add_note(note)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".apkg")
    genanki.Package(deck).write_to_file(tmp.name)

    return tmp.name
