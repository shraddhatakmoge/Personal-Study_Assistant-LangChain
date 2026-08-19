import sys
import os
import html
import json
import textwrap
from pathlib import Path
import os
import streamlit as st

st.write("GROQ KEY PRESENT:", bool(os.getenv("GROQ_API_KEY")))
st.write("MODEL:", os.getenv("MODEL_NAME", "llama-3.1-8b-instant"))
# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# STREAMLIT
# ============================================================

import streamlit as st
import requests


# ============================================================
# NOTES
# ============================================================

# Notes are read directly from data/notes.json for the UI.


# ============================================================
# NOTES UI STORAGE HELPERS
# ============================================================

NOTES_FILE = PROJECT_ROOT / "data" / "notes.json"


def load_notes_for_ui():
    """Load notes directly from the JSON file for the Streamlit UI."""

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


def save_notes_for_ui(notes):
    """Save notes directly to the JSON file."""

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


def delete_note_for_ui(index):
    """Delete one note using its zero-based index."""

    notes = load_notes_for_ui()

    if index < 0 or index >= len(notes):
        return False

    notes.pop(index)

    save_notes_for_ui(notes)

    return True


def clear_all_notes_for_ui():
    """Delete every saved note."""

    save_notes_for_ui([])

    return True



# ============================================================
# RAG API
# ============================================================

RAG_API_URL = os.getenv(
    "STUDYMATE_API_URL",
    "https://personal-study-assistant-langchain.onrender.com",
).rstrip("/")


def upload_document_to_api(
    uploaded_file,
):
    """Upload the selected document to the FastAPI RAG backend."""

    if not uploaded_file.name.lower().endswith(".pdf"):
        return {
            "ok": False,
            "error": "Only PDF files are currently supported for RAG.",
        }

    try:
        file_bytes = uploaded_file.getvalue()

        response = requests.post(
            f"{RAG_API_URL}/rag/upload",
            files={
                "file": (
                    uploaded_file.name,
                    file_bytes,
                    uploaded_file.type or "application/pdf",
                )
            },
            timeout=180,
        )

        if not response.ok:
            try:
                detail = response.json().get(
                    "detail",
                    response.text,
                )
            except Exception:
                detail = response.text

            return {
                "ok": False,
                "error": str(detail),
            }

        data = response.json()

        return {
            "ok": True,
            "data": data,
        }

    except requests.RequestException as exc:
        return {
            "ok": False,
            "error": (
                "Could not connect to the deployed StudyMate API at "
                f"{RAG_API_URL}. Check the Render service status and try again."
            ),
        }

    except Exception as exc:
        return {
            "ok": False,
            "error": str(exc),
        }


def ask_rag_api(
    document_id: str,
    question: str,
):
    """Ask the FastAPI RAG backend about the uploaded PDF."""

    try:
        response = requests.post(
            f"{RAG_API_URL}/rag/ask",
            json={
                "document_id": document_id,
                "question": question,
            },
            timeout=120,
        )

        if not response.ok:
            try:
                detail = response.json().get(
                    "detail",
                    response.text,
                )
            except Exception:
                detail = response.text

            return {
                "ok": False,
                "error": str(detail),
            }

        data = response.json()

        return {
            "ok": True,
            "data": data,
        }

    except requests.RequestException:
        return {
            "ok": False,
            "error": (
                "Could not connect to the deployed StudyMate API at "
                f"{RAG_API_URL}. Check the Render service status and try again."
            ),
        }

    except Exception as exc:
        return {
            "ok": False,
            "error": str(exc),
        }


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="StudyMate",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# HTML HELPER
# ============================================================

def render_html(content: str):
    st.html(textwrap.dedent(content).strip())


# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "memory" not in st.session_state:
    st.session_state.memory = None

if "agent" not in st.session_state:
    st.session_state.agent = None

if "show_notes" not in st.session_state:
    st.session_state.show_notes = False

if "confirm_clear_notes_state" not in st.session_state:
    st.session_state.confirm_clear_notes_state = False

# Start CLOSED. On phones this shows only the compact rail.
# Tapping the purple hamburger opens the full sidebar overlay.
# Fresh sessions start with the compact rail closed.
if "sidebar_open" not in st.session_state:
    st.session_state.sidebar_open = False

if "focus_chat" not in st.session_state:
    st.session_state.focus_chat = False

if "uploaded_document" not in st.session_state:
    st.session_state.uploaded_document = None




# ============================================================
# NOTES
# ============================================================

try:
    # Read the actual stored list directly.
    # The UI does not depend on delete_note/clear_notes imports,
    # avoiding the Streamlit Cloud import error.
    notes = load_notes_for_ui()
except Exception:
    notes = []

