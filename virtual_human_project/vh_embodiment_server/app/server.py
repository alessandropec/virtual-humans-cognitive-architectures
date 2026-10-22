"""Browser avatar, local STT/TTS and text-only connection to an external agent."""
import asyncio
import os
import mimetypes
import logging
import json
from collections import deque
from contextlib import asynccontextmanager, suppress
from pathlib import Path
import tempfile
import uuid
from io import BytesIO
from PIL import Image, UnidentifiedImageError
import httpx

from fastapi import FastAPI, File, Form, HTTPException, Query, Request, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool
from pydantic import ValidationError
import speech
from cognitive_connection import CognitiveConnection
import time
import tts_device
import server_logs
from path_picker import select_path
from model_warmup import ModelWarmup
from project_paths import find_repository
from typing import Literal
from model_files import installed_whisper
from schemas import (AudioFile, AvatarState, CommandResult, GestureRequest, InputEvent,
                     MoodRequest, SpeakRequest, StatusResponse, TextInput, ViewRequest,
                     Settings, AgentReply, ChatResult, ExpressionRequest,
                     CharacterRequest, MotionStopRequest)

ROOT = Path(__file__).resolve().parent
CATALOG = json.loads((ROOT / 'assets/motion-catalog.json').read_text(encoding='utf-8'))
SERVER_PORT = int(os.environ.get('VH_PORT', '8899'))
mimetypes.add_type('text/javascript', '.mjs')
media = tempfile.TemporaryDirectory(prefix='vh-browser-audio-')
MEDIA = Path(media.name)
client: WebSocket | None = None
state = AvatarState()
pending = {}
server_instance = None
shutdown_task: asyncio.Task | None = None
BROWSER_CLOSE_GRACE_SECONDS = 8


def stop_server():
    if server_instance is not None:
        server_instance.should_exit = True


async def stop_after_browser_close():
    await asyncio.sleep(BROWSER_CLOSE_GRACE_SECONDS)
    if client is None:
        print('Avatar page closed: stopping server.', flush=True)
        stop_server()

inputs: deque[InputEvent] = deque(maxlen=100)
sequence = 0
CONFIG = ROOT / 'settings.json'
logger = logging.getLogger(__name__)


def trace(label, data):
    print(f'[{label}] {json.dumps(data, ensure_ascii=True)}', flush=True)


async def progress(text):
    if client is not None:
        try:
            await client.send_json({'kind': 'progress', 'data': {'text': text}})
        except (RuntimeError, WebSocketDisconnect, OSError):
            pass


def get_settings():
    data = json.loads(CONFIG.read_text(encoding='utf-8')) if CONFIG.exists() else {}
    if ROOT.name == 'app' and ROOT.parent.name == 'vh_embodiment_server':
        source_default = (ROOT.parent.parent / 'installation/models').resolve()
        current_models = data.get('models_dir', 'models')
        if current_models == 'models':
            data['models_dir'] = str(source_default)
    if data.get('stt_language') == 'auto':
        data['stt_language'] = 'en'
    if data.get('stt_model') not in (None, 'tiny', 'small'):
        data['stt_model'] = 'small'
    if 'agent_script' not in data:
        for project in (ROOT.parent, ROOT.parent.parent):
            script = project / 'vh_cognitive_architecture_server/vh_cognitive_server.py'
            if script.is_file():
                data['agent_script'] = str(script)
                break
    if data.get('agent_script', '').endswith('server.py'):
        old_script = Path(data['agent_script'])
        renamed = old_script.with_name('vh_cognitive_server.py')
        if renamed.is_file():
            data['agent_script'] = str(renamed)
    if 'agent_python' not in data:
        for parent in ROOT.parents:
            candidate = parent / '.venv-vh-course' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
            if candidate.is_file():
                data['agent_python'] = str(candidate)
                break
    return Settings.model_validate(data)


cognitive_connection = CognitiveConnection(get_settings)
model_warmup = ModelWarmup(get_settings, MEDIA)


