from typing import List, Optional

from pydantic import BaseModel


class ChatMessage(BaseModel):
    """Represents a single message in a chat conversation.

    Attributes:
        role (str): The role of the message sender (e.g., "user", "assistant").
        content (str): The content of the message.
    """

    role: str
    content: str


class ChatRequest(BaseModel):
    """Represents a chat request containing a list of messages and an optional system prompt.

    Attributes:
        messages (List[ChatMessage]): A list of messages in the chat conversation.
        system_prompt (Optional[str]): An optional system prompt to provide context for the conversation.
    """

    messages: List[ChatMessage]
    system_prompt: Optional[str] = None
