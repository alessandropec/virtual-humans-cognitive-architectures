"""The cognitive server's own structured-output schema and catalog."""
from typing import Literal
from pydantic import BaseModel, Field

Emotion = Literal['NEUTRAL', 'HAPPY', 'ANGRY', 'SAD', 'FEAR', 'DISGUST', 'LOVE', 'SLEEP']
Expression = Literal['😐', '😏', '🙂', '😊', '😀', '😃', '😄', '😁', '😆', '😝', '😂', '😉', '😭', '🥺', '😞', '😔', '😳', '☹️', '😚', '😘', '🥰', '😍', '😡', '😠', '😒', '😱', '😬', '🙄', '👀', '😴']
Gesture = Literal['handup', 'index', 'ok', 'thumbup', 'thumbdown', 'side', 'shrug', 'namaste', 'yes', 'no']


class AgentRequest(BaseModel):
    text: str = Field(min_length=1)


class ModelReply(BaseModel):
    speech_text: str | None = Field(default=None, description='Text to say.')
    emotion: Emotion | None = Field(default=None, description='Emotion to keep active.')
    expression: Expression | None = Field(default=None, description='Facial expression.')
    gesture: Gesture | None = Field(default=None, description='One gesture. Null keeps the current gesture.')


class AgentReply(ModelReply):
    # Added by the program, never requested from the language model.
    whiteboard: dict[str, str] | None = None