@asynccontextmanager
async def lifespan(app):
    monitor = asyncio.create_task(cognitive_connection.monitor())
    warmer = asyncio.create_task(model_warmup.run())
    model_warmup.request()
    try:
        yield
    finally:
        if shutdown_task is not None:
            shutdown_task.cancel()
        warmer.cancel()
        with suppress(asyncio.CancelledError):
            await warmer
        monitor.cancel()
        with suppress(asyncio.CancelledError):
            await monitor
        await cognitive_connection.stop()
        media.cleanup()


app = FastAPI(title='VH Embodiment Server — avatar client', version='0.1', lifespan=lifespan,
              description='Avatar with local Whisper/Piper. The external agent receives text only. Open the page before sending avatar commands.')
app.mount('/lib', StaticFiles(directory=ROOT / 'lib'), name='lib')
app.mount('/assets', StaticFiles(directory=ROOT / 'assets'), name='assets')
app.mount('/media', StaticFiles(directory=MEDIA), name='media')


@app.post('/api/shutdown')
async def shutdown(request: Request):
    # Require a custom header so another website cannot stop this local server.
    if request.headers.get('x-virtual-human') != 'shutdown':
        raise HTTPException(403, 'Invalid shutdown command.')
    if server_instance is None:
        raise HTTPException(409, 'Start the server with start.cmd or python server.py.')
    asyncio.get_running_loop().call_later(0.2, stop_server)
    return {'status': 'stopping'}


@app.get('/', include_in_schema=False)
def index():
    return FileResponse(ROOT / 'index.html')


MODEL_API_PATHS = {'/api/speak', '/api/catalog', '/api/status', '/api/whiteboard/images', '/api/audio', '/api/stop'}


@app.get('/model-openapi.json', include_in_schema=False)
def model_openapi():
    from fastapi.openapi.utils import get_openapi
    return get_openapi(title='VH Embodiment Server - Model API', version='0.1-preview',
                       routes=[route for route in app.routes if getattr(route, 'path', '') in MODEL_API_PATHS])


@app.get('/app.js', include_in_schema=False)
def app_js():
    return FileResponse(ROOT / 'app.js', media_type='text/javascript')


@app.get('/avatar.js', include_in_schema=False)
def avatar_js():
    return FileResponse(ROOT / 'avatar.js', media_type='text/javascript')


@app.get('/chat-window.js', include_in_schema=False)
def chat_window_js():
    return FileResponse(ROOT / 'chat-window.js', media_type='text/javascript')


@app.get('/heartbeat')
def heartbeat():
    return {'status': 'ok', 'service': 'VH Embodiment Server'}


@app.get('/api/status', response_model=StatusResponse)
def status():
    return StatusResponse(browser_connected=client is not None, agent_configured=bool(get_settings().agent_url), state=state)


@app.post('/api/paths/select')
async def browse_path(request: Request, kind: Literal['cognitive', 'python', 'models']):
    if request.headers.get('x-virtual-human') != 'agent':
        raise HTTPException(403, 'Invalid folder selection command.')
    return {'path': await run_in_threadpool(select_path, kind)}


@app.get('/api/agent/status')
async def agent_status():
    return cognitive_connection.status()


@app.post('/api/agent/{action}')
async def agent_control(action: str, request: Request):
    if request.headers.get('x-virtual-human') != 'agent':
        raise HTTPException(403, 'Invalid agent command.')
    if action == 'heartbeat':
        await cognitive_connection.check()
    elif action == 'start':
        await cognitive_connection.start()
        for _ in range(8):
            if await cognitive_connection.check():
                break
            if cognitive_connection.process is None or cognitive_connection.process.poll() is not None:
                raise HTTPException(503, 'Cognitive server exited. Check cognitive-server.log.')
            await asyncio.sleep(0.25)
        else:
            raise HTTPException(504, 'Cognitive server has not answered its heartbeat yet. Check its URL and log.')
    elif action == 'stop':
        await cognitive_connection.stop()
    elif action == 'test':
        settings = get_settings()
        if not settings.agent_enabled:
            raise HTTPException(409, 'Enable the agent connection first.')
        try:
            async with httpx.AsyncClient(timeout=30) as http:
                response = await http.post(settings.agent_url, json={'text': 'Hello'})
                response.raise_for_status()
            return AgentReply.model_validate(response.json()).model_dump()
        except (httpx.HTTPError, ValueError) as error:
            raise HTTPException(502, f'Agent test failed: {error}') from error
    else:
        raise HTTPException(404, 'Unknown agent command.')
    return cognitive_connection.status()


