"""HTTP contract for the avatar client; also shown in FastAPI /docs."""
import sys
import json
from pathlib import Path
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

CATALOG = json.loads((Path(__file__).parent / 'assets/motion-catalog.json').read_text(encoding='utf-8'))
Mood = Literal[tuple(CATALOG['moods'])]
Emotion = Literal[tuple(name.upper() for name in CATALOG['moods'])]
Expression = Literal[tuple(dict.fromkeys(name for item in CATALOG['expressions'] for name in [item['id'], *item['aliases']]))]
Gesture = Literal[tuple(item['id'] for item in CATALOG['gestures'])]



class Schema(BaseModel):
    model_config = ConfigDict(extra='forbid')


class BoardImage(Schema):
    type: Literal['image']
    image_url: str = Field(pattern=r'^/media/board-[a-f0-9]{32}\.png$')


class BoardClear(Schema):
    type: Literal['clear']


class AgentReply(Schema):
    speech_text: str | None = Field(default=None, max_length=8000)
    emotion: Emotion | None = None
    expression: Expression | None = None
    gesture: Gesture | None = None
    whiteboard: Annotated[BoardImage | BoardClear, Field(discriminator='type')] | None = None

class SpeakRequest(AgentReply):
    audio_url: str | None = None


class ExpressionRequest(Schema):
    expression: Expression


class GestureRequest(Schema):
    gesture: Gesture


class CharacterRequest(Schema):
    character: Literal['julia', 'david']


class MotionStopRequest(Schema):
    track: Literal['all', 'expression', 'body'] = 'all'


class MoodRequest(Schema):
    mood: Mood


class ViewRequest(Schema):
    view: Literal['head', 'upper', 'mid', 'full']


class TextInput(Schema):
    text: str = Field(min_length=1, max_length=8000)


class AvatarState(Schema):
    character: str = 'julia'
    expression: str | None = None
    gesture: str | None = None
    mood: str = 'neutral'
    view: str = 'upper'
    speaking: bool = False
    recording: bool = False
    whiteboard: BoardImage | BoardClear = Field(default_factory=lambda: BoardClear(type='clear'))


class StatusResponse(Schema):
    browser_connected: bool
    agent_configured: bool = False
    state: AvatarState


class CommandResult(Schema):
    command_id: str
    status: Literal['applied'] = 'applied'
    state: AvatarState


class AudioFile(Schema):
    audio_url: str
    mime_type: str


class InputEvent(Schema):
    id: int
    kind: Literal['text', 'audio']
    text: str | None = None
    audio_url: str | None = None
    mime_type: str | None = None


class Settings(Schema):
    agent_url: str = 'http://127.0.0.1:8000/agent'
    agent_enabled: bool = True
    agent_heartbeat_url: str = 'http://127.0.0.1:8000/heartbeat'
    agent_script: str = ''
    agent_python: str = ''
    agent_autostart: bool = True
    language: Literal['it', 'en'] = 'en'
    stt_language: Literal['it', 'en'] = 'en'
    character: Literal['julia', 'david'] = 'julia'
    models_dir: str = 'models'
    vad_threshold: float = Field(default=0.35, ge=0.1, le=0.9)
    speech_enabled: bool = True
    live_transcription: bool = True
    tts_device: Literal['auto', 'cpu', 'cuda'] = 'cpu'
    stt_device: Literal['auto', 'cpu', 'cuda'] = 'cpu' if sys.platform == 'darwin' else 'auto'
    stt_model: Literal['tiny', 'small'] = 'small'

    @field_validator('stt_device', 'tts_device')
    @classmethod
    def cpu_only_on_mac(cls, value):
        return 'cpu' if sys.platform == 'darwin' else value

    @field_validator('agent_url', 'agent_heartbeat_url')
    @classmethod
    def validate_url(cls, value):
        from urllib.parse import urlparse
        value = value.strip()
        parsed = urlparse(value)
        if value and (parsed.scheme not in ('http', 'https') or not parsed.netloc):
            raise ValueError('Enter a complete HTTP/HTTPS URL or leave it empty.')
        return value


class ChatResult(Schema):
    text: str
    reply: SpeakRequest | None = None
    diagnostics: dict[str, float | str] | None = None
