"""The small JSON contract shared with Unity's AgentNetworkClient."""
from typing import Literal
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

Action = Literal["NONE", "WAVE", "SHRUG", "THINKING"]
Emotion = Literal["NEUTRAL", "HAPPY", "SAD", "SURPRISED", "ANGRY"]
Language = Literal["en", "it"]
CONFIG_PATH = Path(__file__).resolve().with_name("speech_config.json")


class SpeechSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    language: Language = "en"
    stt_language: Literal["auto", "en", "it"] = "auto"


def load_speech_settings() -> SpeechSettings:
    """Read on each request, so a language change does not require a restart."""
    return SpeechSettings.model_validate_json(CONFIG_PATH.read_text(encoding="utf-8"))


class ChatRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    text: str = Field(min_length=1, max_length=8000)


class AgentReply(BaseModel):
    """What the agent decides. The server supplies the audio URL separately."""
    model_config = ConfigDict(extra="forbid")
    speech_text: str
    action: Action = "NONE"
    emotion: Emotion = "NEUTRAL"


class ChatResponse(AgentReply):
    audio_url: str | None = None
    transcript: str | None = None
    brain: str = "mock"
