import genanki
import random
import datetime
import os


# =========================
# ANKI MODEL (NOTE TYPE)
# =========================
ANKI_MODEL = genanki.Model(
    model_id=1607392319,  # stable random ID (do NOT change once released)
    name="DrakQuizLab Question",
    fields=[
        {"name": "Question"},
        {"name": "Choices"},
        {"name": "CorrectAnswer"},
        {"name": "YourAnswer"},
        {"name": "Stats"},
        {"name": "Source"},
    ],
    templates=[
        {
            "name": "Question → Answer",
            "qfmt": """
                <h3>{{Question}}</h3>
                <pre>{{Choices}}</pre>
            """,
            "afmt": """
                {{FrontSide}}
                <hr>
                <b>Correct Answer:</b><br>
                {{CorrectAnswer}}<br><br>

                <b>Your Answer:</b><br>
                {{YourAnswer}}<br><br>

                <b>Stats:</b><br>
                {{Stats}}<br><br>

                <small>{{Source}}</small>
            """,
        }
    ],
)


# =========================
# EXPORT ONE QUESTION
# =========================
def export_single_question_to_anki(
    *,
    question_text: str,
    choices: list[str],
    correct_answer: str,
    user_answer: str,
    quiz_title: str,
    missed_count: int,
    confidence: str,
    output_path: str = "anki_export.apkg",
):
    # Deck ID must stay stable per "deck"
    deck_id = random.randrange(1 << 30, 1 << 31)
    deck_name = f"DrakQuizLab::{quiz_title}"

    deck = genanki.Deck(deck_id, deck_name)

    choices_block = "\n".join(choices)

    stats_block = (
        f"Missed Count: {missed_count}\n"
        f"Confidence: {confidence}"
    )

    source_block = (
        f"DrakQuizLab · {quiz_title} · "
        f"{datetime.date.today().isoformat()}"
    )

    note = genanki.Note(
        model=ANKI_MODEL,
        fields=[
            question_text,
            choices_block,
            correct_answer,
            user_answer or "(Not answered)",
            stats_block,
            source_block,
        ],
        tags=[
            "drakquizlab",
            f"quiz_{quiz_title.replace(' ', '_')}",
            "missed" if missed_count > 0 else "correct",
            f"confidence_{confidence.lower()}",
        ],
    )

    deck.add_note(note)

    genanki.Package(deck).write_to_file(output_path)

    return output_path