note_count = len(notes)


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>

    /* ======================================================
       GLOBAL
       ====================================================== */

    html,
    body {
        margin: 0 !important;
        padding: 0 !important;
        background: #F8F6FC !important;
    }

    .stApp {
        background: #F8F6FC !important;
    }

    [data-testid="stAppViewContainer"] {
        background: #F8F6FC !important;
    }

    [data-testid="stAppViewContainer"] > .main {
        background: #F8F6FC !important;
    }

    header {
        background: transparent !important;
    }

    #MainMenu {
        visibility: hidden !important;
    }

    footer {
        visibility: hidden !important;
    }


    /* ======================================================
       NATIVE STREAMLIT SIDEBAR

       DISABLED.
       We use a custom fixed sidebar so Streamlit's own
       collapsed/expanded browser state cannot hide it.
       ====================================================== */

    section[data-testid="stSidebar"] {
        display: none !important;
        width: 0 !important;
        min-width: 0 !important;
        max-width: 0 !important;
    }


    /* ======================================================
       MAIN CONTENT
       ====================================================== */

    .block-container {

        width: 100% !important;

        max-width: none !important;

        box-sizing: border-box !important;

        padding-top: 18px !important;

        padding-left: 42px !important;

        padding-right: 42px !important;

        /* Leave enough scrollable space for the fixed chat input.
           Without this, the last part of an answer can sit underneath
           the search bar and look cut off. */
        padding-bottom: 155px !important;
    }


    /* ======================================================
       OPEN CUSTOM SIDEBAR

       IMPORTANT:
       Use [class*="..."] instead of exact Streamlit class
       matching. This is more robust across Streamlit versions.
       ====================================================== */

    [class*="st-key-custom_sidebar"] {

        position: fixed !important;

        top: 0 !important;

        left: 0 !important;

        bottom: 0 !important;

        width: 290px !important;

        height: 100vh !important;

        min-width: 290px !important;

        max-width: 290px !important;

        box-sizing: border-box !important;

        padding: 14px 18px 24px 18px !important;

        margin: 0 !important;

        background: #FFFFFF !important;

        border-right: 1px solid #E8E1F2 !important;

        box-shadow:
            2px 0 14px
            rgba(82, 63, 130, 0.035) !important;

        overflow-y: auto !important;

        overflow-x: hidden !important;

        z-index: 999999 !important;
    }


    [class*="st-key-custom_sidebar"] > div {

        width: 100% !important;

        max-width: 100% !important;

        box-sizing: border-box !important;
    }


    /* Reserve exactly the sidebar width without changing
       the right-side design. */

    body:has([class*="st-key-custom_sidebar"])
    .block-container {

        padding-left: 332px !important;

        padding-right: 42px !important;
    }


    /* ======================================================
       OPEN SIDEBAR HAMBURGER
       ====================================================== */

    [class*="st-key-custom_sidebar"]
    [class*="st-key-close_sidebar_button"] {

        width: 38px !important;

        height: 38px !important;

        margin: 0 0 22px auto !important;

        padding: 0 !important;
    }


    [class*="st-key-custom_sidebar"]
    [class*="st-key-close_sidebar_button"] button {

        width: 38px !important;

        height: 38px !important;

        min-width: 38px !important;

        min-height: 38px !important;

        padding: 0 !important;

        margin: 0 !important;

        background: #F3EEFF !important;

        background-color: #F3EEFF !important;

        color: #7354D7 !important;

        border: 1px solid #D8C9F5 !important;

        border-radius: 10px !important;

        box-shadow:
            0 4px 12px
            rgba(115, 84, 215, 0.10) !important;

        display: flex !important;

        align-items: center !important;

        justify-content: center !important;
    }


    [class*="st-key-custom_sidebar"]
    [class*="st-key-close_sidebar_button"] button:hover {

        background: #EAE1FF !important;

        background-color: #EAE1FF !important;

        border-color: #C5B1EF !important;

        color: #6547C9 !important;
    }


    [class*="st-key-custom_sidebar"]
    [class*="st-key-close_sidebar_button"] button p {

        margin: 0 !important;

        padding: 0 !important;

        color: #7354D7 !important;

        font-size: 20px !important;

        font-weight: 800 !important;

        line-height: 1 !important;
    }


    /* ======================================================
       SIDEBAR BRAND
       ====================================================== */

    .brand-wrapper {

        display: flex;

        align-items: center;

        gap: 11px;

        margin: 0 0 27px 0;

        padding: 0;
    }

    .brand-icon {

        width: 48px;

        height: 48px;

        flex-shrink: 0;

        display: flex;

        align-items: center;

        justify-content: center;

        border-radius: 14px;

        background:
            linear-gradient(
                135deg,
                #8066E8,
                #B29CF4
            );

        font-size: 22px;

        box-shadow:
            0 8px 22px
            rgba(128, 102, 232, 0.18);
    }

    .brand-title {

        color: #292535;

        font-size: 19px;

        font-weight: 800;

        line-height: 1.1;
    }

    .brand-subtitle {

        margin-top: 4px;

        color: #918A9F;

        font-size: 9px;

        line-height: 1.2;

        white-space: nowrap;
    }


    /* ======================================================
       SIDEBAR SECTION LABELS
       ====================================================== */

    .side-section {

        margin-top: 20px;

        margin-bottom: 8px;

        color: #9992A7;

        font-size: 9px;

        font-weight: 800;

        letter-spacing: 1.2px;
    }


    /* ======================================================
       SIDEBAR BUTTONS
       ====================================================== */

    [class*="st-key-custom_sidebar"]
    [class*="st-key-new_conversation"],
    [class*="st-key-custom_sidebar"]
    [class*="st-key-study_notes"] {

        width: 100% !important;

        margin: 0 !important;

        padding: 0 !important;
    }


    [class*="st-key-custom_sidebar"]
    [class*="st-key-new_conversation"] button,
    [class*="st-key-custom_sidebar"]
    [class*="st-key-study_notes"] button {

        width: 100% !important;

        min-height: 40px !important;

        padding: 9px 12px !important;

        margin: 0 !important;

        background: #FFFFFF !important;

        background-color: #FFFFFF !important;

        color: #514A5D !important;

        border: 1px solid #E2DBED !important;

        border-radius: 10px !important;

        font-size: 12px !important;

        font-weight: 600 !important;

        line-height: 1.2 !important;

        box-shadow: none !important;
    }


    [class*="st-key-custom_sidebar"]
    [class*="st-key-new_conversation"] button:hover,
    [class*="st-key-custom_sidebar"]
    [class*="st-key-study_notes"] button:hover {

        background: #F6F2FF !important;

        background-color: #F6F2FF !important;

        color: #6F55D4 !important;

        border-color: #C9BBEE !important;
    }


    [class*="st-key-custom_sidebar"]
    [class*="st-key-new_conversation"] button p,
    [class*="st-key-custom_sidebar"]
    [class*="st-key-study_notes"] button p {

        color: inherit !important;

        font-size: 12px !important;

        font-weight: 600 !important;
    }


    /* ======================================================
       CAPABILITIES
       ====================================================== */

    .capability {

        margin: 9px 0;

        color: #777080;

        font-size: 11px;

        line-height: 1.3;

        white-space: nowrap;
    }


    /* ======================================================
       CLOSED RAIL
       ====================================================== */

    [class*="st-key-custom_rail"] {

        position: fixed !important;

        top: 0 !important;

        left: 0 !important;

        bottom: 0 !important;

        width: 64px !important;

        height: 100dvh !important;

        min-width: 64px !important;

        max-width: 64px !important;

        box-sizing: border-box !important;

        padding: 16px 10px !important;

        margin: 0 !important;

        background: #FFFFFF !important;

        border-right: 1px solid #E8E1F2 !important;

        box-shadow:
            2px 0 12px
            rgba(82, 63, 130, 0.035) !important;

        z-index: 999999 !important;

        overflow: hidden !important;
    }


    body:has([class*="st-key-custom_rail"])
    .block-container {

        padding-left: 86px !important;

        padding-right: 42px !important;
    }


    /* ======================================================
       CLOSED RAIL HAMBURGER
       ====================================================== */

    [class*="st-key-custom_rail"]
    [class*="st-key-rail_open_button"] {

        width: 40px !important;

        height: 40px !important;

        margin: 0 0 20px 0 !important;

        padding: 0 !important;
    }


    [class*="st-key-custom_rail"]
    [class*="st-key-rail_open_button"] button {

        width: 40px !important;

        height: 40px !important;

        min-width: 40px !important;

        min-height: 40px !important;

        padding: 0 !important;

        margin: 0 !important;

        background: #F3EEFF !important;

        background-color: #F3EEFF !important;

        color: #7354D7 !important;

        border: 1px solid #D8C9F5 !important;

        border-radius: 10px !important;

        box-shadow:
            0 4px 12px
            rgba(115, 84, 215, 0.10) !important;

        display: flex !important;

        align-items: center !important;

        justify-content: center !important;
    }


    [class*="st-key-custom_rail"]
    [class*="st-key-rail_open_button"] button:hover {

        background: #EAE1FF !important;

        background-color: #EAE1FF !important;

        border-color: #C5B1EF !important;

        color: #6547C9 !important;
    }


    [class*="st-key-custom_rail"]
    [class*="st-key-rail_open_button"] button p {

        margin: 0 !important;

        padding: 0 !important;

        color: #7354D7 !important;

        font-size: 19px !important;

        font-weight: 800 !important;

        line-height: 1 !important;
    }


    /* ======================================================
       RAIL BUTTONS
       ====================================================== */

    [class*="st-key-custom_rail"]
    [class*="st-key-rail_workspace"],
    [class*="st-key-custom_rail"]
    [class*="st-key-rail_search"],
    [class*="st-key-custom_rail"]
    [class*="st-key-rail_notes"],
    [class*="st-key-custom_rail"]
    [class*="st-key-rail_explain"],
    [class*="st-key-custom_rail"]
    [class*="st-key-rail_research"],
    [class*="st-key-custom_rail"]
    [class*="st-key-rail_revision"] {

        width: 40px !important;

        height: 40px !important;

        margin: 0 0 10px 0 !important;

        padding: 0 !important;
    }


    [class*="st-key-custom_rail"]
    [class*="st-key-rail_workspace"] button,
    [class*="st-key-custom_rail"]
    [class*="st-key-rail_search"] button,
    [class*="st-key-custom_rail"]
    [class*="st-key-rail_notes"] button,
    [class*="st-key-custom_rail"]
    [class*="st-key-rail_explain"] button,
    [class*="st-key-custom_rail"]
    [class*="st-key-rail_research"] button,
    [class*="st-key-custom_rail"]
    [class*="st-key-rail_revision"] button {

        width: 40px !important;

        height: 40px !important;

        min-width: 40px !important;

        min-height: 40px !important;

        padding: 0 !important;

        margin: 0 !important;

        background: #F3EEFF !important;

        background-color: #F3EEFF !important;

        color: #7354D7 !important;

        border: 1px solid #D8C9F5 !important;

        border-radius: 11px !important;

        box-shadow:
            0 3px 10px
            rgba(115, 84, 215, 0.08) !important;

        display: flex !important;

        align-items: center !important;

        justify-content: center !important;
    }


    [class*="st-key-custom_rail"]
    [class*="st-key-rail_workspace"] button:hover,
    [class*="st-key-custom_rail"]
    [class*="st-key-rail_search"] button:hover,
    [class*="st-key-custom_rail"]
    [class*="st-key-rail_notes"] button:hover,
    [class*="st-key-custom_rail"]
    [class*="st-key-rail_explain"] button:hover,
    [class*="st-key-custom_rail"]
    [class*="st-key-rail_research"] button:hover,
    [class*="st-key-custom_rail"]
    [class*="st-key-rail_revision"] button:hover {

        background: #EAE1FF !important;

        background-color: #EAE1FF !important;

        border-color: #C5B1EF !important;

        color: #6547C9 !important;
    }


    [class*="st-key-custom_rail"]
    [class*="st-key-rail_workspace"] button p,
    [class*="st-key-custom_rail"]
    [class*="st-key-rail_search"] button p,
    [class*="st-key-custom_rail"]
    [class*="st-key-rail_notes"] button p,
    [class*="st-key-custom_rail"]
    [class*="st-key-rail_explain"] button p,
    [class*="st-key-custom_rail"]
    [class*="st-key-rail_research"] button p,
    [class*="st-key-custom_rail"]
    [class*="st-key-rail_revision"] button p {

        margin: 0 !important;

        padding: 0 !important;

        color: #7354D7 !important;

        font-size: 17px !important;

        line-height: 1 !important;
    }


    /* ======================================================
       WELCOME CARD
       ====================================================== */

    .welcome-card {

        width: 100%;

        box-sizing: border-box;

        padding: 27px 34px;

        background: #FFFFFF;

        border: 1px solid #E8E1F2;

        border-radius: 17px;

        box-shadow:
            0 5px 18px
            rgba(85, 65, 135, 0.035);
    }

    .welcome-title {

        margin-bottom: 8px;

        color: #7055D4;

        font-size: 30px;

        font-weight: 800;

        line-height: 1.15;
    }

    .welcome-text {

        max-width: 1100px;

        color: #858091;

        font-size: 13px;

        line-height: 1.55;
    }


    /* ======================================================
       STATUS
       ====================================================== */

    .status-card {

        display: flex;

        align-items: center;

        gap: 11px;

        width: 100%;

        box-sizing: border-box;

        padding: 11px 15px;

        background: #FFFFFF;

        border: 1px solid #E8E1F2;

        border-radius: 12px;
    }

    .status-dot {

        width: 8px;

        height: 8px;

        flex-shrink: 0;

        border-radius: 50%;

        background: #46C995;

        box-shadow:
            0 0 0 4px
            rgba(70, 201, 149, 0.12);
    }

    .status-text {

        color: #777080;

        font-size: 12px;
    }


    /* ======================================================
       ACTION CARDS
       ====================================================== */

    .action-card {

        min-height: 148px;

        height: 100%;

        box-sizing: border-box;

        padding: 17px;

        background: #FFFFFF;

        border: 1px solid #E8E1F2;

        border-radius: 15px;

        box-shadow:
            0 4px 16px
            rgba(85, 65, 135, 0.035);

        transition:
            transform 0.15s ease,
            box-shadow 0.15s ease,
            border-color 0.15s ease;
    }

    .action-card:hover {

        transform: translateY(-2px);

        border-color: #D8CCF2;

        box-shadow:
            0 8px 22px
            rgba(85, 65, 135, 0.07);
    }

    .action-icon {

        font-size: 21px;

        line-height: 1;
    }

    .action-title {

        margin-top: 8px;

        color: #40394D;

        font-size: 13px;

        font-weight: 700;
    }

    .action-description {

        margin-top: 5px;

        color: #8C8597;

        font-size: 11px;

        line-height: 1.45;
    }


    /* ======================================================
       PROMPT HINT
       ====================================================== */

    .prompt-hint {

        padding: 0 8px;

        color: #9A93A5;

        font-size: 11px;

        line-height: 1.4;

        text-align: center;
    }

    .prompt-hint strong {

        color: #756B82;

        font-weight: 600;
    }


    /* ======================================================
       CHAT MESSAGES
       ====================================================== */

    [data-testid="stChatMessage"] {

        margin-bottom: 10px !important;

        background: #FFFFFF !important;

        border: 1px solid #E8E1F2 !important;

        border-radius: 15px !important;

        box-shadow:
            0 3px 12px
            rgba(85, 65, 135, 0.025) !important;
    }

    [data-testid="stChatMessageContent"] {

        color: #393342 !important;

        font-size: 14px !important;

        line-height: 1.65 !important;
    }


    /* ======================================================
       CHAT INPUT

       FINAL FIX:
       The custom sidebar is fixed at 290px on the left.
       The bottom chat area must therefore occupy ONLY the
       remaining viewport width.

       Do NOT use calc(50% + ...), translateX(), or an invalid
       margin-right value here. Those were causing the input
       to overflow/crop on the right.
       ====================================================== */

    [data-testid="stBottom"] {

        position: fixed !important;

        left: 290px !important;

        right: 0 !important;

        bottom: 0 !important;

        width: auto !important;

        max-width: none !important;

        box-sizing: border-box !important;

        background: #F8F6FC !important;

        background-color: #F8F6FC !important;

        border-top: 1px solid #E8E1F2 !important;

        box-shadow: none !important;

        padding-top: 7px !important;

        padding-bottom: 12px !important;

        padding-left: 0 !important;

        padding-right: 0 !important;
    }

    [data-testid="stBottom"] > div {

        width: 100% !important;

        max-width: none !important;

        box-sizing: border-box !important;

        background: #F8F6FC !important;

        background-color: #F8F6FC !important;

        box-shadow: none !important;
    }

    [data-testid="stBottom"] [data-testid="stChatInput"] {

        width: min(980px, calc(100% - 80px)) !important;

        max-width: 980px !important;

        box-sizing: border-box !important;

        margin-left: auto !important;

        margin-right: auto !important;

        transform: none !important;
    }

    [data-testid="stBottom"] [data-testid="stChatInput"] > div {

        width: 100% !important;

        box-sizing: border-box !important;

        background: #FFFFFF !important;

        background-color: #FFFFFF !important;

        border: 1px solid #DCD3ED !important;

        border-radius: 16px !important;

        box-shadow:
            0 6px 20px
            rgba(80, 60, 130, 0.07) !important;
    }

    [data-testid="stBottom"] [data-testid="stChatInput"] textarea {

        background: #FFFFFF !important;

        background-color: #FFFFFF !important;

        color: #302A3C !important;

        font-size: 14px !important;
    }

    [data-testid="stBottom"] [data-testid="stChatInput"] textarea::placeholder {

        color: #A29BAB !important;
    }


    /* ======================================================
       PURPLE CHAT INPUT BUTTON
       ====================================================== */

    [data-testid="stBottom"] [data-testid="stChatInput"] button {

        background: #F3EEFF !important;

        background-color: #F3EEFF !important;

        border: 1px solid #D8C9F5 !important;

        color: #7354D7 !important;

        box-shadow: none !important;
    }

    [data-testid="stBottom"] [data-testid="stChatInput"] button:hover {

        background: #EAE1FF !important;

        background-color: #EAE1FF !important;

        border-color: #C5B1EF !important;

        color: #6547C9 !important;
    }

    [data-testid="stBottom"] [data-testid="stChatInput"] button svg {

        color: #7354D7 !important;

        stroke: #7354D7 !important;
    }


    /* ======================================================
       DOCUMENT STATUS
       ====================================================== */

    .document-status {

        width: min(980px, 90%);

        box-sizing: border-box;

        margin: 0 auto 7px auto;

        padding: 7px 12px;

        background: #F3EEFF;

        border: 1px solid #DED3F3;

        border-radius: 10px;

        color: #6D55C5;

        font-size: 11px;

        line-height: 1.3;
    }

    .document-status strong {

        color: #5840B5;
    }


    /* ======================================================
       NOTES
       ====================================================== */

    .notes-toolbar {

        display: flex;

        align-items: center;

        justify-content: space-between;

        gap: 12px;

        width: 100%;

        box-sizing: border-box;

        margin: 0 0 14px 0;

        padding: 12px 14px;

        background: #FFFFFF;

        border: 1px solid #E8E1F2;

        border-radius: 12px;

        box-shadow:
            0 3px 12px
            rgba(85, 65, 135, 0.025);
    }

    .notes-count {

        color: #777080;

        font-size: 12px;

        line-height: 1.35;
    }

    .notes-count strong {

        color: #5B4A82;

        font-weight: 800;
    }

    .note-text-wrap {

        min-width: 0;

        width: 100%;

        box-sizing: border-box;
    }

    .note-number {

        display: inline-block;

        margin-bottom: 7px;

        color: #765DD5;

        font-size: 11px;

        font-weight: 800;

        letter-spacing: 0.7px;
    }

    .note-text {

        color: #514A5D;

        font-size: 13px;

        line-height: 1.65;

        white-space: pre-wrap;

        overflow-wrap: anywhere;

        word-break: normal;

        max-width: 100%;

        box-sizing: border-box;
    }

    /* Each complete note is a single visual card. */
    [class*="st-key-note_item_"] {

        width: 100% !important;

        max-width: 100% !important;

        min-width: 0 !important;

        box-sizing: border-box !important;

        margin: 0 0 11px 0 !important;

        padding: 14px 14px 14px 16px !important;

        background: #FFFFFF !important;

        border: 1px solid #E8E1F2 !important;

        border-left: 4px solid #9277E4 !important;

        border-radius: 13px !important;

        box-shadow:
            0 3px 12px
            rgba(85, 65, 135, 0.025) !important;
    }

    [class*="st-key-note_item_"] > div {

        min-width: 0 !important;

        max-width: 100% !important;

        box-sizing: border-box !important;
    }

    /* Keep the note and delete button on one row on desktop. */
    [class*="st-key-note_item_"] [data-testid="stHorizontalBlock"] {

        width: 100% !important;

        max-width: 100% !important;

        min-width: 0 !important;

        flex-wrap: nowrap !important;

        align-items: flex-start !important;

        gap: 12px !important;

        box-sizing: border-box !important;
    }

    [class*="st-key-note_item_"] [data-testid="column"] {

        min-width: 0 !important;

        box-sizing: border-box !important;
    }

    [class*="st-key-note_item_"] [data-testid="column"]:last-child {

        flex: 0 0 42px !important;

        width: 42px !important;

        max-width: 42px !important;

        min-width: 42px !important;
    }

    /* Single-note delete button. */
    [class*="st-key-note_item_"] [data-testid="stButton"] {

        width: 42px !important;

        margin: 0 !important;

    }

    [class*="st-key-note_item_"] [data-testid="stButton"] button {

        width: 42px !important;

        height: 38px !important;

        min-height: 38px !important;

        padding: 0 !important;

        margin: 0 !important;

        background: #FFF7F8 !important;

        background-color: #FFF7F8 !important;

        color: #B75C70 !important;

        border: 1px solid #F0CDD5 !important;

        border-radius: 9px !important;

        box-shadow: none !important;

        font-size: 15px !important;

        font-weight: 700 !important;

    }

    [class*="st-key-note_item_"] [data-testid="stButton"] button:hover {

        background: #FDECEF !important;

        background-color: #FDECEF !important;

        color: #9D4056 !important;

        border-color: #E5AAB8 !important;

    }

    /* Clear-all confirmation box. */
    .clear-notes-confirm {

        width: 100%;

        box-sizing: border-box;

        margin: 0 0 14px 0;

        padding: 13px 14px;

        background: #FFF9FA;

        border: 1px solid #F0CDD5;

        border-radius: 12px;

        color: #6D4650;

        font-size: 12px;

        line-height: 1.45;
    }

    .clear-notes-confirm strong {

        color: #8E3E51;

        font-weight: 800;
    }

    /* Clear-all button. */
    [class*="st-key-clear_all_notes"] button {

        min-height: 38px !important;

        padding: 7px 13px !important;

        background: #FFF7F8 !important;

        background-color: #FFF7F8 !important;

        color: #A3485F !important;

        border: 1px solid #EBC5CE !important;

        border-radius: 9px !important;

        font-size: 11px !important;

        font-weight: 700 !important;

        box-shadow: none !important;
    }

    [class*="st-key-clear_all_notes"] button:hover {

        background: #FDECEF !important;

        background-color: #FDECEF !important;

        color: #8E344A !important;

        border-color: #E1A4B2 !important;
    }

    [class*="st-key-confirm_clear_notes"] button {

        min-height: 38px !important;

        padding: 7px 12px !important;

        border-radius: 9px !important;

        font-size: 11px !important;

        font-weight: 700 !important;
    }


    /* ======================================================
       STREAMLIT SPACING
       ====================================================== */

    .main .element-container {

        margin-bottom: 0 !important;
    }

    .main [data-testid="stVerticalBlock"] {

        gap: 0.25rem !important;
    }

    .main [data-testid="stHorizontalBlock"] {

        gap: 1rem !important;
    }


    /* ======================================================
       RESPONSIVE — MOBILE
       ====================================================== */

    @media (max-width: 900px) {

        /* --------------------------------------------------
           MOBILE MAIN AREA
           -------------------------------------------------- */

        .block-container {
            width: 100% !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
            padding-top: 12px !important;
            padding-right: 14px !important;
            padding-bottom: 145px !important;
            overflow-x: hidden !important;
        }


        /* --------------------------------------------------
           OPEN SIDEBAR = OVERLAY, NOT A COLUMN

           This is the main fix.

           Previously the sidebar stayed fixed at 260px and
           the main content kept 278px left padding. On a
           phone that leaves only a tiny strip for the app.

           Now the sidebar sits OVER the page like ChatGPT's
           mobile drawer.
           -------------------------------------------------- */

        [class*="st-key-custom_sidebar"] {
            width: min(320px, 86vw) !important;
            min-width: min(320px, 86vw) !important;
            max-width: min(320px, 86vw) !important;

            top: 0 !important;
            left: 0 !important;
            bottom: 0 !important;

            height: 100dvh !important;
            max-height: 100dvh !important;

            padding: 12px 16px 24px 16px !important;

            z-index: 1000000 !important;

            overflow-y: auto !important;
            overflow-x: hidden !important;

            box-shadow:
                8px 0 28px
                rgba(55, 40, 95, 0.16) !important;
        }


        body:has([class*="st-key-custom_sidebar"])
        .block-container {
            width: 100% !important;
            max-width: 100% !important;

            padding-left: 14px !important;
            padding-right: 14px !important;

            margin-left: 0 !important;
            margin-right: 0 !important;
        }


        /* Keep sidebar contents inside the drawer. */

        [class*="st-key-custom_sidebar"] > div,
        [class*="st-key-custom_sidebar"] [data-testid="stVerticalBlock"] {
            width: 100% !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
        }


        /* --------------------------------------------------
           CLOSED RAIL
           -------------------------------------------------- */

        [class*="st-key-custom_rail"] {
            width: 64px !important;
            min-width: 64px !important;
            max-width: 64px !important;

            top: 0 !important;
            left: 0 !important;
            bottom: 0 !important;

            height: 100dvh !important;

            padding: 14px 8px !important;

            z-index: 1000000 !important;
        }


        body:has([class*="st-key-custom_rail"])
        .block-container {
            width: 100% !important;
            max-width: 100% !important;

            padding-left: 78px !important;
            padding-right: 14px !important;

            margin-left: 0 !important;
            margin-right: 0 !important;
        }


        /* --------------------------------------------------
           HAMBURGER
           -------------------------------------------------- */

        [class*="st-key-custom_sidebar"]
        [class*="st-key-close_sidebar_button"] {
            margin-bottom: 18px !important;
        }


        /* --------------------------------------------------
           BRAND
           -------------------------------------------------- */

        .brand-wrapper {
            gap: 10px !important;
            margin-bottom: 24px !important;
        }

        .brand-icon {
            width: 46px !important;
            height: 46px !important;
            border-radius: 13px !important;
            font-size: 20px !important;
        }

        .brand-title {
            font-size: 18px !important;
        }

        .brand-subtitle {
            font-size: 9px !important;
        }


        /* --------------------------------------------------
           HOME CARDS

           Force the four cards to use the full mobile width
           instead of allowing four narrow columns to squeeze
           beside each other.
           -------------------------------------------------- */

        [data-testid="stHorizontalBlock"] {
            width: 100% !important;
            max-width: 100% !important;
            box-sizing: border-box !important;

            flex-wrap: wrap !important;
        }

        [data-testid="stHorizontalBlock"] > [data-testid="column"] {
            min-width: 100% !important;
            width: 100% !important;
            max-width: 100% !important;
            flex: 1 1 100% !important;

            box-sizing: border-box !important;
        }

        .action-card {
            width: 100% !important;
            min-height: 0 !important;
            height: auto !important;
            padding: 18px !important;
            margin-bottom: 10px !important;
            box-sizing: border-box !important;
        }

        .action-icon {
            font-size: 22px !important;
        }

        .action-title {
            font-size: 15px !important;
            margin-top: 9px !important;
        }

        .action-description {
            font-size: 12px !important;
            line-height: 1.5 !important;
        }


        /* --------------------------------------------------
           WELCOME / STATUS
           -------------------------------------------------- */

        .welcome-card {
            width: 100% !important;
            padding: 20px !important;
            border-radius: 15px !important;
            box-sizing: border-box !important;
        }

        .welcome-title {
            font-size: 24px !important;
        }

        .welcome-text {
            font-size: 12px !important;
            line-height: 1.5 !important;
        }

        .status-card {
            width: 100% !important;
            padding: 10px 13px !important;
        }

        .status-text {
            font-size: 11px !important;
        }

        .prompt-hint {
            padding: 0 4px !important;
            font-size: 11px !important;
        }


        /* --------------------------------------------------
           CHAT MESSAGES
           -------------------------------------------------- */

        [data-testid="stChatMessage"] {
            width: 100% !important;
            max-width: 100% !important;
            box-sizing: border-box !important;

            margin-bottom: 9px !important;
            border-radius: 14px !important;
        }

        [data-testid="stChatMessageContent"] {
            font-size: 14px !important;
            line-height: 1.55 !important;
            overflow-wrap: anywhere !important;
        }


        /* --------------------------------------------------
           CHAT INPUT

           IMPORTANT:
           On mobile it must use the whole viewport.
           The old left: 290px permanently removed ~290px
           from the phone width.
           -------------------------------------------------- */

        [data-testid="stBottom"] {
            left: 0 !important;
            right: 0 !important;
            width: 100% !important;

            padding: 7px 10px 10px 10px !important;

            box-sizing: border-box !important;
            z-index: 999998 !important;
        }

        [data-testid="stBottom"] > div {
            width: 100% !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
        }

        [data-testid="stBottom"] [data-testid="stChatInput"] {
            width: 100% !important;
            max-width: 100% !important;

            margin: 0 !important;
            box-sizing: border-box !important;

            transform: none !important;
        }

        [data-testid="stBottom"] [data-testid="stChatInput"] > div {
            width: 100% !important;
            max-width: 100% !important;
            box-sizing: border-box !important;

            border-radius: 15px !important;
        }

        [data-testid="stBottom"] [data-testid="stChatInput"] textarea {
            font-size: 14px !important;
        }


        /* --------------------------------------------------
           DOCUMENT STATUS
           -------------------------------------------------- */

        .document-status {
            width: 100% !important;
            max-width: 100% !important;
            margin-left: 0 !important;
            margin-right: 0 !important;

            box-sizing: border-box !important;

            overflow-wrap: anywhere !important;
        }


        /* --------------------------------------------------
           NOTES
           -------------------------------------------------- */

        .note-card {
            width: 100% !important;
            box-sizing: border-box !important;
            overflow-wrap: anywhere !important;
        }
    }


    /* ======================================================
       EXTRA SMALL PHONES
       ====================================================== */

    @media (max-width: 480px) {

        .block-container {
            padding-left: 10px !important;
            padding-right: 10px !important;
            padding-bottom: 140px !important;
        }

        body:has([class*="st-key-custom_sidebar"])
        .block-container {
            padding-left: 10px !important;
            padding-right: 10px !important;
        }

        body:has([class*="st-key-custom_rail"])
        .block-container {
            padding-left: 76px !important;
            padding-right: 10px !important;
        }

        [class*="st-key-custom_sidebar"] {
            width: 86vw !important;
            min-width: 86vw !important;
            max-width: 86vw !important;
        }

        .welcome-card {
            padding: 17px !important;
        }

        .welcome-title {
            font-size: 22px !important;
        }

        .action-card {
            padding: 16px !important;
        }

        .prompt-hint {
            font-size: 10px !important;
            line-height: 1.55 !important;
        }

        [data-testid="stBottom"] {
            padding-left: 7px !important;
            padding-right: 7px !important;
        }
    }


    /* ======================================================
       FINAL RESPONSIVE ALIGNMENT OVERRIDES
       ------------------------------------------------------
       These rules intentionally come last so they win over
       Streamlit's changing layout styles.
       ====================================================== */

    /* Keep the main Streamlit surface flush with the viewport.
       The custom rail itself is fixed and must not create an
       extra hidden left offset. */
    main,
    [data-testid="stAppViewContainer"] main {
        margin-left: 0 !important;
        padding-left: 0 !important;
        width: 100% !important;
        max-width: 100% !important;
    }

    .main .block-container,
    [data-testid="stAppViewContainer"] .block-container {
        margin-left: 0 !important;
        margin-right: 0 !important;
        max-width: none !important;
    }

    /* ======================================================
       CLOSED RAIL — DESKTOP
       ====================================================== */

    [class*="st-key-custom_rail"] {
        width: 72px !important;
        min-width: 72px !important;
        max-width: 72px !important;
        padding-left: 12px !important;
        padding-right: 12px !important;
    }

    body:has([class*="st-key-custom_rail"]) .block-container {
        padding-left: 96px !important;
        padding-right: 42px !important;
    }

    /* ======================================================
       OPEN SIDEBAR — DESKTOP
       ====================================================== */

    [class*="st-key-custom_sidebar"] {
        width: 290px !important;
        min-width: 290px !important;
        max-width: 290px !important;
    }

    body:has([class*="st-key-custom_sidebar"]) .block-container {
        padding-left: 332px !important;
        padding-right: 42px !important;
    }

    /* ======================================================
       BOTTOM CHAT BAR — DESKTOP
       ====================================================== */

    [data-testid="stBottom"] {
        left: 290px !important;
        right: 0 !important;
        width: auto !important;
    }

    body:has([class*="st-key-custom_rail"]) [data-testid="stBottom"] {
        left: 72px !important;
    }

    /* ======================================================
       MOBILE
       ====================================================== */

    @media (max-width: 900px) {

        html,
        body,
        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stAppViewContainer"] > .main,
        main {
            width: 100% !important;
            max-width: 100% !important;
            min-width: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
            overflow-x: hidden !important;
        }

        .main .block-container,
        [data-testid="stAppViewContainer"] .block-container {
            width: 100% !important;
            max-width: 100% !important;
            min-width: 0 !important;
            margin: 0 !important;
            box-sizing: border-box !important;
            padding-top: 12px !important;
            padding-right: 14px !important;
            padding-bottom: 175px !important;
            padding-left: 76px !important;
        }

        /* Compact ChatGPT-like rail. */
        [class*="st-key-custom_rail"] {
            top: 0 !important;
            left: 0 !important;
            bottom: 0 !important;

            width: 64px !important;
            min-width: 64px !important;
            max-width: 64px !important;

            height: 100dvh !important;
            max-height: 100dvh !important;

            padding: 16px 10px !important;
            margin: 0 !important;

            box-sizing: border-box !important;
            overflow: hidden !important;
            z-index: 1000000 !important;
        }

        /* Make every rail button actually fit inside 64px. */
        [class*="st-key-custom_rail"] [class*="st-key-rail_open_button"],
        [class*="st-key-custom_rail"] [class*="st-key-rail_workspace"],
        [class*="st-key-custom_rail"] [class*="st-key-rail_search"],
        [class*="st-key-custom_rail"] [class*="st-key-rail_notes"],
        [class*="st-key-custom_rail"] [class*="st-key-rail_explain"],
        [class*="st-key-custom_rail"] [class*="st-key-rail_research"],
        [class*="st-key-custom_rail"] [class*="st-key-rail_revision"] {
            width: 44px !important;
            max-width: 44px !important;
            min-width: 44px !important;
            height: 44px !important;
            margin-left: 0 !important;
            margin-right: 0 !important;
        }

        [class*="st-key-custom_rail"] button {
            width: 44px !important;
            min-width: 44px !important;
            max-width: 44px !important;
            height: 44px !important;
            min-height: 44px !important;
            max-height: 44px !important;
            box-sizing: border-box !important;
        }

        body:has([class*="st-key-custom_rail"]) .block-container {
            padding-left: 76px !important;
            padding-right: 14px !important;
        }

        /* Main cards occupy only the real content area. */
        [data-testid="stHorizontalBlock"] {
            width: 100% !important;
            max-width: 100% !important;
            margin-left: 0 !important;
            margin-right: 0 !important;
            box-sizing: border-box !important;
        }

        [data-testid="stHorizontalBlock"] > [data-testid="column"] {
            width: 100% !important;
            min-width: 100% !important;
            max-width: 100% !important;
            flex: 1 1 100% !important;
            box-sizing: border-box !important;
        }

        .welcome-card,
        .status-card,
        .action-card,
        .prompt-hint,
        [data-testid="stChatMessage"],
        .document-status,
        .note-card {
            max-width: 100% !important;
            box-sizing: border-box !important;
        }

        /* The fixed composer aligns with the content edge,
           not with the browser's full left edge. */
        [data-testid="stBottom"] {
            left: 64px !important;
            right: 0 !important;
            width: auto !important;
            max-width: none !important;

            padding: 7px 10px 10px 0 !important;
            box-sizing: border-box !important;
        }

        [data-testid="stBottom"] > div {
            width: 100% !important;
            max-width: 100% !important;
            margin: 0 !important;
            box-sizing: border-box !important;
        }

        [data-testid="stBottom"] [data-testid="stChatInput"] {
            width: 100% !important;
            max-width: 100% !important;
            margin: 0 !important;
            box-sizing: border-box !important;
        }

        /* Prevent the example prompt from disappearing under
           the fixed composer. */
        .prompt-hint {
            margin-bottom: 18px !important;
            padding-bottom: 8px !important;
        }

        /* Open drawer is an overlay. It does not alter the
           underlying page width. */
        [class*="st-key-custom_sidebar"] {
            top: 0 !important;
            left: 0 !important;
            bottom: 0 !important;

            width: min(320px, 86vw) !important;
            min-width: min(320px, 86vw) !important;
            max-width: min(320px, 86vw) !important;

            height: 100dvh !important;
            max-height: 100dvh !important;

            box-sizing: border-box !important;
            z-index: 1000001 !important;
        }

        body:has([class*="st-key-custom_sidebar"]) .block-container {
            padding-left: 14px !important;
            padding-right: 14px !important;
        }

        body:has([class*="st-key-custom_sidebar"]) [data-testid="stBottom"] {
            left: 0 !important;
            right: 0 !important;
            padding-left: 10px !important;
            padding-right: 10px !important;
        }
    }

    @media (max-width: 480px) {

        .main .block-container,
        [data-testid="stAppViewContainer"] .block-container {
            padding-left: 72px !important;
            padding-right: 10px !important;
            padding-bottom: 175px !important;
        }

        body:has([class*="st-key-custom_rail"]) .block-container {
            padding-left: 72px !important;
            padding-right: 10px !important;
        }

        [class*="st-key-custom_rail"] {
            width: 60px !important;
            min-width: 60px !important;
            max-width: 60px !important;
            padding-left: 8px !important;
            padding-right: 8px !important;
        }

        [class*="st-key-custom_rail"] [class*="st-key-rail_open_button"],
        [class*="st-key-custom_rail"] [class*="st-key-rail_workspace"],
        [class*="st-key-custom_rail"] [class*="st-key-rail_search"],
        [class*="st-key-custom_rail"] [class*="st-key-rail_notes"],
        [class*="st-key-custom_rail"] [class*="st-key-rail_explain"],
        [class*="st-key-custom_rail"] [class*="st-key-rail_research"],
        [class*="st-key-custom_rail"] [class*="st-key-rail_revision"],
        [class*="st-key-custom_rail"] button {
            width: 44px !important;
            min-width: 44px !important;
            max-width: 44px !important;
            height: 44px !important;
            min-height: 44px !important;
            max-height: 44px !important;
        }

        body:has([class*="st-key-custom_rail"]) [data-testid="stBottom"] {
            left: 60px !important;
        }

        body:has([class*="st-key-custom_sidebar"]) [data-testid="stBottom"] {
            left: 0 !important;
        }
    }

    
    /* ======================================================
       FINAL UI / RESPONSIVE FIXES
       These rules are intentionally LAST.
       They fix the real problems visible on desktop + phone:
       - mobile rail must stay 64px, not grow to ~118px
       - page must use the remaining mobile width
       - long PDF answers/tables/code must never widen the page
       - fixed composer must span the full available width
       - desktop closed rail composer must span full content width
       - opening the drawer must be an overlay on mobile
       ====================================================== */

    /* Never allow the document itself to become horizontally wider
       than the viewport. */
    html,
    body,
    #root,
    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stAppViewContainer"] > .main,
    main {
        max-width: 100vw !important;
        min-width: 0 !important;
        overflow-x: hidden !important;
    }

    /* All Streamlit content wrappers must be allowed to shrink. */
    [data-testid="stVerticalBlock"],
    [data-testid="stHorizontalBlock"],
    [data-testid="column"],
    .element-container,
    [data-testid="stMarkdown"],
    [data-testid="stMarkdownContainer"] {
        min-width: 0 !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
    }

    /* ======================================================
       DESKTOP CLOSED RAIL
       ====================================================== */

    @media (min-width: 901px) {

        [class*="st-key-custom_rail"] {
            position: fixed !important;
            left: 0 !important;
            top: 0 !important;
            bottom: 0 !important;

            width: 72px !important;
            min-width: 72px !important;
            max-width: 72px !important;
            flex: 0 0 72px !important;

            height: 100vh !important;
            padding: 16px 12px !important;
            margin: 0 !important;

            box-sizing: border-box !important;
            overflow: hidden !important;
            z-index: 1000000 !important;
        }

        body:has([class*="st-key-custom_rail"]) .block-container {
            width: 100% !important;
            max-width: none !important;
            margin: 0 !important;
            padding-left: 96px !important;
            padding-right: 42px !important;
            box-sizing: border-box !important;
        }

        /* Closed-rail composer = the entire available content width. */
        body:has([class*="st-key-custom_rail"]) [data-testid="stBottom"] {
            left: 72px !important;
            right: 0 !important;
            width: auto !important;
            max-width: none !important;
            box-sizing: border-box !important;
            padding-left: 0 !important;
            padding-right: 0 !important;
        }

        body:has([class*="st-key-custom_rail"]) [data-testid="stBottom"] [data-testid="stChatInput"] {
            width: calc(100% - 84px) !important;
            max-width: none !important;
            margin-left: auto !important;
            margin-right: auto !important;
            box-sizing: border-box !important;
        }

        /* Open sidebar desktop: content starts after the drawer. */
        [class*="st-key-custom_sidebar"] {
            width: 290px !important;
            min-width: 290px !important;
            max-width: 290px !important;
            flex: 0 0 290px !important;
            box-sizing: border-box !important;
        }

        body:has([class*="st-key-custom_sidebar"]) .block-container {
            width: 100% !important;
            max-width: none !important;
            margin: 0 !important;
            padding-left: 332px !important;
            padding-right: 42px !important;
            box-sizing: border-box !important;
        }

        body:has([class*="st-key-custom_sidebar"]) [data-testid="stBottom"] {
            left: 290px !important;
            right: 0 !important;
            width: auto !important;
            max-width: none !important;
            box-sizing: border-box !important;
        }

        body:has([class*="st-key-custom_sidebar"]) [data-testid="stBottom"] [data-testid="stChatInput"] {
            width: calc(100% - 84px) !important;
            max-width: none !important;
            margin-left: auto !important;
            margin-right: auto !important;
            box-sizing: border-box !important;
        }
    }

    /* ======================================================
       MOBILE — REAL CHATGPT-LIKE RAIL
       ====================================================== */

    @media (max-width: 900px) {

        /* The viewport is the coordinate system. */
        html,
        body,
        #root,
        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stAppViewContainer"] > .main,
        main {
            width: 100% !important;
            max-width: 100vw !important;
            min-width: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
            overflow-x: hidden !important;
        }

        /* --------------------------------------------------
           CLOSED RAIL
           Exactly 64px wide. No flex growth.
           -------------------------------------------------- */
        [class*="st-key-custom_rail"] {
            position: fixed !important;
            left: 0 !important;
            top: 0 !important;
            bottom: 0 !important;

            width: 64px !important;
            min-width: 64px !important;
            max-width: 64px !important;
            flex: 0 0 64px !important;

            height: 100dvh !important;
            min-height: 100dvh !important;
            max-height: 100dvh !important;

            margin: 0 !important;
            padding: 16px 8px !important;

            box-sizing: border-box !important;
            overflow: hidden !important;
            z-index: 1000000 !important;
        }

        /* Every rail control fits inside the 64px rail. */
        [class*="st-key-custom_rail"] [class*="st-key-rail_open_button"],
        [class*="st-key-custom_rail"] [class*="st-key-rail_workspace"],
        [class*="st-key-custom_rail"] [class*="st-key-rail_search"],
        [class*="st-key-custom_rail"] [class*="st-key-rail_notes"],
        [class*="st-key-custom_rail"] [class*="st-key-rail_explain"],
        [class*="st-key-custom_rail"] [class*="st-key-rail_research"],
        [class*="st-key-custom_rail"] [class*="st-key-rail_revision"] {
            width: 48px !important;
            min-width: 48px !important;
            max-width: 48px !important;
            height: 48px !important;
            min-height: 48px !important;
            max-height: 48px !important;
            margin-left: 0 !important;
            margin-right: 0 !important;
            box-sizing: border-box !important;
        }

        [class*="st-key-custom_rail"] button {
            width: 48px !important;
            min-width: 48px !important;
            max-width: 48px !important;
            height: 48px !important;
            min-height: 48px !important;
            max-height: 48px !important;
            margin-left: 0 !important;
            margin-right: 0 !important;
            box-sizing: border-box !important;
        }

        /* --------------------------------------------------
           MOBILE CONTENT
           -------------------------------------------------- */
        .main .block-container,
        [data-testid="stAppViewContainer"] .block-container {
            width: 100% !important;
            max-width: 100% !important;
            min-width: 0 !important;

            margin: 0 !important;

            padding-top: 12px !important;
            padding-left: 76px !important;
            padding-right: 12px !important;
            padding-bottom: 175px !important;

            box-sizing: border-box !important;
            overflow-x: hidden !important;
        }

        body:has([class*="st-key-custom_rail"]) .block-container {
            width: 100% !important;
            max-width: 100% !important;
            padding-left: 76px !important;
            padding-right: 12px !important;
            margin-left: 0 !important;
            margin-right: 0 !important;
        }

        /* --------------------------------------------------
           OPEN DRAWER
           It overlays the page. It NEVER pushes/squeezes the
           content underneath it.
           -------------------------------------------------- */
        [class*="st-key-custom_sidebar"] {
            position: fixed !important;
            left: 0 !important;
            top: 0 !important;
            bottom: 0 !important;

            width: min(320px, 86vw) !important;
            min-width: min(320px, 86vw) !important;
            max-width: min(320px, 86vw) !important;
            flex: 0 0 auto !important;

            height: 100dvh !important;
            min-height: 100dvh !important;
            max-height: 100dvh !important;

            margin: 0 !important;
            padding: 12px 16px 24px 16px !important;

            box-sizing: border-box !important;
            overflow-x: hidden !important;
            overflow-y: auto !important;

            z-index: 1000001 !important;
        }

        body:has([class*="st-key-custom_sidebar"]) .block-container {
            width: 100% !important;
            max-width: 100% !important;
            padding-left: 12px !important;
            padding-right: 12px !important;
            margin: 0 !important;
        }

        /* --------------------------------------------------
           MOBILE COLUMNS
           Never let four home cards become four tiny columns.
           -------------------------------------------------- */
        [data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-wrap: wrap !important;
            width: 100% !important;
            max-width: 100% !important;
            min-width: 0 !important;
            margin: 0 !important;
            box-sizing: border-box !important;
        }

        [data-testid="stHorizontalBlock"] > [data-testid="column"] {
            width: 100% !important;
            min-width: 100% !important;
            max-width: 100% !important;
            flex: 1 1 100% !important;
            box-sizing: border-box !important;
        }

        .welcome-card,
        .status-card,
        .action-card,
        .prompt-hint,
        .note-card,
        .document-status,
        [data-testid="stChatMessage"] {
            width: 100% !important;
            max-width: 100% !important;
            min-width: 0 !important;
            box-sizing: border-box !important;
        }

        /* --------------------------------------------------
           MOBILE LONG ANSWERS / PDFs
           THIS is the fix for the screenshots showing:
           "How it wor..." cut off, code cut off, and
           right-hand content disappearing.

           Text can wrap. Tables become contained. Code scrolls
           INSIDE its box instead of widening the whole page.
           -------------------------------------------------- */
        [data-testid="stChatMessageContent"],
        [data-testid="stChatMessageContent"] > div,
        [data-testid="stChatMessageContent"] p,
        [data-testid="stChatMessageContent"] li,
        [data-testid="stChatMessageContent"] h1,
        [data-testid="stChatMessageContent"] h2,
        [data-testid="stChatMessageContent"] h3,
        [data-testid="stChatMessageContent"] h4,
        [data-testid="stChatMessageContent"] h5,
        [data-testid="stChatMessageContent"] h6 {
            min-width: 0 !important;
            max-width: 100% !important;
            overflow-wrap: anywhere !important;
            word-break: normal !important;
        }

        [data-testid="stChatMessageContent"] table {
            display: block !important;
            width: 100% !important;
            max-width: 100% !important;
            min-width: 0 !important;
            table-layout: fixed !important;
            overflow-x: auto !important;
            box-sizing: border-box !important;
        }

        [data-testid="stChatMessageContent"] th,
        [data-testid="stChatMessageContent"] td {
            max-width: 0 !important;
            min-width: 0 !important;
            padding: 8px 7px !important;
            white-space: normal !important;
            overflow-wrap: anywhere !important;
            word-break: break-word !important;
            box-sizing: border-box !important;
        }

        /* Code must remain readable and may scroll horizontally
           inside the code block, but the page itself never scrolls. */
        [data-testid="stChatMessageContent"] pre,
        [data-testid="stChatMessageContent"] code,
        [data-testid="stCode"],
        [data-testid="stCodeBlock"] {
            max-width: 100% !important;
            min-width: 0 !important;
            box-sizing: border-box !important;
        }

        [data-testid="stChatMessageContent"] pre {
            width: 100% !important;
            overflow-x: auto !important;
            overflow-y: hidden !important;
            white-space: pre !important;
            font-size: 12px !important;
            line-height: 1.5 !important;
        }

        /* Images generated/rendered inside an answer can never
           exceed the phone. */
        [data-testid="stChatMessageContent"] img,
        [data-testid="stChatMessageContent"] video,
        [data-testid="stChatMessageContent"] iframe {
            max-width: 100% !important;
            height: auto !important;
            box-sizing: border-box !important;
        }

        /* --------------------------------------------------
           MOBILE COMPOSER
           Full remaining width, aligned to the 64px rail.
           -------------------------------------------------- */
        [data-testid="stBottom"] {
            position: fixed !important;

            left: 64px !important;
            right: 0 !important;

            width: auto !important;
            max-width: none !important;

            margin: 0 !important;
            padding: 7px 10px 10px 0 !important;

            box-sizing: border-box !important;
            z-index: 999998 !important;
        }

        [data-testid="stBottom"] > div {
            width: 100% !important;
            max-width: 100% !important;
            min-width: 0 !important;
            margin: 0 !important;
            box-sizing: border-box !important;
        }

        [data-testid="stBottom"] [data-testid="stChatInput"] {
            width: 100% !important;
            max-width: none !important;
            min-width: 0 !important;

            margin: 0 !important;
            transform: none !important;
            box-sizing: border-box !important;
        }

        [data-testid="stBottom"] [data-testid="stChatInput"] > div {
            width: 100% !important;
            max-width: 100% !important;
            min-width: 0 !important;
            box-sizing: border-box !important;
        }

        /* Open sidebar should not shrink the composer. */
        body:has([class*="st-key-custom_sidebar"]) [data-testid="stBottom"] {
            left: 0 !important;
            right: 0 !important;
            padding-left: 10px !important;
            padding-right: 10px !important;
        }

        /* Keep content immediately above the fixed composer. */
        .prompt-hint {
            margin-bottom: 18px !important;
            padding-bottom: 10px !important;
        }
    }

    /* ======================================================
       VERY SMALL PHONES
       ====================================================== */
    @media (max-width: 480px) {

        .main .block-container,
        [data-testid="stAppViewContainer"] .block-container,
        body:has([class*="st-key-custom_rail"]) .block-container {
            padding-left: 72px !important;
            padding-right: 9px !important;
            padding-bottom: 175px !important;
        }

        [class*="st-key-custom_rail"] {
            width: 60px !important;
            min-width: 60px !important;
            max-width: 60px !important;
            padding-left: 6px !important;
            padding-right: 6px !important;
        }

        [class*="st-key-custom_rail"] [class*="st-key-rail_open_button"],
        [class*="st-key-custom_rail"] [class*="st-key-rail_workspace"],
        [class*="st-key-custom_rail"] [class*="st-key-rail_search"],
        [class*="st-key-custom_rail"] [class*="st-key-rail_notes"],
        [class*="st-key-custom_rail"] [class*="st-key-rail_explain"],
        [class*="st-key-custom_rail"] [class*="st-key-rail_research"],
        [class*="st-key-custom_rail"] [class*="st-key-rail_revision"],
        [class*="st-key-custom_rail"] button {
            width: 44px !important;
            min-width: 44px !important;
            max-width: 44px !important;
            height: 44px !important;
            min-height: 44px !important;
            max-height: 44px !important;
        }

        body:has([class*="st-key-custom_rail"]) [data-testid="stBottom"] {
            left: 60px !important;
        }

        body:has([class*="st-key-custom_sidebar"]) [data-testid="stBottom"] {
            left: 0 !important;
            right: 0 !important;
        }
    }


    /* ============================================================
       FINAL FINAL RESPONSIVE OVERRIDES
       Do not let Markdown/PDF content collapse to one character
       per line. Do not constrain the composer to a centered box.
       ============================================================ */

    /* The chat message is a flex item in Streamlit. Explicitly
       give both the message and its content a real width. */
    [data-testid="stChatMessage"] {
        width: 100% !important;
        max-width: 100% !important;
        min-width: 0 !important;
        box-sizing: border-box !important;
    }

    [data-testid="stChatMessage"] > div {
        min-width: 0 !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
    }

    [data-testid="stChatMessageContent"],
    [data-testid="stChatMessageContent"] > div,
    [data-testid="stChatMessageContent"] > div > div,
    [data-testid="stChatMessageContent"] [data-testid="stMarkdown"],
    [data-testid="stChatMessageContent"] [data-testid="stMarkdownContainer"] {
        width: 100% !important;
        max-width: 100% !important;
        min-width: 0 !important;
        box-sizing: border-box !important;
    }

    /* Normal prose must wrap at words, NOT individual characters. */
    [data-testid="stChatMessageContent"] p,
    [data-testid="stChatMessageContent"] li,
    [data-testid="stChatMessageContent"] h1,
    [data-testid="stChatMessageContent"] h2,
    [data-testid="stChatMessageContent"] h3,
    [data-testid="stChatMessageContent"] h4,
    [data-testid="stChatMessageContent"] h5,
    [data-testid="stChatMessageContent"] h6,
    [data-testid="stChatMessageContent"] blockquote {
        width: auto !important;
        max-width: 100% !important;
        min-width: 0 !important;
        overflow-wrap: break-word !important;
        word-break: normal !important;
        white-space: normal !important;
    }

    /* TABLES:
       Let the browser calculate sensible column widths.
       If a table is genuinely wider than a phone, scroll the
       table itself instead of squeezing every word into letters. */
    [data-testid="stChatMessageContent"] table {
        display: table !important;
        width: max-content !important;
        min-width: 100% !important;
        max-width: none !important;
        table-layout: auto !important;
        border-collapse: collapse !important;
    }

    [data-testid="stChatMessageContent"] table th,
    [data-testid="stChatMessageContent"] table td {
        width: auto !important;
        min-width: 110px !important;
        max-width: none !important;
        padding: 9px 10px !important;
        white-space: normal !important;
        overflow-wrap: break-word !important;
        word-break: normal !important;
        vertical-align: top !important;
        box-sizing: border-box !important;
    }

    /* Put wide tables inside a scroll container where possible. */
    [data-testid="stChatMessageContent"] table {
        margin-left: 0 !important;
        margin-right: 0 !important;
    }

    /* CODE: preserve indentation and horizontal scrolling. */
    [data-testid="stChatMessageContent"] pre {
        display: block !important;
        width: 100% !important;
        max-width: 100% !important;
        min-width: 0 !important;
        overflow-x: auto !important;
        overflow-y: hidden !important;
        white-space: pre !important;
        word-break: normal !important;
        overflow-wrap: normal !important;
        box-sizing: border-box !important;
    }

    [data-testid="stChatMessageContent"] pre code {
        display: block !important;
        width: max-content !important;
        min-width: 100% !important;
        max-width: none !important;
        white-space: pre !important;
        word-break: normal !important;
        overflow-wrap: normal !important;
    }

    /* ------------------------------------------------------------
       COMPOSER — CLOSED RAIL
       It should use the whole available horizontal rectangle,
       not a 980px/centered box.
       ------------------------------------------------------------ */
    [data-testid="stBottom"] {
        box-sizing: border-box !important;
        width: auto !important;
        max-width: none !important;
        margin: 0 !important;
    }

    [data-testid="stBottom"] > div,
    [data-testid="stBottom"] > div > div,
    [data-testid="stBottom"] > div > div > div {
        box-sizing: border-box !important;
        max-width: none !important;
    }

    [data-testid="stBottom"] [data-testid="stChatInput"] {
        box-sizing: border-box !important;
        max-width: none !important;
        transform: none !important;
    }

    @media (min-width: 901px) {
        /* Rail is 72px. Composer fills essentially the entire
           remaining viewport, with only a small visual gutter. */
        body:has([class*="st-key-custom_rail"]) [data-testid="stBottom"] {
            left: 72px !important;
            right: 0 !important;
            width: auto !important;
            padding: 7px 18px 12px 18px !important;
        }

        body:has([class*="st-key-custom_rail"]) [data-testid="stBottom"] [data-testid="stChatInput"] {
            width: 100% !important;
            max-width: none !important;
            margin: 0 !important;
        }

        /* When the full sidebar is open on desktop, the composer
           begins after that sidebar and still spans the remainder. */
        body:has([class*="st-key-custom_sidebar"]) [data-testid="stBottom"] {
            left: 290px !important;
            right: 0 !important;
            width: auto !important;
            padding: 7px 18px 12px 18px !important;
        }

        body:has([class*="st-key-custom_sidebar"]) [data-testid="stBottom"] [data-testid="stChatInput"] {
            width: 100% !important;
            max-width: none !important;
            margin: 0 !important;
        }
    }

    @media (max-width: 900px) {
        /* Closed rail: composer starts immediately after the rail
           and uses all remaining phone width. */
        body:has([class*="st-key-custom_rail"]) [data-testid="stBottom"] {
            left: 64px !important;
            right: 0 !important;
            width: auto !important;
            padding: 7px 10px 10px 10px !important;
        }

        body:has([class*="st-key-custom_rail"]) [data-testid="stBottom"] [data-testid="stChatInput"] {
            width: 100% !important;
            max-width: none !important;
            margin: 0 !important;
        }

        /* Open drawer overlays the page, so composer becomes full
           viewport width. */
        body:has([class*="st-key-custom_sidebar"]) [data-testid="stBottom"] {
            left: 0 !important;
            right: 0 !important;
            width: 100% !important;
            padding: 7px 10px 10px 10px !important;
        }

        body:has([class*="st-key-custom_sidebar"]) [data-testid="stBottom"] [data-testid="stChatInput"] {
            width: 100% !important;
            max-width: none !important;
            margin: 0 !important;
        }

        /* Give the actual phone content the width between the rail
           and the right edge. */
        body:has([class*="st-key-custom_rail"]) .block-container {
            width: calc(100vw - 64px) !important;
            max-width: calc(100vw - 64px) !important;
            min-width: 0 !important;
            margin-left: 64px !important;
            margin-right: 0 !important;
            padding-left: 16px !important;
            padding-right: 12px !important;
            box-sizing: border-box !important;
        }

        body:has([class*="st-key-custom_sidebar"]) .block-container {
            width: 100vw !important;
            max-width: 100vw !important;
            margin-left: 0 !important;
            padding-left: 12px !important;
            padding-right: 12px !important;
            box-sizing: border-box !important;
        }
    }

    /* The Streamlit main area itself must never become a wider
       flex item than the phone. */
    @media (max-width: 900px) {
        [data-testid="stAppViewContainer"] > .main,
        [data-testid="stAppViewContainer"] > .main > div,
        [data-testid="stAppViewContainer"] .main {
            min-width: 0 !important;
            max-width: 100vw !important;
            overflow-x: hidden !important;
        }

        [data-testid="stChatMessageContent"] ul,
        [data-testid="stChatMessageContent"] ol {
            width: auto !important;
            max-width: 100% !important;
            min-width: 0 !important;
            padding-left: 1.5em !important;
            overflow-wrap: normal !important;
            word-break: normal !important;
        }
    }

