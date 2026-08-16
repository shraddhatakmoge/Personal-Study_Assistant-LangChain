from langchain_core.messages import HumanMessage, AIMessage

from app.memory.memory import ConversationMemory


def test_memory():
    memory = ConversationMemory()

    messages = [
        HumanMessage(content="What is LangChain?"),
        AIMessage(content="LangChain is a framework for LLM applications.")
    ]

    memory.add_messages(messages)

    assert len(memory.get_messages()) == 2
    assert memory.get_messages()[0].content == "What is LangChain?"
    assert memory.get_messages()[1].content == "LangChain is a framework for LLM applications."