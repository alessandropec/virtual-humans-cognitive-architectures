# VH Embodiment Server

A browser avatar with chat, local speech recognition, voice, facial expressions, gestures and an image whiteboard. Connect it to your Python agent or try behaviours directly in the API Playground.

## Requirements

- A 64-bit Windows computer, or macOS 14+ on Apple Silicon / Intel. The Mac package is a CPU preview.
- A browser with WebGL and microphone support. Allow microphone access when recording.
- Internet during installation. Speech and the Playground work locally afterward; an online LLM still needs Internet.

Resource estimates for planning, rather than guaranteed performance on every computer:

| Configuration | RAM | Free disk space |
| --- | --- | --- |
| CPU with Whisper Tiny | 4 GB | 6 GB |
| CPU with Whisper Small | 8 GB | 6 GB |
| Windows with NVIDIA acceleration | 8 GB and 4 GB GPU memory | 14 GB |

Both speech models are installed. GPU use is optional and needs a compatible NVIDIA driver already installed.

## Installation

Clone or download the whole repository and extract it before starting. Keep the installer in its original repository folder so setup can find the project.

### Windows

1. Open `virtual_human_project/vh_embodiment_server/dist/win/VirtualHuman-Setup.exe`.
2. If setup detects a compatible NVIDIA GPU, enable acceleration for transcription and/or voice to use it. Setup installs the required libraries. If no GPU is detected, leave CPU selected; it works without extra hardware.
3. Click **Install** and wait for the checks to finish. Keep **Launch after installation** selected to open the app automatically.
4. For later launches, open `virtual_human_project/installation/VirtualHuman.exe`.

### Mac

1. Extract `virtual_human_project/vh_embodiment_server/dist/mac/VirtualHuman-Mac-CPU-preview.zip` in its `dist/mac` folder.
2. Open `Install Virtual Human.app` and complete setup.
3. Open `Virtual Human.app` in your user Applications folder.

The Mac preview uses CPU. Use setup on each computer; the installed folder is not portable.

### What setup installs

| Location inside `virtual_human_project/` | Contents |
| --- | --- |
| `installation/` | Embodiment application, speech models and local settings |
| `.venv-vh-course/` | Shared Python 3.12 environment for both servers and all notebooks |
| `installation/.python/` | Private Python when a suitable existing Python is unavailable |

Setup installs Whisper Small and Tiny, plus four Piper voices: English/Italian, female/male. It reuses compatible environments and verified downloads. Select `.venv-vh-course` as the kernel in VS Code notebooks. Keep these folders in place.

### Update or reinstall

Close both servers, update the repository, then run the installer again from the same location. It reuses a compatible `.venv-vh-course` and verified models/downloads, and completes missing dependencies. There is no need to delete the environment or models. Select the NVIDIA options again if you want to keep using acceleration, then click **Install**.

### Downloads and releases

Use the installer in this repository's `dist/win` or `dist/mac` folder. The `speech-models-v1` GitHub release stores the speech model files used by setup: **you do not need to download them manually**. Setup downloads and checks the files it needs.

## First launch

1. The launcher opens `http://127.0.0.1:8899`. Wait for the avatar and speech models to load.
2. Check the connection indicator at the top. **Connecting...** means the cognitive server is being contacted; green means connected. Settings contains its start and restart controls.
3. Type a message or press the microphone, speak, then press it again to stop and send. **Use voice** switches avatar speech on or off.

**On a fresh download of the public repository, the mock agent is already selected.** Send any message: it replies **"Hello world"** every time. This is expected and confirms that the avatar and cognitive server are connected. No provider account or API key is needed for this test.

To program the agent, change its answer or connect an LLM, follow the [VH Cognitive Architecture Server guide](../vh_cognitive_architecture_server/README.md). That is where your Python agent code lives; this application handles chat, speech and the avatar.

Use **API Playground** to try avatar behaviours directly, without calling an agent.

### Main controls