</style>
<style>
/* ============================================================
   ABSOLUTE FINAL COMPOSER WIDTH FIX
   The previous rules still allowed Streamlit's internal
   centered/max-width wrapper to constrain st.chat_input.

   Desktop:
   - closed rail: input spans from the rail to the right edge
   - open sidebar: input spans from the sidebar edge to the
     right edge
   Mobile rules are intentionally left to the existing
   responsive CSS above.
   ============================================================ */

@media (min-width: 901px) {

    /* Remove Streamlit's centered/max-width constraint from
       every layer around the fixed chat input. */
    [data-testid="stBottom"],
    [data-testid="stBottom"] > div,
    [data-testid="stBottom"] > div > div,
    [data-testid="stBottom"] > div > div > div,
    [data-testid="stBottom"] [data-testid="stChatInput"],
    [data-testid="stBottom"] [data-testid="stChatInput"] > div {
        box-sizing: border-box !important;
        max-width: none !important;
        min-width: 0 !important;
    }

    /* CLOSED RAIL
       The rail in the desktop UI is 96px wide visually. */
    body:has([class*="st-key-custom_rail"]):not(:has([class*="st-key-custom_sidebar"]))
    [data-testid="stBottom"] {
        position: fixed !important;
        left: 96px !important;
        right: 0 !important;
        width: auto !important;
        max-width: none !important;
        margin: 0 !important;
        padding: 7px 18px 12px 18px !important;
    }

    body:has([class*="st-key-custom_rail"]):not(:has([class*="st-key-custom_sidebar"]))
    [data-testid="stBottom"] > div,
    body:has([class*="st-key-custom_rail"]):not(:has([class*="st-key-custom_sidebar"]))
    [data-testid="stBottom"] > div > div,
    body:has([class*="st-key-custom_rail"]):not(:has([class*="st-key-custom_sidebar"]))
    [data-testid="stBottom"] > div > div > div,
    body:has([class*="st-key-custom_rail"]):not(:has([class*="st-key-custom_sidebar"]))
    [data-testid="stBottom"] [data-testid="stChatInput"],
    body:has([class*="st-key-custom_rail"]):not(:has([class*="st-key-custom_sidebar"]))
    [data-testid="stBottom"] [data-testid="stChatInput"] > div {
        width: 100% !important;
        max-width: none !important;
        margin-left: 0 !important;
        margin-right: 0 !important;
    }

    /* OPEN SIDEBAR
       In the rendered desktop UI the sidebar occupies about
       380px. The composer therefore starts exactly at its
       visible right edge instead of staying centered. */
    body:has([class*="st-key-custom_sidebar"])
    [data-testid="stBottom"] {
        position: fixed !important;
        left: 380px !important;
        right: 0 !important;
        width: auto !important;
        max-width: none !important;
        margin: 0 !important;
        padding: 7px 18px 12px 18px !important;
    }

    body:has([class*="st-key-custom_sidebar"])
    [data-testid="stBottom"] > div,
    body:has([class*="st-key-custom_sidebar"])
    [data-testid="stBottom"] > div > div,
    body:has([class*="st-key-custom_sidebar"])
    [data-testid="stBottom"] > div > div > div,
    body:has([class*="st-key-custom_sidebar"])
    [data-testid="stBottom"] [data-testid="stChatInput"],
    body:has([class*="st-key-custom_sidebar"])
    [data-testid="stBottom"] [data-testid="stChatInput"] > div {
        width: 100% !important;
        max-width: none !important;
        margin-left: 0 !important;
        margin-right: 0 !important;
    }

    /* The actual input itself must not inherit Streamlit's
       normal 768px-ish centered width. */
    [data-testid="stBottom"] [data-testid="stChatInput"] {
        display: block !important;
        flex: 1 1 auto !important;
    }

    [data-testid="stBottom"] [data-testid="stChatInput"] form,
    [data-testid="stBottom"] [data-testid="stChatInput"] form > div {
        width: 100% !important;
        max-width: none !important;
    }
}
</style>

    """,
    unsafe_allow_html=True,
)


# ============================================================
# CUSTOM SIDEBAR / RAIL
#
# IMPORTANT:
# We deliberately do NOT use st.sidebar here.
# Streamlit's native sidebar can retain a collapsed browser
# state. This custom container cannot be hidden by that state.
# ============================================================

if st.session_state.sidebar_open:

    with st.container(key="custom_sidebar"):

        # ----------------------------------------------------
        # HAMBURGER
        # ----------------------------------------------------

        if st.button(
            "☰",
            key="close_sidebar_button",
            help="Collapse sidebar",
        ):

            st.session_state.sidebar_open = False

            st.rerun()


        # ----------------------------------------------------
        # BRAND
        # ----------------------------------------------------

        render_html(
            """
            <div class="brand-wrapper">

                <div class="brand-icon">
                    🤖
                </div>

                <div>

                    <div class="brand-title">
                        StudyMate
                    </div>

                    <div class="brand-subtitle">
                        Personal AI Study Companion
                    </div>

                </div>

            </div>
            """
        )


        # ----------------------------------------------------
        # WORKSPACE
        # ----------------------------------------------------

        st.markdown(
            '<div class="side-section">WORKSPACE</div>',
            unsafe_allow_html=True,
        )


        if st.button(
            "＋  New Conversation",
            use_container_width=True,
            key="new_conversation",
        ):

            if st.session_state.memory is not None:
                st.session_state.memory.clear()

            st.session_state.messages = []

            st.session_state.show_notes = False

            st.session_state.uploaded_document = None

            st.rerun()


        # ----------------------------------------------------
        # STUDY
        # ----------------------------------------------------

        st.markdown(
            '<div class="side-section">STUDY</div>',
            unsafe_allow_html=True,
        )


        if st.button(
            f"📝  Study Notes · {note_count}",
            use_container_width=True,
            key="study_notes",
        ):

            st.session_state.show_notes = True

            st.rerun()


        # ----------------------------------------------------
        # WHAT I CAN DO
        # ----------------------------------------------------

        st.markdown(
            '<div class="side-section">WHAT I CAN DO</div>',
            unsafe_allow_html=True,
        )


        render_html(
            """
            <div class="capability">
                💡 &nbsp; Explain concepts
            </div>

            <div class="capability">
                🧮 &nbsp; Solve calculations
            </div>

            <div class="capability">
                🔎 &nbsp; Research topics
            </div>

            <div class="capability">
                📝 &nbsp; Save study notes
            </div>

            <div class="capability">
                🧠 &nbsp; Remember conversations
            </div>

            <div class="capability">
                🎯 &nbsp; Help with revision
            </div>
            """
        )

else:

    # ========================================================
    # CLOSED RAIL
    #
    # The compact rail intentionally contains ONLY these five
    # controls:
    #   1. Hamburger  -> opens/closes the sidebar
    #   2. StudyMate logo -> returns to the main study page
    #   3. Search -> returns to/focuses the main study page
    #   4. Notes -> opens Study Notes on the main page
    #   5. New conversation -> clears the conversation
    #
    # CRITICAL: none of these buttons changes sidebar_open except
    # the hamburger. They therefore NEVER open the sidebar.
    # ========================================================

    with st.container(key="custom_rail"):

        # 1. HAMBURGER -- the ONLY rail control allowed to open
        # the sidebar.
        if st.button(
            "☰",
            key="rail_open_button",
            help="Open sidebar",
        ):
            st.session_state.sidebar_open = True
            st.rerun()

        # 2. STUDYMATE LOGO -- HOME / MAIN STUDY PAGE
        if st.button(
            "🤖",
            key="rail_home",
            help="StudyMate home",
        ):
            st.session_state.show_notes = False
            st.rerun()

        # 3. SEARCH -- MAIN CHAT PAGE
        # This deliberately does NOT touch sidebar_open.
        if st.button(
            "⌕",
            key="rail_search",
            help="Go to search",
        ):
            st.session_state.show_notes = False
            st.session_state.focus_chat = True
            st.rerun()

        # 4. NOTES -- OPEN NOTES PAGE, WITHOUT OPENING SIDEBAR
        if st.button(
            "📝",
            key="rail_notes",
            help="Study notes",
        ):
            st.session_state.show_notes = True
            st.rerun()

        # 5. NEW CONVERSATION -- CLEAR CHAT, WITHOUT OPENING SIDEBAR
        if st.button(
            "＋",
            key="rail_new_conversation",
            help="New conversation",
        ):
            if st.session_state.memory is not None:
                st.session_state.memory.clear()

            st.session_state.messages = []
            st.session_state.show_notes = False
            st.session_state.uploaded_document = None
            st.rerun()


st.markdown(
    """
    <style>
    /* ============================================================
       NOTES — FINAL RESPONSIVE OVERRIDES
       ============================================================ */

    [class*="st-key-note_item_"] {
        width: 100% !important;
        max-width: 100% !important;
        min-width: 0 !important;
        box-sizing: border-box !important;
    }

    [class*="st-key-note_item_"] [data-testid="stHorizontalBlock"] {
        width: 100% !important;
        max-width: 100% !important;
        min-width: 0 !important;
        display: flex !important;
        flex-wrap: nowrap !important;
        align-items: flex-start !important;
        box-sizing: border-box !important;
    }

    [class*="st-key-note_item_"] [data-testid="column"]:first-child {
        min-width: 0 !important;
        max-width: none !important;
        flex: 1 1 auto !important;
        box-sizing: border-box !important;
    }

    [class*="st-key-note_item_"] [data-testid="column"]:last-child {
        flex: 0 0 42px !important;
        width: 42px !important;
        min-width: 42px !important;
        max-width: 42px !important;
        box-sizing: border-box !important;
    }

    [class*="st-key-note_item_"] .note-text-wrap {
        width: 100% !important;
        max-width: 100% !important;
        min-width: 0 !important;
        overflow: hidden !important;
        box-sizing: border-box !important;
    }

    [class*="st-key-note_item_"] .note-text {
        width: 100% !important;
        max-width: 100% !important;
        min-width: 0 !important;
        white-space: pre-wrap !important;
        overflow-wrap: anywhere !important;
        word-break: normal !important;
        box-sizing: border-box !important;
    }

    /* The broad mobile CSS makes all Streamlit columns 100%.
       Override that ONLY inside a note card so the delete icon
       stays on the right of the same card. */
    @media (max-width: 900px) {

        [class*="st-key-note_item_"] {
            padding: 13px 11px 13px 13px !important;
        }

        [class*="st-key-note_item_"] [data-testid="stHorizontalBlock"] {
            width: 100% !important;
            max-width: 100% !important;
            flex-wrap: nowrap !important;
            gap: 8px !important;
        }

        [class*="st-key-note_item_"] [data-testid="column"]:first-child {
            width: auto !important;
            min-width: 0 !important;
            max-width: calc(100% - 50px) !important;
            flex: 1 1 auto !important;
        }

        [class*="st-key-note_item_"] [data-testid="column"]:last-child {
            width: 42px !important;
            min-width: 42px !important;
            max-width: 42px !important;
            flex: 0 0 42px !important;
        }

        [class*="st-key-note_item_"] [data-testid="stButton"] button {
            width: 42px !important;
            min-width: 42px !important;
            max-width: 42px !important;
            height: 38px !important;
            min-height: 38px !important;
            padding: 0 !important;
        }

        .notes-toolbar {
            padding: 11px 12px !important;
        }
    }

    @media (max-width: 480px) {

        [class*="st-key-note_item_"] {
            padding: 12px 9px 12px 11px !important;
        }

        [class*="st-key-note_item_"] [data-testid="column"]:last-child {
            width: 40px !important;
            min-width: 40px !important;
            max-width: 40px !important;
            flex-basis: 40px !important;
        }

        [class*="st-key-note_item_"] [data-testid="stButton"],
        [class*="st-key-note_item_"] [data-testid="stButton"] button {
            width: 40px !important;
            min-width: 40px !important;
            max-width: 40px !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# NOTES PAGE
# ============================================================

if st.session_state.show_notes:

    render_html(
        """
        <div class="welcome-card">

            <div class="welcome-title">
                Study Notes
            </div>

            <div class="welcome-text">
                Your saved study knowledge — clean, readable, and
                ready for revision.
            </div>

        </div>
        """
    )

    st.write("")


    # --------------------------------------------------------
    # BACK
    # --------------------------------------------------------

    if st.button(
        "←  Back to StudyMate",
        key="back_to_studymate",
    ):

        st.session_state.show_notes = False
        st.session_state.confirm_clear_notes_state = False

        st.rerun()


    st.write("")


    # --------------------------------------------------------
    # NOTES HEADER + CLEAR ALL
    # --------------------------------------------------------

    if notes:

        render_html(
            f"""
            <div class="notes-toolbar">

                <div class="notes-count">
                    <strong>{note_count}</strong>
                    {"saved note" if note_count == 1 else "saved notes"}
                </div>

            </div>
            """
        )


        # ----------------------------------------------------
        # CLEAR ALL CONFIRMATION
        # ----------------------------------------------------

        if st.session_state.confirm_clear_notes_state:

            render_html(
                """
                <div class="clear-notes-confirm">

                    <strong>Delete all study notes?</strong><br>

                    This will permanently remove every saved note
                    from your notes file. This cannot be undone.

                </div>
                """
            )

            confirm_col, cancel_col = st.columns(
                [1, 1],
                gap="small",
            )

            with confirm_col:

                if st.button(
                    "Yes, clear all notes",
                    key="confirm_clear_notes",
                    use_container_width=True,
                ):

                    clear_all_notes_for_ui()

                    st.session_state.confirm_clear_notes_state = False

                    st.rerun()


            with cancel_col:

                if st.button(
                    "Cancel",
                    key="cancel_clear_notes",
                    use_container_width=True,
                ):

                    st.session_state.confirm_clear_notes_state = False

                    st.rerun()

        else:

            if st.button(
                "Clear all notes",
                key="clear_all_notes",
                help="Delete every saved study note",
            ):

                st.session_state.confirm_clear_notes_state = True

                st.rerun()


        st.write("")


        # ----------------------------------------------------
        # NOTE CARDS
        # ----------------------------------------------------

        for index, note in enumerate(
            notes,
            start=1,
        ):

            safe_note = html.escape(
                str(note)
            )

            # Use a stable zero-based storage index for deletion.
            note_index = index - 1

            with st.container(
                key=f"note_item_{note_index}",
            ):

                note_col, delete_col = st.columns(
                    [0.90, 0.10],
                    gap="small",
                )


                with note_col:

                    render_html(
                        f"""
                        <div class="note-text-wrap">

                            <div class="note-number">
                                NOTE {index:02d}
                            </div>

                            <div class="note-text">
                                {safe_note}
                            </div>

                        </div>
                        """
                    )


                with delete_col:

                    if st.button(
                        "×",
                        key=f"delete_note_{note_index}",
                        help=f"Delete note {index}",
                    ):

                        delete_result = delete_note_for_ui(
                            note_index
                        )

                        # If the deleted note was the last note,
                        # also close any stale confirmation state.
                        st.session_state.confirm_clear_notes_state = False

                        st.rerun()

    else:

        st.session_state.confirm_clear_notes_state = False

        st.info(
            "You haven't saved any notes yet."
        )

        st.caption(
            "When you save a study note, it will appear here."
        )

    st.stop()




# ============================================================
# HOME
# ============================================================

if not st.session_state.messages:

    # --------------------------------------------------------
    # WELCOME
    # --------------------------------------------------------

    render_html(
        """
        <div class="welcome-card">

            <div class="welcome-title">
                Learn. Revise. Remember.
            </div>

            <div class="welcome-text">
                Your personal AI study companion for learning,
                researching, solving problems, saving knowledge,
                and revising whatever you are studying.
            </div>

        </div>
        """
    )

    st.write("")


    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    render_html(
        """
        <div class="status-card">

            <span class="status-dot"></span>

            <span class="status-text">
                StudyMate is ready to help
            </span>

        </div>
        """
    )

    st.write("")


    # --------------------------------------------------------
    # ACTION CARDS
    # --------------------------------------------------------

    card1, card2, card3, card4 = st.columns(
        4,
        gap="medium",
    )


    with card1:

        render_html(
            """
            <div class="action-card">

                <div class="action-icon">
                    💡
                </div>

                <div class="action-title">
                    Explain
                </div>

                <div class="action-description">
                    Understand difficult concepts clearly
                    and step by step.
                </div>

            </div>
            """
        )


    with card2:

        render_html(
            """
            <div class="action-card">

                <div class="action-icon">
                    🧮
                </div>

                <div class="action-title">
                    Calculate
                </div>

                <div class="action-description">
                    Solve calculations and numerical
                    problems accurately.
                </div>

            </div>
            """
        )


    with card3:

        render_html(
            """
            <div class="action-card">

                <div class="action-icon">
                    🔎
                </div>

                <div class="action-title">
                    Research
                </div>

                <div class="action-description">
                    Explore topics and find useful
                    information.
                </div>

            </div>
            """
        )


    with card4:

        render_html(
            """
            <div class="action-card">

                <div class="action-icon">
                    🎯
                </div>

                <div class="action-title">
                    Revise
                </div>

                <div class="action-description">
                    Test your understanding and
                    strengthen your memory.
                </div>

            </div>
            """
        )


    st.write("")


    # --------------------------------------------------------
    # EXAMPLE PROMPTS
    # --------------------------------------------------------

    render_html(
        """
        <div class="prompt-hint">

            Try:

            <strong>
                "Explain gradient descent simply"
            </strong>

            &nbsp; · &nbsp;

            <strong>
                "Calculate 3456 × 6543"
            </strong>

            &nbsp; · &nbsp;

            <strong>
                "Save this as a note"
            </strong>

        </div>
        """
    )


# ============================================================
# CHAT HISTORY
# ============================================================

for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )


# ============================================================
# DOCUMENT STATUS
# ============================================================

if st.session_state.uploaded_document:

    document_name = html.escape(
        st.session_state.uploaded_document["name"]
    )

    render_html(
        f"""
        <div class="document-status">

            📄

            <strong>
                {document_name}
            </strong>

            &nbsp; · &nbsp;

            Attached to this study session

        </div>
        """
    )


# ============================================================
# CHAT INPUT
#
# NORMAL CHAT + PDF/RAG BEHAVIOR
#
# IMPORTANT:
#
# The existence of a previously uploaded PDF does NOT force
# every future message into RAG mode.
#
# Routing is decided by THIS submission:
#
#   Normal text only
#       -> General Agent
#
#   PDF + text in the same submission
#       -> RAG
#
#   PDF only
#       -> Upload/attach the PDF and wait for a question
#
# This makes the app behave much more like a normal chatbot.
# ============================================================

chat_submission = st.chat_input(
    "Ask anything you're studying...",
    key="study_chat_input",
    accept_file=True,
    file_type=[
        "pdf",
    ],
)


# ============================================================
# HANDLE CHAT SUBMISSION
# ============================================================

if chat_submission:

    # --------------------------------------------------------
    # TEXT
    # --------------------------------------------------------

    user_input = getattr(
        chat_submission,
        "text",
        "",
    )

    if user_input is None:
        user_input = ""

    user_input = user_input.strip()


    # --------------------------------------------------------
    # FILE
    # --------------------------------------------------------

    uploaded_files = getattr(
        chat_submission,
        "files",
        [],
    )


    # --------------------------------------------------------
    # ROUTING FLAG
    # --------------------------------------------------------
    #
    # This is the important fix.
    #
    # DO NOT use st.session_state.uploaded_document to decide
    # whether the current message is a RAG request.
    #
    # uploaded_document persists for the session. Therefore,
    # using it for routing would make every later message a
    # PDF/RAG question.
    #
    # Instead, only a PDF attached to THIS message activates
    # RAG for THIS message.
    # --------------------------------------------------------

    has_new_pdf = bool(uploaded_files)


    # ========================================================
    # PDF UPLOAD
    # ========================================================

    if has_new_pdf:

        uploaded_file = uploaded_files[0]


        # ----------------------------------------------------
        # SEND DOCUMENT TO FASTAPI / RAG
        # ----------------------------------------------------

        upload_result = upload_document_to_api(
            uploaded_file
        )


        if not upload_result["ok"]:

            st.error(
                f"PDF upload failed: {upload_result['error']}"
            )

            st.stop()


        rag_data = upload_result["data"]


        # ----------------------------------------------------
        # SAVE DOCUMENT INFORMATION
        # ----------------------------------------------------
        #
        # The document remains visible in the UI for the
        # current study session.
        #
        # IMPORTANT:
        # This stored value is NOT used as the routing flag.
        # ----------------------------------------------------

        st.session_state.uploaded_document = {

            "name": uploaded_file.name,

            "type": uploaded_file.type,

            "size": uploaded_file.size,

            "bytes": uploaded_file.getvalue(),

            "document_id": rag_data["document_id"],

            "chunks": rag_data.get(
                "chunks",
                0,
            ),

        }


    # ========================================================
    # PDF ONLY
    # ========================================================
    #
    # User attached a PDF but did not ask anything yet.
    # We upload it and show an attachment message.
    # ========================================================

    if has_new_pdf and not user_input:

        file_name = uploaded_files[0].name


        attachment_message = (
            f"📄 **Uploaded `{file_name}`**\n\n"
            "The document is attached to this study session. "
            "To ask the document a question, attach the PDF "
            "with your question."
        )


        st.session_state.messages.append(
            {
                "role": "user",
                "content": attachment_message,
            }
        )


        with st.chat_message("user"):

            st.markdown(
                attachment_message
            )


        st.stop()


    # ========================================================
    # EMPTY MESSAGE
    # ========================================================

    if not user_input:
        st.stop()


    # ========================================================
    # USER MESSAGE
    # ========================================================

    display_user_message = user_input


    if has_new_pdf:

        file_name = uploaded_files[0].name

        display_user_message = (
            f"📄 **{file_name}**\n\n"
            f"{user_input}"
        )


    st.session_state.messages.append(
        {
            "role": "user",
            "content": display_user_message,
        }
    )


    with st.chat_message("user"):

        st.markdown(
            display_user_message
        )


    # ========================================================
    # ROUTING
    # ========================================================
    #
    # PDF attached to THIS message
    #       -> RAG
    #
    # No PDF attached to THIS message
    #       -> General Agent
    #
    # A PDF uploaded earlier does NOT change this behavior.
    # ========================================================

    try:

        # ====================================================
        # RAG MODE
        # ====================================================

        if has_new_pdf:

            uploaded_document = (
                st.session_state.uploaded_document
            )


            if not uploaded_document:

                raise RuntimeError(
                    "PDF was uploaded but no document information "
                    "was stored."
                )


            document_id = uploaded_document.get(
                "document_id"
            )


            if not document_id:

                raise RuntimeError(
                    "PDF upload succeeded but no document_id "
                    "was returned by the RAG API."
                )


            # ------------------------------------------------
            # ASK RAG
            # ------------------------------------------------

            rag_result = ask_rag_api(
                document_id=document_id,
                question=user_input,
            )


            if not rag_result["ok"]:

                raise RuntimeError(
                    rag_result["error"]
                )


            rag_data = rag_result["data"]


            # ------------------------------------------------
            # ANSWER
            # ------------------------------------------------

            final_response = rag_data.get(
                "answer",
                "",
            )


            # ------------------------------------------------
            # SOURCES
            # ------------------------------------------------

            sources = rag_data.get(
                "sources",
                [],
            )


            if sources:

                source_lines = []
                seen_sources = set()


                for source in sources:

                    filename = source.get(
                        "filename",
                        "unknown",
                    )


                    page = source.get(
                        "page_label",
                        source.get(
                            "page",
                            None,
                        ),
                    )


                    source_key = (
                        filename,
                        page,
                    )


                    if source_key in seen_sources:
                        continue


                    seen_sources.add(
                        source_key
                    )


                    if page is not None:

                        source_lines.append(
                            f"- {filename} — page {page}"
                        )

                    else:

                        source_lines.append(
                            f"- {filename}"
                        )


                if source_lines:

                    final_response = (
                        f"{final_response}\n\n"
                        "**Sources:**\n"
                        + "\n".join(
                            source_lines
                        )
                    )


            if not isinstance(
                final_response,
                str,
            ):

                final_response = str(
                    final_response
                )


        # ====================================================
        # GENERAL CHAT MODE
        # ====================================================
        #
        # This is now the default path.
        #
        # Even if a PDF was uploaded earlier, a normal message
        # comes here unless a PDF is attached to that message.
        # ====================================================

        else:

            # ------------------------------------------------
            # LAZY LOAD GENERAL AGENT
            # ------------------------------------------------

            try:

                if st.session_state.agent is None:

                    from app.agent.agent import get_agent

                    from app.memory.memory import (
                        ConversationMemory
                    )


                    st.session_state.agent = (
                        get_agent()
                    )


                    st.session_state.memory = (
                        ConversationMemory()
                    )


                agent = (
                    st.session_state.agent
                )


                memory = (
                    st.session_state.memory
                )


                # ------------------------------------------------
                # BUILD CONVERSATION INPUT
                # ------------------------------------------------

                messages_for_agent = (
                    memory.get_messages()
                    + [
                        {
                            "role": "user",
                            "content": user_input,
                        }
                    ]
                )


                # ------------------------------------------------
                # INVOKE GENERAL AGENT
                # ------------------------------------------------

                response = agent.invoke(
                    {
                        "messages": messages_for_agent
                    }
                )


                # ------------------------------------------------
                # UPDATE MEMORY
                # ------------------------------------------------

                memory.add_messages(
                    response["messages"]
                )


                # ------------------------------------------------
                # GET FINAL RESPONSE
                # ------------------------------------------------

                final_message = (
                    response["messages"][-1]
                )


                final_response = (
                    final_message.content
                )


                if not isinstance(
                    final_response,
                    str,
                ):

                    final_response = str(
                        final_response
                    )


            except Exception as agent_error:

                raise RuntimeError(
                    "General chat failed. "
                    f"Agent error: {agent_error}"
                )


        # ====================================================
        # SAVE ASSISTANT MESSAGE
        # ====================================================

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": final_response,
            }
        )


        # ====================================================
        # DISPLAY ASSISTANT MESSAGE
        # ====================================================

        with st.chat_message(
            "assistant"
        ):

            st.markdown(
                final_response
            )


    except Exception as e:

        print(
            f"StudyMate error: "
            f"{type(e).__name__}: {e}"
        )


        error_message = (
            "I couldn't complete that request right now. "
            "Please try again."
        )


        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": error_message,
            }
        )


        with st.chat_message(
            "assistant"
        ):

            st.warning(
                error_message
            )