@app.get('/api/settings', response_model=Settings)
def settings():
    return get_settings()


@app.put('/api/settings', response_model=Settings)
async def save_settings(request: Settings):
    temporary = CONFIG.with_suffix('.tmp')
    temporary.write_text(request.model_dump_json(indent=2), encoding='utf-8')
    temporary.replace(CONFIG)
    model_warmup.request()
    return request


async def render_reply(request: SpeakRequest, settings: Settings):
    validate_reply(request)
    if not settings.speech_enabled or model_warmup.disabled:
        return request.model_copy(update={'audio_url': None})
    if request.audio_url or not (request.speech_text or '').strip():
        return request
    await progress('Preparing speech…')
    try:
        url = await run_in_threadpool(speech.synthesize, request.speech_text, settings, MEDIA)
    except (FileNotFoundError, speech.SpeechDeviceError) as exc:
        raise HTTPException(503, str(exc)) from exc
    except Exception as exc:
        logger.exception('TTS failed')
        raise HTTPException(503, 'Speech generation failed.') from exc
    stats = dict(tts_device.last_run)
    # Bound generated audio on disk; input uploads and board images are separate.
    files = sorted(MEDIA.glob('*.wav'), key=lambda path: path.stat().st_mtime, reverse=True)
    total = 0
    for index, path in enumerate(files):
        total += path.stat().st_size
        if index >= 20 or (total > 64 * 1024 * 1024 and index > 0):
            path.unlink(missing_ok=True)
    return request.model_copy(update={'audio_url': url, 'diagnostics': stats})


def validate_reply(reply):
    """Validate the catalog before starting speech or changing the scene."""
    if reply.expression:
        reaction(reply.expression)
    if reply.gesture:
        gesture_item(reply.gesture)
    if reply.whiteboard and reply.whiteboard.type == 'image':
        if not (MEDIA / Path(reply.whiteboard.image_url).name).is_file():
            raise HTTPException(422, 'Image unavailable: upload it to /api/whiteboard/images.')


async def ask_agent(text: str, settings: Settings):
    if not settings.agent_enabled or not settings.agent_url:
        trace('AGENT', {'status': 'not configured', 'text': text})
        return ChatResult(text=text)
    await progress('Agent is writing…')
    agent_started = time.perf_counter()
    trace('AVATAR -> AGENT', {'text': text})
    try:
        async with httpx.AsyncClient(timeout=60, follow_redirects=False) as http:
            response = await http.post(settings.agent_url, json={'text': text})
            response.raise_for_status()
        data = response.json()
        reply = AgentReply.model_validate(data)
        trace('AGENT -> AVATAR', reply.model_dump())
    except (httpx.HTTPError, ValueError, ValidationError) as exc:
        logger.warning('Agent response failed: %s', exc)
        raise HTTPException(502, 'Agent API unavailable or invalid response. Check the URL and schema in /docs.') from exc
    agent_seconds = round(time.perf_counter() - agent_started, 3)
    rendered = await render_reply(SpeakRequest(**reply.model_dump(exclude_none=True)), settings)
    rendered = rendered.model_copy(update={'diagnostics': {**(rendered.diagnostics or {}), 'agent_seconds': agent_seconds}})
    trace('AVATAR -> BROWSER', rendered.model_dump())
    return ChatResult(text=text, reply=rendered)


@app.post('/api/chat', response_model=ChatResult)
async def chat(request: TextInput):
    """Send only {text} to the configured agent, then synthesize its reply locally."""
    add_input(kind='text', text=request.text)
    trace('TEXT INPUT', request.model_dump())
    return await ask_agent(request.text, get_settings())


