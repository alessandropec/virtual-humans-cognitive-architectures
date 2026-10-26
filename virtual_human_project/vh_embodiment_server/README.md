# Installation guide

Install and open **VH Embodiment Server**, the application that displays the avatar. Its installer also prepares Python, speech models and the connection to the cognitive server. You do not need a separate installation for the agent.

## Before you start

Download and extract the whole repository. Keep its folders together. You need Internet for setup and a browser with WebGL support.

Choose **Windows or Mac** below, then continue to **Try the chat**.

## Installation

### Windows

1. In the downloaded repository, open `virtual_human_project/vh_embodiment_server/dist/win/VirtualHuman-Setup.exe`.
2. If setup detects an NVIDIA GPU, you can enable acceleration for voice and transcription. Otherwise leave CPU selected.
3. Click **Install**. Leave **Launch after installation** checked: the avatar opens when setup finishes.

Next time, open `virtual_human_project/installation/VirtualHuman.exe`.

> **"Windows protected your PC"?** The course installer is not signed, so SmartScreen warns about it. Click **More info**, then **Run anyway**.

### Mac

1. Open `virtual_human_project/vh_embodiment_server/dist/mac/` and extract `VirtualHuman-Mac-CPU-preview.zip` there.
2. Open **Install Virtual Human.app** and complete setup.
3. Open **Virtual Human.app** in your user Applications folder.

Mac uses CPU; GPU acceleration is not supported. Keep **Install Virtual Human.app** inside `dist/mac/`: do not move it to Applications.

> **"Install Virtual Human" cannot be opened / Apple could not verify it?** The course installer is not signed by Apple. Close the message, open **System Settings → Privacy & Security**, scroll down to **Security** and click **Open Anyway** next to "Install Virtual Human", then confirm with your password. If Terminal asks to access the folder that contains the repository, click **Allow**.

## Try the chat

1. Wait for the avatar to appear and the connection indicator to turn green.
2. Type **Hello** and press **Send**.
3. The avatar replies **"Hello world"**. This confirms that the application and agent are connected.

![VH Embodiment Server connected, with the avatar and a Hello world reply](../docs/images/browser-ready.png)

You should see **Cognitive Architecture Server connected** and **Hello world**, as above.

The default mock agent always returns this fixed phrase. No LLM or API key is needed. To change the answer and build your own agent, continue to the [Agent guide](../vh_cognitive_architecture_server/README.md).

You can also use the microphone: press it to record and press it again to send. **Use voice** turns the avatar's voice on or off. Closing the avatar tab shuts down the local application.

<details>
<summary>Computer requirements</summary>

64-bit Windows, or macOS 14+ on Apple Silicon / Intel. A microphone is needed only for voice input.

| Configuration | RAM estimate | Free disk space |
| --- | --- | --- |
| CPU with Whisper Tiny | 4 GB | 6 GB |
| CPU with Whisper Small | 8 GB | 6 GB |
| Windows with NVIDIA acceleration | 8 GB and 4 GB GPU memory | 14 GB |

Setup installs both Whisper models. Small is the default; Tiny uses fewer resources. NVIDIA acceleration needs a compatible driver already installed.

</details>

<details>
<summary>Where the application is installed</summary>

Inside `virtual_human_project/`, setup creates `installation/` for the application and speech models, and `.venv-vh-course/` for the shared Python environment. Keep both folders in place. For course notebooks, select `.venv-vh-course` as the VS Code kernel.

</details>

<details>
<summary>Avatar controls</summary>

| Area | Use |
| --- | --- |
| Conversation | Fixed chat on the left; message details show available timings and audio replay. The trash button clears the conversation. |
| Settings | Character, microphone and transcription, voice and cognitive server connection. Transcription and voice languages are independent. |
| API Playground | Compose and apply speech, emotion, expression, gesture and whiteboard changes without an agent. |
| Server logs | Read embodiment and cognitive output, including agent prints. |
| Camera setting | Open/close camera controls. Left-drag the avatar to move it, right-drag to rotate; scroll over the scene to zoom. |
| Whiteboard | Drag its surface to move it; drag the bottom-right corner to resize. |

Keep one avatar tab open. Closing it shuts down the embodiment and its connected local cognitive server after a short grace period. A page refresh keeps the session running. Stop the application before reinstalling.

</details>

## API reference

<details>
<summary>Send an avatar reply with POST /api/speak</summary>

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

</details>

<details>
<summary>Troubleshooting</summary>

- **Interrupted download:** retry setup. Verified files are reused; do not delete the installation or environment to fix a network error.
- **Missing speech models:** select their folder in Settings or continue without speech. Run setup to install missing models.
- **Incompatible Python environment:** follow the path-specific setup error. Setup does not silently delete an existing environment.
- **No agent reply:** check the connection indicator and **Server logs > Cognitive**. Try the mock agent first.
- **Security warning when opening the installer:** the installers are unsigned. See the notes under [Windows](#windows) and [Mac](#mac).

</details>

## Credits and licences

The avatar is based on [TalkingHead](https://github.com/met4citizen/TalkingHead). Thank you to its authors and the open-source contributors who make this project possible.

Dependency licences are included in `app/lib/`. See [asset sources](app/assets/sources.json) and [speech model notices](app/assets/speech-model-licenses.txt) for attribution and model terms.
