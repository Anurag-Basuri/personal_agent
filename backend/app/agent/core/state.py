"""Types and state definitions for the LangGraph agent."""

from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage


def add_messages(left: list[BaseMessage], right: list[BaseMessage]) -> list[BaseMessage]:
    """Custom reducer for messages."""
    return left + right


class AgentState(TypedDict):
    """The state of the agent graph."""
    messages: Annotated[list[BaseMessage], add_messages]
    session_id: str
    user_id: str | None
    # e.g., "GUEST" or "ADMIN"
    role: str
    current_url: str | None
    # Intent classification from the router node
    # "tool_use", "direct_reply", "greeting", "meta_question"
    intent: str
    # Conversation summary injected from memory
    summary: str | None