@app.post('/api/voice-chat', response_model=ChatResult)
async def voice_chat(audio: UploadFile = File(...), request_id: str = Form(default='', max_length=100)):
    """Local STT -> text-only agent -> local TTS. The agent never receives audio."""
    settings = get_settings()
    trace('AUDIO INPUT', {'file': audio.filename, 'type': audio.content_type})
    await progress('Transcribing voice message…')
    saved = await save_audio(audio)
    path = MEDIA / Path(saved.audio_url).name
    diagnostics = {}
    try:
        text = await run_in_threadpool(speech.transcribe, path, settings, diagnostics)
    except speech.AudioInputError as exc:
        logger.info('Voice input rejected: %s; %s', exc, diagnostics)
        raise HTTPException(400, {'message': str(exc), 'stage': 'stt', 'diagnostics': diagnostics}) from exc
    except FileNotFoundError as exc:
        raise HTTPException(503, {'message': str(exc), 'stage': 'stt', 'diagnostics': diagnostics}) from exc
    except speech.SpeechDeviceError as exc:
        raise HTTPException(503, {'message': str(exc), 'stage': 'device', 'diagnostics': diagnostics}) from exc
    except (MemoryError, RuntimeError) as exc:
        if isinstance(exc, MemoryError) or 'memory' in str(exc).lower():
            logger.exception('Not enough memory for speech recognition')
            raise HTTPException(503, {'message': 'Not enough memory for transcription. Close other server instances or large applications and retry.',
                                      'stage': 'model', 'diagnostics': diagnostics}) from exc
        logger.exception('Speech model failed')
        raise HTTPException(503, {'message': 'Speech model failed: check the server configuration.',
                                  'stage': 'model', 'diagnostics': diagnostics}) from exc
    except Exception as exc:
        logger.exception('STT failed')
        raise HTTPException(422, {'message': 'Cannot read the recording. Replay it or try the selected microphone again.',
                                  'stage': 'stt', 'diagnostics': diagnostics}) from exc
    finally:
        path.unlink(missing_ok=True)
    add_input(kind='text', text=text)
    trace('TRANSCRIPT', {'text': text})
    if client is not None:
        try:
            await client.send_json({'kind': 'transcript', 'data': {'text': text, 'request_id': request_id}})
        except (RuntimeError, WebSocketDisconnect, OSError):
            pass
    try:
        result = await ask_agent(text, settings)
    except HTTPException as exc:
        # Preserve a successful transcription even when the agent or TTS fails.
        raise HTTPException(exc.status_code, {'message': exc.detail, 'stage': 'reply',
                            'transcript': text, 'diagnostics': diagnostics}) from exc
    logger.info('Voice transcription completed: %s', diagnostics)
    return result.model_copy(update={'diagnostics': diagnostics})


@app.get('/api/speech/device')
def speech_device():
    return tts_device.status(get_settings())


@app.post('/api/speech/prepare')
async def prepare_speech():
    settings = get_settings()
    try:
        url = await run_in_threadpool(speech.synthesize, 'Prova della voce.' if settings.language == 'it' else 'Voice test.', settings, MEDIA)
        (MEDIA / url.rsplit('/', 1)[1]).unlink(missing_ok=True)
        return {'status': 'ready', 'diagnostics': dict(tts_device.last_run)}
    except (FileNotFoundError, speech.SpeechDeviceError) as exc:
        raise HTTPException(503, str(exc)) from exc
    except Exception as exc:
        logger.exception('Voice preparation failed')
        raise HTTPException(503, 'Speech preparation failed. Check the server log.') from exc


@app.post('/api/models/retry')
async def retry_models(request: Request):
    if request.headers.get('x-virtual-human') != 'agent':
        raise HTTPException(403, 'Invalid speech command.')
    model_warmup.request(force=True)
    return model_warmup.status


@app.post('/api/models/skip')
async def skip_speech_models(request: Request):
    if request.headers.get('x-virtual-human') != 'agent':
        raise HTTPException(403, 'Invalid speech command.')
    model_warmup.skip()
    return model_warmup.status


