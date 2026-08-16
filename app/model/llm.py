from langchain_groq import ChatGroq

from app.config import MODEL_NAME


def get_llm():
    return ChatGroq(
        model=MODEL_NAME,
        temperature=0,
    )