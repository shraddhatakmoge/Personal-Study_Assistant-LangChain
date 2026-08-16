import json
from pathlib import Path

from langchain_core.tools import tool


NOTES_FILE = Path("data/notes.json")


def load_notes():
    if not NOTES_FILE.exists():
        return []

    with open(NOTES_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_notes(notes):
    NOTES_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(NOTES_FILE, "w", encoding="utf-8") as file:
        json.dump(notes, file, indent=4)


@tool
def save_note(note: str) -> str:
    """Save a study note for future revision."""

    notes = load_notes()
    notes.append(note)
    save_notes(notes)

    return "Note saved successfully."


@tool
def get_notes() -> str:
    """Retrieve all saved study notes."""

    notes = load_notes()

    if not notes:
        return "No notes saved yet."

    return "\n".join(
        f"{i + 1}. {note}"
        for i, note in enumerate(notes)
    )