@app.get('/api/logs')
def logs():
    cognitive_log = Path(get_settings().agent_script).parent / 'cognitive-server.log'
    return {'embodiment': server_logs.tail(ROOT / 'embodiment-server.log'), 'cognitive': server_logs.tail(cognitive_log)}


@app.get('/api/models/warmup')
def warmup_status():
    return model_warmup.status


@app.get('/api/models')
def local_models():
    return {'installed': installed_whisper(speech.models_path(get_settings()))}


@app.get('/api/transcribe/device')
def transcription_device():
    return speech.stt_device.status(get_settings())


@app.post('/api/transcribe/prepare')
async def prepare_transcription():
    """Prepare the installed local STT model before recording. No downloads."""
    try:
        diagnostics = await run_in_threadpool(speech.prepare_preview, get_settings())
    except speech.SpeechDeviceError as exc:
        raise HTTPException(503, str(exc)) from exc
    except Exception as exc:
        logger.warning('Cannot prepare live transcription: %s', type(exc).__name__)
        raise HTTPException(503, 'Cannot prepare the selected model. Check the installed model folder and processing device.') from exc
    return {'status': 'ready', 'diagnostics': diagnostics}


@app.post('/api/transcribe', response_model=ChatResult)
async def transcribe_preview(audio: UploadFile = File(...)):
    """Provisional transcript of a growing recording. Never contacts the agent or TTS."""
    saved = await save_audio(audio)
    path = MEDIA / Path(saved.audio_url).name
    diagnostics = {}
    try:
        text = await run_in_threadpool(speech.transcribe, path, get_settings(), diagnostics, preview=True)
        return ChatResult(text=text, diagnostics=diagnostics)
    except speech.AudioInputError:
        # Silence/short input is normal while the user is still speaking.
        return ChatResult(text='', diagnostics=diagnostics)
    except (FileNotFoundError, speech.SpeechDeviceError) as exc:
        raise HTTPException(503, str(exc)) from exc
    except Exception as exc:
        logger.warning('Live transcription unavailable: %s', type(exc).__name__)
        raise HTTPException(503, 'Preview unavailable; complete transcription will run on send.') from exc
    finally:
        path.unlink(missing_ok=True)


@app.post('/api/conversation/clear')
async def clear_conversation():
    """Clear local history; notify the agent on a best-effort basis."""
    inputs.clear()
    settings = get_settings()
    if settings.agent_enabled and settings.agent_url:
        url = httpx.URL(settings.agent_url)
        base_path = url.path.rsplit('/', 1)[0]
        url = url.copy_with(path=base_path + '/conversation/clear', query=None, fragment=None)
        trace('AVATAR -> AGENT RESET', {'url': str(url), 'payload': {}})
        try:
            async with httpx.AsyncClient(timeout=2, follow_redirects=False) as http:
                response = await http.post(url, json={})
                response.raise_for_status()
        except httpx.HTTPError as exc:
            trace('AGENT RESET UNAVAILABLE', {'error': type(exc).__name__})
    return {'status': 'ok'}


async def command(kind, data=None):
    if client is None:
        raise HTTPException(503, 'Open the avatar page in the browser before sending commands.')
    command_id = uuid.uuid4().hex
    future = asyncio.get_running_loop().create_future()
    pending[command_id] = future
    try:
        await client.send_json({'id': command_id, 'kind': kind, 'data': data or {}})
        result = await asyncio.wait_for(future, timeout=15)
        if result.get('error'):
            raise HTTPException(422, result['error'])
        return CommandResult(command_id=command_id, state=AvatarState.model_validate(result['state']))
    except asyncio.TimeoutError:
        raise HTTPException(504, 'The browser did not acknowledge the command within 15 seconds.')
    except (RuntimeError, WebSocketDisconnect):
        raise HTTPException(503, 'Browser disconnected.')
    finally:
        pending.pop(command_id, None)


@app.post('/api/speak', response_model=CommandResult)
async def speak(request: SpeakRequest):
    """Test an agent reply: generate local TTS if no audio URL is supplied, then animate."""
    if client is None:
        raise HTTPException(503, 'Open the avatar page before running the request.')
    trace('MANUAL REPLY', request.model_dump())
    reply = await render_reply(request, get_settings())
    trace('AVATAR -> BROWSER', reply.model_dump())
    return await command('receive', reply.model_dump())


