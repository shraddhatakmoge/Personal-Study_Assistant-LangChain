from app.agent.agent import get_agent
from app.memory.memory import ConversationMemory
from app.tools.notes import get_notes


def main():
    agent = get_agent()
    memory = ConversationMemory()

    while True:
        user_input = input("\nYou: ").strip()

        if not user_input:
            continue

        if user_input.lower() in {"/exit", "/quit"}:
            print("Goodbye!")
            break

        if user_input.lower() == "/help":
            print("""
Available commands:

/help   - Show available commands
/notes  - Show saved study notes
/clear  - Clear conversation memory
/exit   - Exit the assistant
""")
            continue

        if user_input.lower() == "/notes":
            print("\n" + get_notes.invoke({}))
            continue

        if user_input.lower() == "/clear":
            memory.clear()
            print("\nConversation memory cleared.")
            continue

        try:
            response = agent.invoke({
                "messages": memory.get_messages() + [
                    {
                        "role": "user",
                        "content": user_input
                    }
                ]
            })

            memory.add_messages(response["messages"])

            print("\nAssistant:", response["messages"][-1].content)

        except Exception as e:
            print(f"\nError: {e}")


if __name__ == "__main__":
    main()