"""A stateless mock. Replace respond() with LangChain during the course."""
import re

from schemas import AgentReply


def respond(text: str) -> AgentReply:
    """Text in, speech and optional body language out. No API key is needed."""
    if re.search(r"\b(hi|hello|ciao)\b", text, re.IGNORECASE):
        return AgentReply(speech_text="Hello! I am Camila.", action="WAVE", emotion="HAPPY")
    if "name" in text.lower() or "nome" in text.lower():
        return AgentReply(speech_text="I do not remember earlier messages yet.")
    if re.search(r"\b(thanks|grazie)\b", text, re.IGNORECASE):
        return AgentReply(speech_text="You are welcome!", emotion="HAPPY")
    return AgentReply(speech_text=f"You said: {text}")