@app.post('/api/whiteboard/images')
async def upload_image(file: UploadFile = File(...)):
    """Upload a PNG, JPEG or WebP; use the returned image_url in whiteboard."""
    try:
        data = await file.read(8 * 1024 * 1024 + 1)
        if not data or len(data) > 8 * 1024 * 1024:
            raise HTTPException(413, 'Image is empty or exceeds 8 MB.')
        try:
            with Image.open(BytesIO(data)) as image:
                if image.format not in ('PNG', 'JPEG', 'WEBP') or image.width * image.height > 16_000_000:
                    raise HTTPException(422, 'Use PNG, JPEG or WebP, up to 16 megapixels.')
                name = 'board-' + uuid.uuid4().hex + '.png'
                image.convert('RGBA').save(MEDIA / name, format='PNG')
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
            raise HTTPException(422, 'Invalid image.') from exc
        return {'image_url': '/media/' + name}
    finally:
        await file.close()


def reaction(name):
    item = next((item for item in CATALOG['expressions']
                 if name == item['id'] or name in item['aliases']), None)
    if item is None:
        raise HTTPException(422, 'Unknown expression. See /api/catalog.')
    return item


@app.get('/api/catalog')
def motion_catalog():
    return CATALOG


@app.post('/api/expression', response_model=CommandResult)
async def expression(request: ExpressionRequest):
    reaction(request.expression)
    return await command('expression', request.model_dump())


def gesture_item(name):
    item = next((item for item in motion_catalog()['gestures'] if item['id'] == name), None)
    if item is None:
        raise HTTPException(422, 'Unknown gesture. See /api/catalog.')
    return item


@app.post('/api/gesture', response_model=CommandResult)
async def gesture(request: GestureRequest):
    gesture_item(request.gesture)
    return await command('gesture', request.model_dump())


@app.post('/api/avatar', response_model=CommandResult)
async def character(request: CharacterRequest):
    result = await command('character', request.model_dump())
    await save_settings(get_settings().model_copy(update={'character': request.character}))
    return result


@app.post('/api/motion/stop', response_model=CommandResult)
async def stop_motion(request: MotionStopRequest):
    return await command('motion-stop', request.model_dump())


@app.post('/api/reset', response_model=CommandResult)
async def reset_motion():
    return await command('reset')


@app.post('/api/mood', response_model=CommandResult)
async def mood(request: MoodRequest):
    return await command('mood', request.model_dump())


@app.post('/api/view', response_model=CommandResult)
async def view(request: ViewRequest):
    return await command('view', request.model_dump())


@app.post('/api/stop', response_model=CommandResult)
async def stop():
    return await command('stop')


@app.get('/api/inputs', response_model=list[InputEvent])
def get_inputs(after: int = Query(default=0, ge=0)):
    """Latest 100 inputs in memory. Poll with after=last_seen_id. No automatic replies."""
    return [event for event in inputs if event.id > after]


def add_input(**fields):
    global sequence
    sequence += 1
    event = InputEvent(id=sequence, **fields)
    inputs.append(event)
    return event


@app.post('/api/inputs/text', response_model=InputEvent)
def text_input(request: TextInput):
    return add_input(kind='text', text=request.text)


async def save_audio(audio: UploadFile) -> AudioFile:
    try:
        data = await audio.read(20 * 1024 * 1024 + 1)
        if not data:
            raise HTTPException(400, 'Empty audio.')
        if len(data) > 20 * 1024 * 1024:
            raise HTTPException(413, 'Maximum 20 MB per audio file.')
        suffix = { 'audio/wav': '.wav', 'audio/x-wav': '.wav', 'audio/webm': '.webm',
                   'audio/mp4': '.mp4', 'audio/mpeg': '.mp3', 'audio/ogg': '.ogg' }.get((audio.content_type or '').split(';')[0])
        if not suffix:
            raise HTTPException(415, 'Unsupported audio format. Use WAV, WebM, MP4, MP3 or OGG.')
        name = uuid.uuid4().hex + suffix
        (MEDIA / name).write_bytes(data)
        return AudioFile(audio_url='/media/' + name, mime_type=audio.content_type)
    finally:
        await audio.close()