| Area | Use |
| --- | --- |
| Conversation | Fixed chat on the left; message details show available timings and audio replay. The trash button clears the conversation. |
| Settings | Character, microphone and transcription, voice and cognitive server connection. Transcription and voice languages are independent. |
| API Playground | Compose and apply speech, emotion, expression, gesture and whiteboard changes without an agent. |
| Server logs | Read embodiment and cognitive output, including agent prints. |
| Camera setting | Open/close camera controls. Left-drag the avatar to move it, right-drag to rotate; scroll over the scene to zoom. |
| Whiteboard | Drag its surface to move it; drag the bottom-right corner to resize. |

Keep one avatar tab open. Closing it shuts down the embodiment and its connected local cognitive server after a short grace period. A page refresh keeps the session running. Stop the application before reinstalling.

## API reference

Use **`POST http://127.0.0.1:8899/api/speak`** with `Content-Type: application/json`. Keep the avatar page open. The API Playground provides a ready-to-run example without writing a client.

```json
{
  "speech_text": "Hello! Let us look at this together.",
  "emotion": "HAPPY",
  "expression": null,
  "gesture": "handup",
  "whiteboard": null
}
```

| Field | Value | Null or omitted |
| --- | --- | --- |
| `speech_text` | Text for the avatar to say | No new speech; empty text also works |
| `emotion` | Uppercase emotion from the catalog | Keep the current emotion |
| `expression` | Expression ID from the catalog | Do not start a new expression |
| `gesture` | One gesture name from the catalog | Do not start a new gesture |
| `whiteboard` | Image or clear command described below | Keep the current board |

Emotion starts neutral and persists until changed; send `NEUTRAL` to reset it. Expressions and gestures last **5 seconds**. Speech, emotion, expression and one gesture can run together. A new gesture replaces the previous gesture; null does not cancel it.

An accepted command returns `status: "applied"`; speech playback may still be running. Invalid fields or catalog values return **422**. An unavailable avatar or speech service can return **503**.

<details>
<summary>Emotion, expression and gesture catalog</summary>

**Emotions:** `NEUTRAL`, `HAPPY`, `ANGRY`, `SAD`, `FEAR`, `DISGUST`, `LOVE`, `SLEEP`.

**Expressions** (use the ID):

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

**Gestures** (use the name):

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

</details>

<details>
<summary>Whiteboard behaviour</summary>

The whiteboard is part of the same reply. In the supplied agents, the program sets it to null; the LLM does not choose board images.

Upload a PNG, JPEG or WebP in the Playground (up to 8 MB / 16 megapixels), then use the returned image URL in the reply:

```json
{"whiteboard":{"type":"image","image_url":"/media/board-0123456789abcdef0123456789abcdef.png"}}
```

The URL above is an example: use an image actually uploaded to this running server. Uploading alone does not display it. To clear the board:

```json
{"whiteboard":{"type":"clear"}}
```

An image command replaces the current image. Null preserves it. Failed image loads preserve the previous board. Uploaded images are temporary and disappear when the server stops.

</details>

<details>
<summary>Troubleshooting</summary>

- **Interrupted download:** retry setup. Verified files are reused; do not delete the installation or environment to fix a network error.
- **Missing speech models:** select their folder in Settings or continue without speech. Run setup to install missing models.
- **Incompatible Python environment:** follow the path-specific setup error. Setup does not silently delete an existing environment.
- **No agent reply:** check the connection indicator and **Server logs > Cognitive**. Try the mock agent first.
- **Unsigned installer:** the preview is unsigned. Follow your operating system or institution's policy for software supplied by the course.

</details>

## Credits and licences

The avatar is based on [TalkingHead](https://github.com/met4citizen/TalkingHead). Thank you to its authors and the open-source contributors who make this project possible.

Dependency licences are included in `app/lib/`. See [asset sources](app/assets/sources.json) and [speech model notices](app/assets/speech-model-licenses.txt) for attribution and model terms.
