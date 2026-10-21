# Virtual Human Integration

- [Download Unity assets and Camila](https://github.com/alessandropec/virtual-humans-cognitive-architectures/releases/download/unity-project/unity_virtual_human.zip)
- [Download speech models](https://github.com/alessandropec/virtual-humans-cognitive-architectures/releases/download/unity-project/speech_models.zip)

[Part 1](https://github.com/stevieTheTurtle/AI_powered_VH_2026-Part_1) explains the Unity character and speech pipeline in detail. It is recommended but not required. Use this course's download, even if you already downloaded Part 1: it includes the Python bridge adapted for our LangChain integration and a common **Python 3.12** environment.

The five-file **Python server is in this repository**. The Release downloads contain **Camila** and the **Whisper small / Piper English and Italian speech models**. The completed **Unity project will be added after Part 1**; it is not included yet. The agent currently uses canned, stateless replies and needs no LLM account, API key or Ollama installation.

## Download and run

1. Download this course repository with **Code > Download ZIP** and extract it, or clone it with Git.
2. Download the **Unity assets** and **speech models** ZIPs linked above.
3. Extract **both ZIPs into the extracted course repository root**, merging their `unity_virtual_human` folder with the existing one. The archives already contain the correct paths.

The resulting folders are:

```text
course-repository/
  requirements.txt
  unity_virtual_human/
    Assets/Characters/           Camila, from the Unity ZIP
    PythonProject/
      main.py
      agent.py
      schemas.py
      stt.py
      tts.py
      speech_config.json
      models/                   from the speech models ZIP
        faster-whisper-small/
        piper-voice-en_US-hfc_female-medium/
        piper-voice-it_IT-serena-high/
```

The completed `UnityProject/` will be added to the Unity download after Part 1. The repository itself stays small: character assets and model weights are separate Release attachments. There is **one requirements.txt**, at the course repository root.

Use the same **Python 3.12** environment for the notebooks and server. From the course repository root, on Windows:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --app-dir unity_virtual_human/PythonProject --reload --port 8000
```

If the course environment already exists with Python 3.12, reuse it and install the updated requirements. On macOS/Linux use `python3.12 -m venv .venv` and `.venv/bin/python` in place of `.\.venv\Scripts\python.exe`.

The server's first speech request loads the local models and may take a little longer. Models work on the CPU; a GPU is not required. After installing the Python packages, speech processing uses the files included in the download.

## English and Italian

Whisper small recognizes both English and Italian. The models download includes an English Piper voice and the Italian **Serena** voice.

Edit `unity_virtual_human/PythonProject/speech_config.json`. For Italian replies and voice:

```json
{
  "language": "it",
  "stt_language": "auto"
}
```

Set `language` to `en` for English (the default), or `it` for Italian. This selects both the mock reply language and the voice. The server reads the settings on every request, so saving the file applies to the next turn without restarting.

With `stt_language: "auto"`, incoming speech can be English or Italian. Set it to `en` or `it` if you prefer to force recognition in one language. The reply language follows `language`, independently of the recognized input language. The JSON fields exchanged with Unity stay the same.

## The five Python files

| File | Responsibility |
|---|---|
| `main.py` | FastAPI server: coordinates input, agent and voice |
| `agent.py` | Mock replies now; LangChain and memory later |
| `schemas.py` | The JSON contract Unity reads |
| `stt.py` | Recording to text with Whisper |
| `tts.py` | Reply text to a WAV with Piper |

Unity is the HTTP client. It sends text to `POST /chat`, or a WAV file in the `audio` field to `POST /voice-chat`. Both routes call the same agent. Python returns the reply text, gesture, emotion and an audio URL. Unity downloads the WAV and plays it through the character's audio system.

Open <http://127.0.0.1:8000/docs> and try `POST /chat` with:

```json
{"text": "Hello Camila"}
```

The response has this shape:

```json
{
  "speech_text": "Hello! I am Camila.",
  "action": "WAVE",
  "emotion": "HAPPY",
  "audio_url": "/static/audio/<generated-file>.wav",
  "transcript": null,
  "brain": "mock"
}
```

`transcript` contains the recognized text for voice requests. If speech synthesis fails, the server still returns the text with `audio_url: null`. The mock deliberately has no conversation memory. The course will replace `agent.respond(text, language="en")` while preserving the Unity HTTP contract and the speech components. When adding LangChain, use the supplied `language` in the reply prompt so the agent and voice keep the same language.

Unity version: **6000.3.26f1**. Final scene-opening instructions will be added with the Unity project. Meta OVRLipSync remains a separate download under its own terms; follow Part 1 when that component is needed.
