import genanki
import random
import os
from datetime import datetime

from auto_quiz.archive.anki_prototypes.anki_model import ANKI_MODEL


def build_anki_deck(
    deck_name: str,
    questions: list,
    output_dir: str = "exports",
):
    """
    questions = [
        {
            "question": "What port does HTTPS use?",
            "choices": ["A. 21", "B. 22", "C. 443", "D. 80"],
            "correct": "C. 443",
            "explanation": "HTTPS uses TCP port 443.",
            "stats": "Missed 3 times · Confidence: Low",
            "source": "Server+ Practice Set"
        }
    ]
    """

    os.makedirs(output_dir, exist_ok=True)

    deck_id = random.randrange(1 << 30, 1 << 31)
    deck = genanki.Deck(deck_id, deck_name)

    for q in questions:
        note = genanki.Note(
            model=ANKI_MODEL,
            fields=[
                q.get("question", ""),
                "<br>".join(q.get("choices", [])),
                q.get("correct", ""),
                q.get("explanation", ""),
                q.get("stats", ""),
                q.get("source", ""),
            ]
        )
        deck.add_note(note)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{deck_name.replace(' ', '_')}_{timestamp}.apkg"
    filepath = os.path.join(output_dir, filename)

    genanki.Package(deck).write_to_file(filepath)

    return filepath
