"""Unity sends text or a WAV; this server calls STT, the agent and TTS."""
import logging
from pathlib import Path
import tempfile

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

import agent
import stt
import tts
from schemas import ChatRequest, ChatResponse, load_speech_settings

logger = logging.getLogger(__name__)
MAX_AUDIO_BYTES = 20 * 1024 * 1024
tts.AUDIO_DIR.mkdir(parents=True, exist_ok=True)
app = FastAPI(title="Virtual Human: course integration")
app.mount("/static", StaticFiles(directory=tts.AUDIO_DIR.parent), name="static")


@app.get("/")
def status():
    return {"status": "ok", "brain": "mock", **load_speech_settings().model_dump()}


async def respond(text: str, transcript: str | None = None) -> ChatResponse:
    settings = load_speech_settings()
    reply = await run_in_threadpool(agent.respond, text, language=settings.language)
    await run_in_threadpool(tts.cleanup)
    try:
        audio_url = await run_in_threadpool(tts.synthesize, reply.speech_text, language=settings.language)
    except Exception:
        logger.exception("Speech synthesis failed; returning the text without audio")
        audio_url = None
    return ChatResponse(**reply.model_dump(), audio_url=audio_url, transcript=transcript)


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    return await respond(request.text)


@app.post("/voice-chat", response_model=ChatResponse)
async def voice_chat(audio: UploadFile = File(...)):
    path = None
    try:
        recording = await audio.read(MAX_AUDIO_BYTES + 1)
        if not recording:
            raise HTTPException(status_code=400, detail="The recording is empty.")
        if len(recording) > MAX_AUDIO_BYTES:
            raise HTTPException(status_code=413, detail="The recording exceeds 20 MB.")
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as file:
            path = Path(file.name)
            file.write(recording)
        try:
            text = await run_in_threadpool(stt.transcribe, path)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except Exception as exc:
            logger.exception("Speech recognition failed")
            raise HTTPException(status_code=422, detail="The recording could not be transcribed.") from exc
        if not text.strip():
            raise HTTPException(status_code=400, detail="No speech was detected. Please try again.")
        return await respond(text, transcript=text)
    finally:
        await audio.close()
        if path is not None:
            path.unlink(missing_ok=True)