@app.post('/api/audio', response_model=AudioFile)
async def upload_audio(audio: UploadFile = File(...)):
    """Upload audio supplied by an external agent, then use its URL in /api/speak."""
    return await save_audio(audio)


@app.post('/api/inputs/audio', response_model=InputEvent)
async def audio_input(audio: UploadFile = File(...)):
    saved = await save_audio(audio)
    return add_input(kind='audio', **saved.model_dump())


@app.websocket('/ws')
async def browser_socket(socket: WebSocket):
    global client, state, shutdown_task
    origin = socket.headers.get('origin')
    if origin and origin not in (f'http://127.0.0.1:{SERVER_PORT}', f'http://localhost:{SERVER_PORT}'):
        await socket.close(code=1008)
        return
    await socket.accept()
    if client is not None:
        await socket.close(code=1008, reason='An avatar is already connected. Close the first tab.')
        return
    if shutdown_task is not None:
        shutdown_task.cancel()
        shutdown_task = None
    client = socket
    try:
        while True:
            result = await socket.receive_json()
            if 'state' in result:
                state = AvatarState.model_validate(result['state'])
            future = pending.get(result.get('id'))
            if future is not None and not future.done():
                future.set_result(result)
    except (WebSocketDisconnect, ValueError):
        pass
    finally:
        client = None
        if server_instance is not None and not server_instance.should_exit:
            shutdown_task = asyncio.create_task(stop_after_browser_close())
        for future in pending.values():
            if not future.done():
                future.set_exception(WebSocketDisconnect())


if __name__ == '__main__':
    import sys
    import uvicorn
    import threading
    import webbrowser
    sys.stdout.reconfigure(errors='backslashreplace')
    server_logs.capture(ROOT / 'embodiment-server.log')
    # Reuse this service instead of launching another copy on the same port.
    try:
        existing = httpx.get(f'http://127.0.0.1:{SERVER_PORT}/heartbeat', timeout=1, trust_env=False)
        if existing.json().get('service') == 'VH Embodiment Server':
            print(f'VH Embodiment Server is already running on port {SERVER_PORT}.')
            if os.environ.get('VH_OPEN_BROWSER', '1') == '1':
                webbrowser.open(f'http://127.0.0.1:{SERVER_PORT}/')
            raise SystemExit(0)
    except (httpx.HTTPError, ValueError, AttributeError):
        pass
    print(f'Avatar: http://127.0.0.1:{SERVER_PORT} | API: http://127.0.0.1:{SERVER_PORT}/docs')
    print('Close the avatar browser tab or press Ctrl+C to stop the local servers.')
    print('Closing the avatar page stops the server after 8 seconds.')
    class QuietPolling(logging.Filter):
        def filter(self, record):
            return not (isinstance(record.args, tuple) and len(record.args) > 2 and
                        str(record.args[2]).split('?')[0] in ('/heartbeat', '/api/agent/status', '/api/models/warmup', '/api/logs'))
    logging.getLogger('uvicorn.access').addFilter(QuietPolling())
    server_instance = uvicorn.Server(uvicorn.Config(
        app, host='127.0.0.1', port=SERVER_PORT, timeout_graceful_shutdown=3))
    if os.environ.get('VH_OPEN_BROWSER', '1') == '1':
        def open_when_ready():
            import time
            for _ in range(100):
                try:
                    response = httpx.get(f'http://127.0.0.1:{SERVER_PORT}/heartbeat', timeout=1, trust_env=False)
                    if response.json().get('service') == 'VH Embodiment Server':
                        webbrowser.open(f'http://127.0.0.1:{SERVER_PORT}/')
                        return
                except (httpx.HTTPError, ValueError):
                    pass
                if server_instance.should_exit:
                    return
                time.sleep(.2)
        threading.Thread(target=open_when_ready, daemon=True).start()
    server_instance.run()
