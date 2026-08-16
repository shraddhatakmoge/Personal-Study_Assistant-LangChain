import json
from pathlib import Path

from langchain_core.tools import tool


NOTES_FILE = Path("data/notes.json")


# ============================================================
# LOAD NOTES
# ============================================================

def load_notes():
    """Load all saved study notes from the JSON file."""

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
    """Save the complete notes list to the JSON file."""

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
# SAVE NOTE
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
# GET NOTES
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
    """Delete one saved study note using its zero-based index."""

    notes = load_notes()

    if not notes:
        return "No notes saved yet."

    if index < 0 or index >= len(notes):
        return "Invalid note index."

    deleted_note = notes.pop(index)

    save_notes(notes)

    return "Note deleted successfully."


# ============================================================
# CLEAR ALL NOTES
# ============================================================

@tool
def clear_notes() -> str:
    """Delete all saved study notes."""

    save_notes([])

    return "All study notes have been cleared."