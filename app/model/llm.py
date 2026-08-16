import os

from langchain_groq import ChatGroq

from app.config import MODEL_NAME


def get_llm():

    groq_api_key = os.getenv("GROQ_API_KEY")

    if not groq_api_key:
        raise ValueError(
            "GROQ_API_KEY is not configured."
        )

    return ChatGroq(
        model=MODEL_NAME,
        temperature=0,
        api_key=groq_api_key,
    )