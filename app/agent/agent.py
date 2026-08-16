from langchain.agents import create_agent

from app.model.llm import get_llm
from app.agent.prompt import SYSTEM_PROMPT
from app.tools.calculator import calculator
from app.tools.research import research
from app.tools.notes import save_note, get_notes


def get_agent():
    llm = get_llm()

    return create_agent(
        model=llm,
        tools=[
            calculator,
            research,
            save_note,
            get_notes,
        ],
        system_prompt=SYSTEM_PROMPT,
    )