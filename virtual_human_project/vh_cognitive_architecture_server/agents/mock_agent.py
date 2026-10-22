"""Fixed reply for testing without an LLM or API keys."""
from schemas import AgentReply


def response(text: str) -> AgentReply:
    return AgentReply(speech_text="Hello world", whiteboard=None)
