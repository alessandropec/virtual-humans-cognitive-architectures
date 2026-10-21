"""A stateless mock. Replace respond() with LangChain during the course."""
import re

from schemas import AgentReply, Language


def respond(text: str, language: Language = "en") -> AgentReply:
    """Text in, speech and optional body language out. No API key is needed."""
    italian = language == "it"
    if re.search(r"\b(hi|hello|ciao|salve|buongiorno|buonasera)\b", text, re.IGNORECASE):
        return AgentReply(speech_text="Ciao! Sono Camila." if italian else "Hello! I am Camila.", action="WAVE", emotion="HAPPY")
    if "name" in text.lower() or "nome" in text.lower():
        return AgentReply(speech_text="Non ricordo ancora i messaggi precedenti." if italian else "I do not remember earlier messages yet.")
    if re.search(r"\b(thanks|grazie)\b", text, re.IGNORECASE):
        return AgentReply(speech_text="Prego!" if italian else "You are welcome!", emotion="HAPPY")
    return AgentReply(speech_text=f"Hai detto: {text}" if italian else f"You said: {text}")
