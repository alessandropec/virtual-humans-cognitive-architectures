"""The small JSON contract shared with Unity's AgentNetworkClient."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Action = Literal["NONE", "WAVE", "SHRUG", "THINKING"]
Emotion = Literal["NEUTRAL", "HAPPY", "SAD", "SURPRISED", "ANGRY"]


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
