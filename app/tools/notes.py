from pathlib import Path
from langchain_core.tools import tool
from pathlib import Path
from langchain_core.tools import tool

print("🔥 NOTES.PY LOADED")
print("🔥 NOTES FILE:", __file__)


NOTES_FILE = Path(__file__).resolve().parents[2] / "data" / "notes.txt"


def load_notes() -> list[str]:
    """Load all saved notes."""
    if not NOTES_FILE.exists():
        return []

    text = NOTES_FILE.read_text(encoding="utf-8").strip()

    if not text:
        return []

    return [line for line in text.splitlines() if line.strip()]


def _save_notes(notes: list[str]) -> None:
    """Save notes to disk."""
    NOTES_FILE.parent.mkdir(parents=True, exist_ok=True)
    NOTES_FILE.write_text(
        "\n".join(notes),
        encoding="utf-8",


    )

@tool
def save_note(note: str) -> str:
    """Save a study note to the study notes file."""
    note = note.strip()

    if not note:
        return "Cannot save an empty note."

    notes = load_notes()
    notes.append(note)

    _save_notes(notes)

    return f"Note saved: {note}"


@tool
def get_notes() -> str:
    """Return all saved notes."""
    notes = load_notes()

    if not notes:
        return "No notes saved."

    return "\n".join(
        f"{i + 1}. {note}"
        for i, note in enumerate(notes)
    )


@tool
def delete_note(index: int) -> str:
    """Delete a note by its 1-based index."""
    notes = load_notes()

    if not notes:
        return "No notes to delete."

    if index < 1 or index > len(notes):
        return f"Invalid note number. Choose between 1 and {len(notes)}."

    deleted = notes.pop(index - 1)
    _save_notes(notes)

    return f"Deleted note: {deleted}"


@tool
def clear_notes() -> str:
    """Delete all saved notes."""
    _save_notes([])

    return "All notes cleared."