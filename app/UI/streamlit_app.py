import html
import textwrap

import streamlit as st

from app.agent.agent import get_agent
from app.memory.memory import ConversationMemory
from app.tools.notes import get_notes


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="StudyMate",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# HTML HELPER
# ============================================================

def render_html(content: str):
    st.html(textwrap.dedent(content).strip())


# ============================================================
# SESSION STATE
# ============================================================

if "agent" not in st.session_state:
    st.session_state.agent = get_agent()

if "memory" not in st.session_state:
    st.session_state.memory = ConversationMemory()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "show_notes" not in st.session_state:
    st.session_state.show_notes = False

if "sidebar_open" not in st.session_state:
    st.session_state.sidebar_open = True


agent = st.session_state.agent
memory = st.session_state.memory


# ============================================================
# NOTES
# ============================================================

notes_result = get_notes.invoke({})

if notes_result == "No notes saved yet.":
    notes = []
else:
    notes = [
        line.strip()
        for line in notes_result.splitlines()
        if line.strip()
    ]

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
       MAIN CONTENT
       ====================================================== */

    .block-container {
        width: 100% !important;
        max-width: none !important;

        box-sizing: border-box !important;

        padding-top: 18px !important;
        padding-left: 42px !important;
        padding-right: 42px !important;
        padding-bottom: 90px !important;
    }


    /* ======================================================
       REMOVE NATIVE STREAMLIT SIDEBAR HEADER
       ====================================================== */

    [data-testid="stSidebarHeader"] {
        display: none !important;

        height: 0 !important;
        min-height: 0 !important;
        max-height: 0 !important;

        padding: 0 !important;
        margin: 0 !important;
    }

    [data-testid="stSidebarCollapseButton"] {
        display: none !important;
    }

    [data-testid="stSidebarCollapsedControl"] {
        display: none !important;
    }

    button[aria-label="Close sidebar"],
    button[aria-label="Open sidebar"],
    button[aria-label="Expand sidebar"],
    button[aria-label="Collapse sidebar"] {
        display: none !important;
    }


    /* ======================================================
       SIDEBAR OPEN
       ====================================================== */

    section[data-testid="stSidebar"] {
        background: #FFFFFF !important;

        width: 210px !important;
        min-width: 210px !important;
        max-width: 210px !important;

        flex-basis: 210px !important;

        border-right: 1px solid #E8E1F2 !important;

        box-shadow:
            2px 0 12px
            rgba(82, 63, 130, 0.035) !important;
    }

    section[data-testid="stSidebar"] > div {
        background: #FFFFFF !important;

        padding: 0 12px 18px 12px !important;

        margin: 0 !important;
    }


    /* ======================================================
       OPEN SIDEBAR HAMBURGER
       ====================================================== */

    .st-key-close_sidebar_button {
        width: 36px !important;
        height: 36px !important;

        margin: 8px 0 14px auto !important;
        padding: 0 !important;
    }

    .st-key-close_sidebar_button button {
        width: 36px !important;
        height: 36px !important;

        min-width: 36px !important;
        min-height: 36px !important;

        padding: 0 !important;
        margin: 0 !important;

        background: #F3EEFF !important;
        background-color: #F3EEFF !important;

        border: 1px solid #D8C9F5 !important;
        border-radius: 10px !important;

        color: #7354D7 !important;

        box-shadow:
            0 3px 10px
            rgba(115, 84, 215, 0.10) !important;

        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    .st-key-close_sidebar_button button:hover {
        background: #EAE1FF !important;
        background-color: #EAE1FF !important;

        border-color: #C6B3EF !important;

        color: #6547C9 !important;
    }

    .st-key-close_sidebar_button button p {
        margin: 0 !important;
        padding: 0 !important;

        color: #7354D7 !important;

        font-size: 18px !important;
        font-weight: 800 !important;

        line-height: 1 !important;
    }


    /* ======================================================
       BRAND
       ====================================================== */

    .brand-wrapper {
        display: flex;

        align-items: center;

        gap: 9px;

        margin: 0 0 20px 0 !important;
        padding: 0 !important;
    }

    .brand-icon {
        width: 42px;
        height: 42px;

        flex-shrink: 0;

        display: flex;
        align-items: center;
        justify-content: center;

        border-radius: 12px;

        background:
            linear-gradient(
                135deg,
                #8066E8,
                #B29CF4
            );

        font-size: 21px;

        box-shadow:
            0 7px 18px
            rgba(128, 102, 232, 0.18);

        position: relative;
    }

    /* ------------------------------------------------------
       Robot greeting animation
       ------------------------------------------------------ */

    .robot-greeting {
        display: inline-flex;
        align-items: center;

        margin-left: 2px;

        color: #7354D7;

        font-size: 10px;
        font-weight: 800;

        animation:
            robot_hi 1.8s ease-in-out infinite;
    }

    @keyframes robot_hi {

        0% {
            opacity: 0.45;
            transform: translateY(1px);
        }

        25% {
            opacity: 1;
            transform: translateY(0);
        }

        50% {
            opacity: 0.8;
            transform: translateY(-1px);
        }

        75% {
            opacity: 1;
            transform: translateY(0);
        }

        100% {
            opacity: 0.45;
            transform: translateY(1px);
        }
    }

    .brand-title {
        color: #292535;

        font-size: 18px;
        font-weight: 800;

        line-height: 1.1;
    }

    .brand-subtitle {
        margin-top: 4px;

        color: #918A9F;

        font-size: 8px;

        line-height: 1.2;

        white-space: nowrap;
    }


    /* ======================================================
       SIDEBAR SECTION LABELS
       ====================================================== */

    .side-section {
        margin-top: 17px;
        margin-bottom: 7px;

        color: #9992A7;

        font-size: 9px;
        font-weight: 800;

        letter-spacing: 1.1px;
    }


    /* ======================================================
       NORMAL SIDEBAR BUTTONS
       ====================================================== */

    .st-key-new_conversation,
    .st-key-study_notes {
        width: 100% !important;

        margin: 0 !important;
        padding: 0 !important;
    }

    .st-key-new_conversation button,
    .st-key-study_notes button {
        width: 100% !important;

        min-height: 38px !important;

        padding: 8px 10px !important;
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

        appearance: none !important;
        -webkit-appearance: none !important;
    }

    .st-key-new_conversation button:hover,
    .st-key-study_notes button:hover {
        background: #F6F2FF !important;
        background-color: #F6F2FF !important;

        color: #6F55D4 !important;

        border-color: #C9BBEE !important;
    }

    .st-key-new_conversation button p,
    .st-key-study_notes button p {
        color: inherit !important;

        font-size: 12px !important;

        font-weight: 600 !important;
    }


    /* ======================================================
       CAPABILITIES
       ====================================================== */

    .capability {
        margin: 8px 0;

        color: #777080;

        font-size: 10.5px;

        line-height: 1.3;

        white-space: nowrap;
    }


    /* ======================================================
       COLLAPSED SIDEBAR
       ====================================================== */

    body:has(.st-key-rail_open_button)
    section[data-testid="stSidebar"] {
        width: 58px !important;
        min-width: 58px !important;
        max-width: 58px !important;

        flex-basis: 58px !important;

        padding: 0 !important;

        overflow: hidden !important;
    }

    body:has(.st-key-rail_open_button)
    section[data-testid="stSidebar"] > div {
        width: 58px !important;
        min-width: 58px !important;
        max-width: 58px !important;

        padding: 0 !important;

        margin: 0 !important;

        overflow: hidden !important;
    }


    /* ======================================================
       CLOSED HAMBURGER
       ====================================================== */

    .st-key-rail_open_button {
        width: 38px !important;
        height: 38px !important;

        margin: 10px auto 10px auto !important;
        padding: 0 !important;
    }

    .st-key-rail_open_button button {
        width: 38px !important;
        height: 38px !important;

        min-width: 38px !important;
        min-height: 38px !important;

        padding: 0 !important;
        margin: 0 !important;

        background: #F3EEFF !important;
        background-color: #F3EEFF !important;

        border: 1px solid #D8C9F5 !important;
        border-radius: 10px !important;

        color: #7354D7 !important;

        box-shadow:
            0 3px 10px
            rgba(115, 84, 215, 0.10) !important;

        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    .st-key-rail_open_button button:hover {
        background: #EAE1FF !important;
        background-color: #EAE1FF !important;

        border-color: #C6B3EF !important;

        color: #6547C9 !important;
    }

    .st-key-rail_open_button button p {
        margin: 0 !important;
        padding: 0 !important;

        color: #7354D7 !important;

        font-size: 18px !important;
        font-weight: 800 !important;

        line-height: 1 !important;
    }


    /* ======================================================
       CLOSED RAIL BUTTONS
       ====================================================== */

    .st-key-rail_workspace,
    .st-key-rail_search,
    .st-key-rail_notes,
    .st-key-rail_explain,
    .st-key-rail_research,
    .st-key-rail_revision {
        width: 38px !important;
        height: 38px !important;

        margin: 5px auto !important;
        padding: 0 !important;
    }

    .st-key-rail_workspace button,
    .st-key-rail_search button,
    .st-key-rail_notes button,
    .st-key-rail_explain button,
    .st-key-rail_research button,
    .st-key-rail_revision button {
        width: 38px !important;
        height: 38px !important;

        min-width: 38px !important;
        min-height: 38px !important;

        padding: 0 !important;
        margin: 0 !important;

        background: #F3EEFF !important;
        background-color: #F3EEFF !important;

        border: 1px solid #D8C9F5 !important;
        border-radius: 10px !important;

        color: #7354D7 !important;

        box-shadow: none !important;

        display: flex !important;
        align-items: center !important;
        justify-content: center !important;

        appearance: none !important;
        -webkit-appearance: none !important;
    }

    .st-key-rail_workspace button:hover,
    .st-key-rail_search button:hover,
    .st-key-rail_notes button:hover,
    .st-key-rail_explain button:hover,
    .st-key-rail_research button:hover,
    .st-key-rail_revision button:hover {
        background: #EAE1FF !important;
        background-color: #EAE1FF !important;

        border-color: #C6B3EF !important;

        color: #6547C9 !important;
    }

    .st-key-rail_workspace button p,
    .st-key-rail_search button p,
    .st-key-rail_notes button p,
    .st-key-rail_explain button p,
    .st-key-rail_research button p,
    .st-key-rail_revision button p {
        margin: 0 !important;
        padding: 0 !important;

        color: #7354D7 !important;

        font-size: 16px !important;

        line-height: 1 !important;
    }


    /* ======================================================
       REMOVE STREAMLIT VERTICAL GAPS AROUND RAIL
       ====================================================== */

    section[data-testid="stSidebar"]
    div[data-testid="stElementContainer"]:has(.st-key-rail_open_button),
    section[data-testid="stSidebar"]
    div[data-testid="stElementContainer"]:has(.st-key-rail_workspace),
    section[data-testid="stSidebar"]
    div[data-testid="stElementContainer"]:has(.st-key-rail_search),
    section[data-testid="stSidebar"]
    div[data-testid="stElementContainer"]:has(.st-key-rail_notes),
    section[data-testid="stSidebar"]
    div[data-testid="stElementContainer"]:has(.st-key-rail_explain),
    section[data-testid="stSidebar"]
    div[data-testid="stElementContainer"]:has(.st-key-rail_research),
    section[data-testid="stSidebar"]
    div[data-testid="stElementContainer"]:has(.st-key-rail_revision) {
        margin: 0 !important;
        padding: 0 !important;

        height: 48px !important;

        min-height: 48px !important;
        max-height: 48px !important;
    }


    /* ======================================================
       RAIL DIVIDER
       ====================================================== */

    .rail-divider {
        width: 30px !important;
        height: 1px !important;

        margin: 7px auto !important;

        background: #E5DDF0 !important;
    }


    /* ======================================================
       WELCOME
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
       PROMPT
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
       CHAT
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
       ====================================================== */

    [data-testid="stBottom"] {
        background: #F8F6FC !important;
        background-color: #F8F6FC !important;

        border-top: 1px solid #E8E1F2 !important;

        box-shadow: none !important;

        padding-top: 7px !important;
        padding-bottom: 12px !important;
    }

    [data-testid="stBottom"] > div {
        background: #F8F6FC !important;
        background-color: #F8F6FC !important;

        box-shadow: none !important;
    }

    [data-testid="stBottom"] section {
        background: #F8F6FC !important;
        background-color: #F8F6FC !important;
    }

    [data-testid="stBottom"] form {
        background: transparent !important;

        border: none !important;

        box-shadow: none !important;
    }

    [data-testid="stChatInput"] {
        width: min(980px, 90%) !important;

        max-width: 980px !important;

        margin: 0 auto !important;
    }

    [data-testid="stChatInput"] > div {
        background: #FFFFFF !important;
        background-color: #FFFFFF !important;

        border: 1px solid #DCD3ED !important;

        border-radius: 16px !important;

        box-shadow:
            0 6px 20px
            rgba(80, 60, 130, 0.07) !important;
    }

    [data-testid="stChatInput"] textarea {
        background: #FFFFFF !important;
        background-color: #FFFFFF !important;

        color: #302A3C !important;

        font-size: 14px !important;
    }

    [data-testid="stChatInput"] textarea::placeholder {
        color: #A29BAB !important;
    }


    /* ======================================================
       PURPLE CHAT SEND ARROW
       ====================================================== */

    [data-testid="stChatInput"] button {
        background: #F3EEFF !important;
        background-color: #F3EEFF !important;

        border: 1px solid #E0D5F4 !important;

        color: #7354D7 !important;
    }

    [data-testid="stChatInput"] button:hover {
        background: #EAE1FF !important;
        background-color: #EAE1FF !important;

        border-color: #CDBDEE !important;

        color: #6547C9 !important;
    }

    [data-testid="stChatInput"] button svg {
        color: #7354D7 !important;

        stroke: #7354D7 !important;

        fill: none !important;
    }

    [data-testid="stChatInput"] button:hover svg {
        color: #6547C9 !important;

        stroke: #6547C9 !important;
    }


    /* ======================================================
       NOTES
       ====================================================== */

    .note-card {
        margin-bottom: 9px;

        padding: 14px 16px;

        background: #FFFFFF;

        border: 1px solid #E8E1F2;

        border-left: 4px solid #9277E4;

        border-radius: 12px;

        color: #514A5D;

        font-size: 13px;

        line-height: 1.55;
    }

    .note-number {
        color: #765DD5;

        font-weight: 700;
    }


    /* ======================================================
       STREAMLIT GENERAL SPACING
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
       RESPONSIVE
       ====================================================== */

    @media (max-width: 900px) {

        section[data-testid="stSidebar"] {
            width: 58px !important;
            min-width: 58px !important;
            max-width: 58px !important;
        }

        .block-container {
            padding-top: 15px !important;
            padding-left: 18px !important;
            padding-right: 18px !important;
        }

        .welcome-card {
            padding: 22px;
        }

        .welcome-title {
            font-size: 25px;
        }

        .welcome-text {
            font-size: 12px;
        }

        .action-card {
            min-height: 108px;
        }

        [data-testid="stChatInput"] {
            width: 94% !important;
        }
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    # ========================================================
    # COLLAPSED RAIL
    # ========================================================

    if not st.session_state.sidebar_open:

        # ----------------------------------------------------
        # HAMBURGER
        # ----------------------------------------------------

        if st.button(
            "☰",
            key="rail_open_button",
            help="Open sidebar",
        ):

            st.session_state.sidebar_open = True
            st.rerun()


        # ----------------------------------------------------
        # WORKSPACE
        # ----------------------------------------------------

        if st.button(
            "▦",
            key="rail_workspace",
            help="Workspace",
        ):

            st.session_state.sidebar_open = True
            st.rerun()


        # ----------------------------------------------------
        # SEARCH
        # ----------------------------------------------------

        if st.button(
            "⌕",
            key="rail_search",
            help="Search",
        ):

            st.session_state.sidebar_open = True
            st.rerun()


        # ----------------------------------------------------
        # DIVIDER
        # ----------------------------------------------------

        render_html(
            """
            <div class="rail-divider"></div>
            """
        )


        # ----------------------------------------------------
        # NOTES
        # ----------------------------------------------------

        if st.button(
            "📝",
            key="rail_notes",
            help="Study Notes",
        ):

            st.session_state.sidebar_open = True
            st.session_state.show_notes = True

            st.rerun()


        # ----------------------------------------------------
        # EXPLAIN
        # ----------------------------------------------------

        if st.button(
            "💡",
            key="rail_explain",
            help="Explain concepts",
        ):

            st.session_state.sidebar_open = True
            st.rerun()


        # ----------------------------------------------------
        # RESEARCH
        # ----------------------------------------------------

        if st.button(
            "🔎",
            key="rail_research",
            help="Research topics",
        ):

            st.session_state.sidebar_open = True
            st.rerun()


        # ----------------------------------------------------
        # REVISION
        # ----------------------------------------------------

        if st.button(
            "🎯",
            key="rail_revision",
            help="Help with revision",
        ):

            st.session_state.sidebar_open = True
            st.rerun()


    # ========================================================
    # OPEN SIDEBAR
    # ========================================================

    else:

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

            memory.clear()

            st.session_state.messages = []

            st.session_state.show_notes = False

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
                Your saved study knowledge.
            </div>

        </div>
        """
    )

    st.write("")


    if st.button(
        "←  Back to StudyMate",
        key="back_to_studymate",
    ):

        st.session_state.show_notes = False
        st.rerun()


    st.write("")


    if not notes:

        st.info(
            "You haven't saved any notes yet."
        )

    else:

        for index, note in enumerate(
            notes,
            start=1,
        ):

            safe_note = html.escape(note)

            render_html(
                f"""
                <div class="note-card">

                    <span class="note-number">
                        {index:02d}
                    </span>

                    &nbsp;&nbsp;

                    {safe_note}

                </div>
                """
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
    # PROMPT HINT
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
# CHAT INPUT
# ============================================================

user_input = st.chat_input(
    "Ask anything you're studying..."
)


# ============================================================
# HANDLE MESSAGE
# ============================================================

if user_input:

    # --------------------------------------------------------
    # USER
    # --------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_input,
        }
    )


    with st.chat_message("user"):

        st.markdown(
            user_input
        )


    # --------------------------------------------------------
    # AGENT
    # --------------------------------------------------------

    try:

        response = agent.invoke(
            {
                "messages": (
                    memory.get_messages()
                    + [
                        {
                            "role": "user",
                            "content": user_input,
                        }
                    ]
                )
            }
        )


        # ----------------------------------------------------
        # MEMORY
        # ----------------------------------------------------

        memory.add_messages(
            response["messages"]
        )


        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        final_message = response["messages"][-1]

        final_response = final_message.content


        if not isinstance(
            final_response,
            str,
        ):

            final_response = str(
                final_response
            )


        # ----------------------------------------------------
        # SAVE
        # ----------------------------------------------------

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": final_response,
            }
        )


        # ----------------------------------------------------
        # DISPLAY
        # ----------------------------------------------------

        with st.chat_message("assistant"):

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


        with st.chat_message("assistant"):

            st.warning(
                error_message
            )