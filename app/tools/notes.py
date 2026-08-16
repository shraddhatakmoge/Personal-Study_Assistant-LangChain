import json
from pathlib import Path

from langchain_core.tools import tool


NOTES_FILE = Path("data/notes.json")


# ============================================================
# LOAD NOTES
# ============================================================

def load_notes():
    """Load all saved study notes."""

    if not NOTES_FILE.exists():
        return []

    try:
        with open(
            NOTES_FILE,
            "r",
            encoding="utf-8",
        ) as file:

            notes = json.load(file)

        if not isinstance(notes, list):
            return []

        return notes

    except (
        json.JSONDecodeError,
        OSError,
    ):
        return []


# ============================================================
# SAVE NOTES
# ============================================================

def save_notes(notes):
    """Save all notes to the JSON file."""

    NOTES_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        NOTES_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            notes,
            file,
            indent=4,
            ensure_ascii=False,
        )


# ============================================================
# SAVE ONE NOTE
# ============================================================

@tool
def save_note(note: str) -> str:
    """Save a study note for future revision."""

    note = note.strip()

    if not note:
        return "Cannot save an empty note."

    notes = load_notes()

    notes.append(note)

    save_notes(notes)

    return "Note saved successfully."


# ============================================================
# GET ALL NOTES
# ============================================================

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


# ============================================================
# DELETE ONE NOTE
# ============================================================

@tool
def delete_note(index: int) -> str:
    """
    Delete one study note.

    index is ZERO-BASED:
        0 = first note
        1 = second note
        2 = third note
    """

    notes = load_notes()

    if not notes:
        return "No notes saved yet."

    if index < 0 or index >= len(notes):
        return "Invalid note index."

    notes.pop(index)

    save_notes(notes)

    return "Note deleted successfully."


# ============================================================
# DELETE ALL NOTES
# ============================================================

@tool
def clear_notes() -> str:
    """Delete all saved study notes."""

    save_notes([])

    return "All study notes have been cleared."