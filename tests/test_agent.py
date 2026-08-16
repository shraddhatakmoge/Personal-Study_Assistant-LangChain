from app.agent.agent import get_agent


def test_agent():
    agent = get_agent()

    response = agent.invoke({
        "messages": [
            {
                "role": "user",
                "content": "What is LangChain?"
            }
        ]
    })

    assert "messages" in response
    assert len(response["messages"]) > 0