st.markdown(
    """
    <style>
    /* ============================================================
       FINAL CLOSED-RAIL CONTROLS
       Exactly five icons. Only the hamburger opens the sidebar.
       ============================================================ */

    [class*="st-key-custom_rail"] {
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        gap: 10px !important;
    }

    [class*="st-key-custom_rail"] [class*="st-key-rail_open_button"],
    [class*="st-key-custom_rail"] [class*="st-key-rail_home"],
    [class*="st-key-custom_rail"] [class*="st-key-rail_search"],
    [class*="st-key-custom_rail"] [class*="st-key-rail_notes"],
    [class*="st-key-custom_rail"] [class*="st-key-rail_new_conversation"] {
        display: block !important;
        width: 40px !important;
        min-width: 40px !important;
        max-width: 40px !important;
        height: 40px !important;
        min-height: 40px !important;
        max-height: 40px !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    [class*="st-key-custom_rail"] [class*="st-key-rail_open_button"] button,
    [class*="st-key-custom_rail"] [class*="st-key-rail_home"] button,
    [class*="st-key-custom_rail"] [class*="st-key-rail_search"] button,
    [class*="st-key-custom_rail"] [class*="st-key-rail_notes"] button,
    [class*="st-key-custom_rail"] [class*="st-key-rail_new_conversation"] button {
        width: 40px !important;
        min-width: 40px !important;
        max-width: 40px !important;
        height: 40px !important;
        min-height: 40px !important;
        max-height: 40px !important;
        margin: 0 !important;
        padding: 0 !important;
        box-sizing: border-box !important;
        background: #F3EEFF !important;
        background-color: #F3EEFF !important;
        color: #7354D7 !important;
        border: 1px solid #D8C9F5 !important;
        border-radius: 11px !important;
        box-shadow: 0 3px 10px rgba(115, 84, 215, 0.08) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    [class*="st-key-custom_rail"] [class*="st-key-rail_open_button"] button p,
    [class*="st-key-custom_rail"] [class*="st-key-rail_home"] button p,
    [class*="st-key-custom_rail"] [class*="st-key-rail_search"] button p,
    [class*="st-key-custom_rail"] [class*="st-key-rail_notes"] button p,
    [class*="st-key-custom_rail"] [class*="st-key-rail_new_conversation"] button p {
        margin: 0 !important;
        padding: 0 !important;
        color: #7354D7 !important;
        font-size: 18px !important;
        line-height: 1 !important;
    }

    [class*="st-key-custom_rail"] button:hover {
        background: #EAE1FF !important;
        background-color: #EAE1FF !important;
        border-color: #C5B1EF !important;
        color: #6547C9 !important;
    }

    /* Mobile: keep the same five controls, scaled to the existing
       compact rail instead of allowing Streamlit to stretch them. */
    @media (max-width: 900px) {
        [class*="st-key-custom_rail"] {
            gap: 10px !important;
        }

        [class*="st-key-custom_rail"] [class*="st-key-rail_open_button"],
        [class*="st-key-custom_rail"] [class*="st-key-rail_home"],
        [class*="st-key-custom_rail"] [class*="st-key-rail_search"],
        [class*="st-key-custom_rail"] [class*="st-key-rail_notes"],
        [class*="st-key-custom_rail"] [class*="st-key-rail_new_conversation"] {
            width: 44px !important;
            min-width: 44px !important;
            max-width: 44px !important;
            height: 44px !important;
            min-height: 44px !important;
            max-height: 44px !important;
        }

        [class*="st-key-custom_rail"] [class*="st-key-rail_open_button"] button,
        [class*="st-key-custom_rail"] [class*="st-key-rail_home"] button,
        [class*="st-key-custom_rail"] [class*="st-key-rail_search"] button,
        [class*="st-key-custom_rail"] [class*="st-key-rail_notes"] button,
        [class*="st-key-custom_rail"] [class*="st-key-rail_new_conversation"] button {
            width: 44px !important;
            min-width: 44px !important;
            max-width: 44px !important;
            height: 44px !important;
            min-height: 44px !important;
            max-height: 44px !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <style>
    /* ============================================================
       FINAL CHAT BAR — ALIGN WITH THE MAIN CONTENT RECTANGLES
       ------------------------------------------------------------
       The chat/search bar is NOT centered independently.

       Its LEFT and RIGHT edges follow the same content area as the
       hero/status/cards above it.

       Closed rail:
           content starts after the compact rail.

       Open sidebar:
           content starts after the full sidebar.

       Mobile:
           content uses the available screen width.
    ============================================================ */

    [data-testid="stBottom"],
    [data-testid="stBottom"] > div,
    [data-testid="stBottom"] > div > div,
    [data-testid="stBottom"] > div > div > div {
        box-sizing: border-box !important;
    }

    [data-testid="stBottom"] [data-testid="stChatInput"],
    [data-testid="stBottom"] [data-testid="stChatInput"] > div,
    [data-testid="stBottom"] [data-testid="stChatInput"] form,
    [data-testid="stBottom"] [data-testid="stChatInput"] form > div {
        box-sizing: border-box !important;
        min-width: 0 !important;
        max-width: none !important;
    }

    /* ============================================================
       DESKTOP
    ============================================================ */
    @media (min-width: 901px) {

        /* Bottom composer follows the CLOSED-RAIL content area */
        [data-testid="stBottom"] {
            left: 50px !important;
            right: 0 !important;
            width: auto !important;
            padding: 7px 28px 12px 28px !important;
            box-sizing: border-box !important;
        }

        /* If the full sidebar is open, follow its content edge */
        body:has([class*="st-key-custom_sidebar"]) [data-testid="stBottom"] {
            left: 382px !important;
            right: 0 !important;
            width: auto !important;
            padding: 7px 28px 12px 28px !important;
        }

        /* THE BAR ITSELF:
           same horizontal span as the main content.
           No centering. No 980px cap. */
        [data-testid="stBottom"] [data-testid="stChatInput"] {
            display: block !important;
            width: 100% !important;
            max-width: none !important;
            min-width: 0 !important;
            margin: 0 !important;
            transform: none !important;
            box-sizing: border-box !important;
        }

        [data-testid="stBottom"] [data-testid="stChatInput"] > div,
        [data-testid="stBottom"] [data-testid="stChatInput"] form,
        [data-testid="stBottom"] [data-testid="stChatInput"] form > div {
            width: 100% !important;
            max-width: none !important;
            min-width: 0 !important;
            margin: 0 !important;
            box-sizing: border-box !important;
        }
    }

    /* ============================================================
       MOBILE
    ============================================================ */
    @media (max-width: 900px) {

        /* Closed rail */
        [data-testid="stBottom"] {
            left: 118px !important;
            right: 0 !important;
            width: auto !important;
            padding: 7px 10px 10px 26px !important;
            box-sizing: border-box !important;
        }

        /* Open sidebar — Streamlit's sidebar becomes an overlay,
           so the composer uses the full viewport width. */
        body:has([class*="st-key-custom_sidebar"]) [data-testid="stBottom"] {
            left: 0 !important;
            right: 0 !important;
            width: 100% !important;
            padding: 7px 10px 10px 10px !important;
        }

        [data-testid="stBottom"] [data-testid="stChatInput"],
        [data-testid="stBottom"] [data-testid="stChatInput"] > div,
        [data-testid="stBottom"] [data-testid="stChatInput"] form,
        [data-testid="stBottom"] [data-testid="stChatInput"] form > div {
            width: 100% !important;
            max-width: none !important;
            min-width: 0 !important;
            margin: 0 !important;
            box-sizing: border-box !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    """
    <style>
    /* ============================================================
       FINAL SEARCH / CHAT BAR ALIGNMENT
       ------------------------------------------------------------
       The composer is intentionally NOT centered.

       Desktop closed rail:
         Main cards start at ~128px and end at ~1608px.
         Match those exact horizontal edges.

       Desktop open sidebar:
         Start after the 290px drawer + 34px content padding.

       The old rules above are kept for the rest of the UI.
       These rules are the LAST rules, so they win.
       ============================================================ */

    @media (min-width: 901px) {

        /* CLOSED RAIL */
        body:has([class*="st-key-custom_rail"]):not(:has([class*="st-key-custom_sidebar"]))
        [data-testid="stBottom"] {
            position: fixed !important;
            left: 94px !important;
            right: 56px !important;
            width: auto !important;
            max-width: none !important;
            margin: 0 !important;
            padding: 7px 0 12px 34px !important;
            box-sizing: border-box !important;
        }

        /* OPEN SIDEBAR */
        body:has([class*="st-key-custom_sidebar"])
        [data-testid="stBottom"] {
            position: fixed !important;
            left: 290px !important;
            right: 56px !important;
            width: auto !important;
            max-width: none !important;
            margin: 0 !important;
            padding: 7px 0 12px 42px !important;
            box-sizing: border-box !important;
        }

        /* Remove every Streamlit centering / max-width layer. */
        [data-testid="stBottom"],
        [data-testid="stBottom"] > div,
        [data-testid="stBottom"] > div > div,
        [data-testid="stBottom"] > div > div > div,
        [data-testid="stBottom"] [data-testid="stChatInput"],
        [data-testid="stBottom"] [data-testid="stChatInput"] > div,
        [data-testid="stBottom"] [data-testid="stChatInput"] form,
        [data-testid="stBottom"] [data-testid="stChatInput"] form > div {
            width: 100% !important;
            max-width: none !important;
            min-width: 0 !important;
            margin-left: 0 !important;
            margin-right: 0 !important;
            box-sizing: border-box !important;
            transform: none !important;
        }

        /* For the closed rail, the bottom bar's 34px left padding
           is the same visual gutter used by the main cards. */
        body:has([class*="st-key-custom_rail"]):not(:has([class*="st-key-custom_sidebar"]))
        [data-testid="stBottom"] [data-testid="stChatInput"] {
            width: calc(100% - 34px) !important;
        }

        /* For the open drawer, match the content gutter. */
        body:has([class*="st-key-custom_sidebar"])
        [data-testid="stBottom"] [data-testid="stChatInput"] {
            width: calc(100% - 42px) !important;
        }
    }

    @media (max-width: 900px) {

        /* Mobile remains full-width relative to the available page;
           do not apply the desktop rectangle measurements. */
        body:has([class*="st-key-custom_rail"]) [data-testid="stBottom"] {
            left: 64px !important;
            right: 0 !important;
            width: auto !important;
            padding: 7px 10px 10px 10px !important;
        }

        body:has([class*="st-key-custom_sidebar"]) [data-testid="stBottom"] {
            left: 0 !important;
            right: 0 !important;
            width: 100% !important;
            padding: 7px 10px 10px 10px !important;
        }

        [data-testid="stBottom"] [data-testid="stChatInput"],
        [data-testid="stBottom"] [data-testid="stChatInput"] > div,
        [data-testid="stBottom"] [data-testid="stChatInput"] form,
        [data-testid="stBottom"] [data-testid="stChatInput"] form > div {
            width: 100% !important;
            max-width: none !important;
            min-width: 0 !important;
            margin: 0 !important;
            box-sizing: border-box !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    """
    <style>
    /* ============================================================
       FINAL RESPONSE / TABLE OVERFLOW FIX
       ------------------------------------------------------------
       Fixes generated answer content escaping the white response
       box on the right. This does NOT change the search bar.
       ============================================================ */

    [data-testid="stChatMessageContent"],
    [data-testid="stChatMessageContent"] > div,
    [data-testid="stChatMessageContent"] [data-testid="stMarkdown"],
    [data-testid="stChatMessageContent"] [data-testid="stMarkdownContainer"] {
        width: 100% !important;
        max-width: 100% !important;
        min-width: 0 !important;
        box-sizing: border-box !important;
        overflow-x: hidden !important;
    }

    /* Keep generated Markdown tables inside the response box. */
    [data-testid="stChatMessageContent"] table {
        display: table !important;
        width: 100% !important;
        min-width: 0 !important;
        max-width: 100% !important;
        table-layout: fixed !important;
        border-collapse: collapse !important;
        box-sizing: border-box !important;
        overflow: hidden !important;
    }

    [data-testid="stChatMessageContent"] table th,
    [data-testid="stChatMessageContent"] table td {
        min-width: 0 !important;
        max-width: none !important;
        padding: 9px 10px !important;
        white-space: normal !important;
        overflow-wrap: anywhere !important;
        word-break: break-word !important;
        vertical-align: top !important;
        box-sizing: border-box !important;
    }

    /* Long text, links, and inline code must wrap inside cells. */
    [data-testid="stChatMessageContent"] table p,
    [data-testid="stChatMessageContent"] table li,
    [data-testid="stChatMessageContent"] table span,
    [data-testid="stChatMessageContent"] table strong,
    [data-testid="stChatMessageContent"] table em,
    [data-testid="stChatMessageContent"] table a {
        max-width: 100% !important;
        min-width: 0 !important;
        white-space: normal !important;
        overflow-wrap: anywhere !important;
        word-break: break-word !important;
        box-sizing: border-box !important;
    }

    [data-testid="stChatMessageContent"] table code {
        display: inline !important;
        max-width: 100% !important;
        min-width: 0 !important;
        white-space: pre-wrap !important;
        overflow-wrap: anywhere !important;
        word-break: break-word !important;
        box-sizing: border-box !important;
    }

    /* Normal answer text must also never widen the response. */
    [data-testid="stChatMessageContent"] p,
    [data-testid="stChatMessageContent"] li,
    [data-testid="stChatMessageContent"] blockquote,
    [data-testid="stChatMessageContent"] h1,
    [data-testid="stChatMessageContent"] h2,
    [data-testid="stChatMessageContent"] h3,
    [data-testid="stChatMessageContent"] h4,
    [data-testid="stChatMessageContent"] h5,
    [data-testid="stChatMessageContent"] h6 {
        max-width: 100% !important;
        min-width: 0 !important;
        overflow-wrap: anywhere !important;
        word-break: break-word !important;
        box-sizing: border-box !important;
    }

    /* Code blocks can scroll internally rather than widening the page. */
    [data-testid="stChatMessageContent"] pre {
        display: block !important;
        width: 100% !important;
        max-width: 100% !important;
        min-width: 0 !important;
        overflow-x: auto !important;
        overflow-y: hidden !important;
        box-sizing: border-box !important;
    }

    /* Media stays inside the answer card. */
    [data-testid="stChatMessageContent"] img,
    [data-testid="stChatMessageContent"] video,
    [data-testid="stChatMessageContent"] iframe {
        max-width: 100% !important;
        min-width: 0 !important;
        height: auto !important;
        box-sizing: border-box !important;
    }

    @media (max-width: 900px) {
        [data-testid="stChatMessageContent"] table {
            width: 100% !important;
            max-width: 100% !important;
            min-width: 0 !important;
            table-layout: fixed !important;
        }

        [data-testid="stChatMessageContent"] table th,
        [data-testid="stChatMessageContent"] table td {
            min-width: 0 !important;
            padding: 7px 6px !important;
            font-size: 12px !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)