from langchain_core.messages import BaseMessage


class ConversationMemory:

    def __init__(self):
        self.messages: list[BaseMessage] = []

    def add_messages(self, messages):
        self.messages.extend(messages)

    def get_messages(self):
        return self.messages

    def clear(self):
        self.messages.clear()