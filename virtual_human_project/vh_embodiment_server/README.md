# VH Embodiment Server

A browser avatar for the course: local speech recognition, speech generation, emotion, expression, gesture and an image whiteboard. Connect your own cognitive architecture server through a small JSON API.

Built with [TalkingHead](https://github.com/met4citizen/TalkingHead), [HeadAudio](https://github.com/met4citizen/HeadAudio), [Three.js](https://threejs.org/), [faster-whisper](https://github.com/SYSTRAN/faster-whisper), [Piper](https://github.com/OHF-Voice/piper1-gpl) and [FastAPI](https://fastapi.tiangolo.com/). Original licences and asset references are included in `app/lib/` and `app/assets/sources.json`.

## Installation

Use a browser with WebGL support. Allow microphone access to record.

Setup always installs into **`virtual_human_project/installation`**, alongside the two server folders. Open the installer from its `dist/win` or `dist/mac` folder inside the cloned repository. Paths are calculated on your computer; there is no installation-folder selection.

Setup prepares Python 3.12, dependencies, **Whisper Small + Tiny** and **four Piper voices** (English/Italian, female/male). Small is the default; choose Tiny on computers with limited resources. Julia uses a female voice and David a male voice.

Setup creates **`virtual_human_project/.venv-vh-course`**, the single Python 3.12 environment for both servers and all course notebooks. It installs the project [requirements.txt](../requirements.txt), including the repository's notebook dependencies. If this environment already exists, setup checks it and completes missing dependencies. If it is incompatible, rename or remove the indicated `.venv-vh-course` folder and run setup again. Setup never removes it automatically.

Server paths are connected automatically. In VS Code, select `virtual_human_project/.venv-vh-course` as the notebook kernel. Keep `installation` and `.venv-vh-course` in place; setup may store their base Python in `installation/.python`. No packages or models download at application startup.

### Recommended resources

| Use | RAM | Free disk space |
| --- | --- | --- |
| Windows or Mac, CPU, Tiny | 4 GB | 6 GB |
| Windows or Mac, CPU, Small | 8 GB | 6 GB |
| Windows, NVIDIA acceleration | 8 GB + GPU with 4 GB VRAM | 14 GB |

Both Whisper models are installed, so Tiny and Small need the same disk space. Download the [NVIDIA driver](https://www.nvidia.com/en-us/drivers/) separately; setup supplies the other GPU libraries.

Models are downloaded first from the course GitHub release, with their original pinned Hugging Face files as backup. Each file is checked before installation. Original model notices are in [speech-model-licenses.txt](app/assets/speech-model-licenses.txt); the English HFC cards identify non-commercial source-data terms.

Internet is needed for setup. Afterward, speech and the Playground work locally, with no model or package downloads during use. An online agent still needs Internet.

### Windows

1. Open **VirtualHuman-Setup.exe** on 64-bit Windows.
2. The installation folder is fixed at **`virtual_human_project\installation`**.
3. Select CPU, or enable NVIDIA acceleration independently for transcription and voice.
4. Wait for setup to finish, then open **VirtualHuman.exe**.

**Launch:** `virtual_human_project\installation\VirtualHuman.exe`. It opens [http://127.0.0.1:8899](http://127.0.0.1:8899) and starts the embodiment server. Close the app before a repair or update.

The course build is unsigned, so an unfamiliar-publisher warning is expected. For the installer received from the course, **Windows protected your PC > More info > Run anyway** allows it to start. This warning alone does not mean malware was detected. If your institution blocks this option, contact its IT support. See [Microsoft's explanation](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation).

### Mac

1. On **macOS 14+**, Apple Silicon or Intel, extract **VirtualHuman-Mac-CPU-preview.zip** inside its `dist/mac` folder in the repository.
2. Open **Install Virtual Human.app**. Setup uses **`virtual_human_project/installation`** automatically.
3. Confirm and wait for setup. Open **Virtual Human.app** in your user Applications folder; this launcher starts the installed embodiment.

Mac uses CPU; Homebrew is not needed. The package is an unsigned preview and still needs testing on a real Mac.

If macOS cannot verify the developer, this is expected for the unsigned course build. Try opening it once, then go to **System Settings > Privacy & Security > Open Anyway > Open**. Authenticate if asked. This grants an exception for that app. Use the package supplied by the course; an alert specifically reporting malware or damage is a different issue. See [Apple's instructions](https://support.apple.com/en-us/102445).

Use the installer on each computer; the installed folder is not a portable package.

## Interface

- **Server logs:** separate Embodiment and Cognitive tabs show server output, including agent `print()` calls. Source `start.cmd` also opens a dedicated cognitive log console on Windows.
- **Conversation:** type a message or record with Microphone, then Stop & send. Live transcription can show a draft while you speak.
- **Settings:** choose Julia or David, configure the agent URL, microphone, transcription model and processing devices. **Transcription language and Voice language are separate**, each English or Italian, both defaulting to English.
- **API Playground:** select speech, emotion, expression, one gesture and a whiteboard update. Inspect the generated JSON, run it and read the result. It works without an agent.
- **Camera:** Face, Upper body and Full body select the framing. Use **+ / -** or scroll over the avatar to zoom. Use the arrows or right-drag to move the avatar in the frame. Reset restores the selected view.
- **Whiteboard:** drag Move whiteboard or its bottom-right corner to move or resize it. Editing is always available; the board and both controls stay behind the avatar canvas. Settings can hide the board without erasing its image.

In **Settings > Cognitive Architecture Server**, the defaults are API `http://127.0.0.1:8000/agent` and heartbeat `http://127.0.0.1:8000/heartbeat`. The connection is checked every 3 seconds without calling the LLM or printing each heartbeat. Only connection changes are logged. Save settings, then use **Test heartbeat** or **Test cognitive API** (sends “Hello” to the selected agent).

Setup connects the shared environment and local server automatically. Use **Start Cognitive Architecture Server** and **Stop Cognitive Architecture Server** in Settings to restart it after code changes. Paths have Browse buttons if you need to change them. Settings save when you press Save or close the Settings window, including its X button.

Keep one avatar tab open. Closing it stops the embodiment and the connected local cognitive server and releases their ports after about 8 seconds. Refreshing the page during this interval keeps them running. A remote cognitive server is left running. Another program occupying a port is reported and is never terminated.

Starting with `start.cmd` or the launcher opens the browser automatically. A loading screen blocks the interface while the avatar and selected Whisper/Piper models prepare. It also appears when changing or testing models. Selected models stay in memory until the selection changes or the server stops; there are no runtime downloads. Errors close the loading screen and explain the problem. Save settings again after fixing an error to retry preparation.

## API reference

Base URL: `http://127.0.0.1:8899`. The avatar page must be connected for avatar commands. See [interactive API](http://127.0.0.1:8899/docs) for all endpoints and [avatar schema](http://127.0.0.1:8899/model-openapi.json) for the integration contract.

| Request | Purpose |
| --- | --- |
| `POST /api/speak` | Apply a reply JSON |
| `GET /api/catalog` | Available emotions, expressions and gestures |
| `GET /api/status` | Browser connection and avatar state |
| `POST /api/whiteboard/images` | Upload an image; multipart field `file` |
| `POST /api/audio` | Upload existing audio; multipart field `audio` |
| `POST /api/stop` | Stop speech |

### Reply JSON

Your agent returns this structure. The Playground and `POST /api/speak` use the same fields:

```json
{
  "speech_text": "Hello! Let us look at this together.",
  "emotion": "HAPPY",
  "expression": "😉",
  "gesture": "handup"
}
```

All fields are optional. The Playground sends unselected fields as **null**. Null or omission means keep the current state. The avatar starts neutral; null keeps its current emotion, while `NEUTRAL` resets it. Expressions and gestures last **5 seconds**. Emotion stays until changed. Empty or null speech does not start TTS.

**Emotion, expression and one gesture can run together**, alongside speech. A new gesture replaces the previous body movement. Emotion supplies the base facial mood; expression overlays it. Mouth expressions can blend with lip-sync. There is no word-level timing.

Only gestures are available. Use a plain catalog name such as `handup`, `shrug` or `namaste`. There are no type prefixes, pose choices, uploads or stop choice in the reply model.

```json
{"speech_text":null,"emotion":null,"expression":null,"gesture":"handup","whiteboard":null}
```

### Whiteboard images

`whiteboard` belongs to the same reply JSON and the same `POST /api/speak` API. The language model does not choose it: the agent program adds it when constructing `AgentReply`, currently always as `null`. Use the Playground to test an image, clear, or null (keep the current board).

Upload **PNG, JPEG or WebP**, up to **8 MB / 16 megapixels**, to `/api/whiteboard/images`. Use its returned `image_url`:

```json
{"whiteboard":{"type":"image","image_url":"/media/board-0123456789abcdef0123456789abcdef.png"}}
```
```json
{"whiteboard":{"type":"clear"}}
```

An image replaces the previous image; clear erases it; omitting `whiteboard` preserves it. Uploading alone does not display an image. Failed image loads preserve the previous image. Images are temporary until server shutdown; refreshing the avatar page clears its visible board.

Commands return `status: "applied"` after the browser accepts them, while playback can continue. Common errors: **422** invalid field or catalog ID, **413** oversized upload, **503** no connected avatar or unavailable speech service.

## API catalog

`GET /api/catalog` is the current catalog. Facial/body combinations are excluded.

**Emotions:** `NEUTRAL`, `HAPPY`, `SAD`, `ANGRY`, `FEAR`, `DISGUST`, `LOVE`, `SLEEP`.

### Expressions

Use the ID in `expression`.

| ID | Expression |
| --- | --- |
| 😐 | Puzzled |
| 😏 | Smirk |
| 🙂 | Gentle smile |
| 😊 | Warm smile |
| 😀 | Open smile |
| 😃 | Enthusiasm |
| 😄 | Joy |
| 😁 | Toothy smile |
| 😆 | Laughter |
| 😝 | Tongue out |
| 😂 | Intense laughter |
| 😉 | Wink |
| 😭 | Crying |
| 🥺 | Pleading |
| 😞 | Disappointment |
| 😔 | Sadness |
| 😳 | Surprise |
| ☹️ | Displeasure |
| 😚 | Kiss with closed eyes |
| 😘 | Kiss |
| 🥰 | Tenderness |
| 😍 | Admiration |
| 😡 | Anger |
| 😠 | Irritation |
| 😒 | Disapproval |
| 😱 | Fright |
| 😬 | Tension |
| 🙄 | Eye roll |
| 👀 | Side glance |
| 😴 | Drowsiness |

### Gestures

Use the name in `gesture`. Choose only one at a time.

| Name | Gesture |
| --- | --- |
| `handup` | Handup |
| `index` | Index |
| `ok` | Ok |
| `thumbup` | Thumb Up |
| `thumbdown` | Thumb Down |
| `side` | Side |
| `shrug` | Shrug |
| `namaste` | Namaste |
| `yes` | Nod |
| `no` | Shake head |

## Source files and builds

```text
app/           Application source, assets and browser libraries
build/win/     Windows builder, requirements and installer sources
build/mac/     Mac builder, requirements and installer sources
build/common/  Shared setup, packaging and guide helpers
dist/win/      Windows packages
dist/mac/      Mac packages
tests/         Automated checks
README.md      This guide; README.html is the in-app version
```

Edit `app/` to change the embodiment. To test without rebuilding or reinstalling, open `app/start.cmd` on Windows, or run `server.py` with the course Python from `app/` on Mac. Close the installed server first: both use port 8899. The default model path is always `virtual_human_project/installation/models`, even if that folder is missing. A custom folder can be selected and saved. If models are missing, the app shows the path and offers **Select models folder** or **Continue without speech models**. Continuing disables local transcription and voice generation for that session; text, avatar behaviour and the Playground still work. To download models, run the installation setup and launch the installed app. For HTML/JavaScript changes, reload with Ctrl+F5; for Python changes, restart the source server.

To rebuild later, use Python 3.12 and Node.js 22. From this folder, install the platform's requirements plus `build/common/requirements.txt`, then run:

```text
python build/win/build.py
python build/mac/build.py
```

Each script checks the app and writes its package to `dist/win/` or `dist/mac/`. The Windows builder runs on Windows; the Mac package still needs a native Mac test. To update only the in-app guide, run `python build/common/render_docs.py`.

If a download is interrupted, setup retries automatically up to five times, using IPv4 after a failed connection. If it stops, check your connection and click **Retry**, or close and reopen the installer. Completed files are verified and reused; matching partial downloads resume when the server supports it. **Do not delete the installation or environment folders to fix a connection error.**
