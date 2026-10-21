# Part 1 project setup

This guide prepares Stefano Calzolari's Unity and Python starter for the Part 1 exercises. The download contains the scripts and animations, with Camila supplied as an importable package. You still build the Unity scene and complete the marked exercises during Part 1.

## 1. Install the software

Allow about 25 GB of free space for Unity, its import cache and the project dependencies. The first Unity import can take more than ten minutes.

| Software | Required version or setting |
|---|---|
| [Unity Hub](https://unity.com/download) | Sign in and activate a licence appropriate to your use |
| [Unity Editor](https://unity.com/releases/editor/archive) | **6000.3.26f1**, as specified in `ProjectSettings/ProjectVersion.txt` |
| [Python](https://www.python.org/downloads/) | **3.12.x** for this project's speech dependencies |
| [VS Code](https://code.visualstudio.com/download) | Microsoft Python extension |
| [Ollama](https://ollama.com/download) | Install the app and sign in with your Ollama account |

In Unity Hub, use **Installs > Install Editor > Archive** to find the exact editor version. Extra Android or iOS modules are not required for the editor exercises. On Windows, add Python to PATH during installation and reopen the terminal afterwards.

The Python **3.13** environment at the cognitive architectures repository root is for that course's notebooks. The Part 1 speech server uses its own **Python 3.12** environment inside `PythonProject`.

## 2. Download and extract the project

Use [Part_1_Project_and_Camila.zip](https://github.com/alessandropec/virtual-humans-cognitive-architectures/releases/download/part1-2026-10-21/Part_1_Project_and_Camila.zip), hosted in this repository's [Part 1 Release](https://github.com/alessandropec/virtual-humans-cognitive-architectures/releases/tag/part1-2026-10-21).

Extract to a short path without spaces or accents, for example `C:/VH/`. After extraction:

```text
C:/VH/Part_1_Virtual_Humans/
  README.md
  SETUP.md
  Camila_Character.unitypackage
  VH_Starter_Project/
    UnityProject/
    PythonProject/
    to_import/
```

If you already cloned the repository or used **Code > Download ZIP**, keep that copy and download [Camila_Character.unitypackage](https://github.com/alessandropec/virtual-humans-cognitive-architectures/releases/download/part1-2026-10-21/Camila_Character.unitypackage) separately. Camila is a Release attachment and is not part of the Git file tree.

## 3. Open Unity and import Camila

1. In Unity Hub, choose **Projects > Add > Add project from disk** and select `VH_Starter_Project/UnityProject`. Select the folder containing `Assets`, `Packages` and `ProjectSettings`.
2. Open it with **6000.3.26f1** and let Unity finish importing packages and compiling scripts.
3. Choose **Assets > Import Package > Custom Package...** and select `Camila_Character.unitypackage` from the extracted download.
4. Leave the package contents selected and click **Import**.
5. In the Project window, select `Assets/Characters/Camila_URP`. Check that the preview shows normal materials. The original `CC4_Camila_DEMO` uses HDRP materials and may appear pink in this URP project.

The starter has no completed `.unity` scene. An empty scene or Game view at this stage is expected. Follow Stefano's Part 1 lesson to create the scene, place the prefab and wire its components. Importing the character is a setup step, rather than the full scene construction.

## 4. Prepare OVRLipSync

Download **OVRLipSync 29.0.0** from [Meta's download page](https://developers.meta.com/horizon/downloads/package/oculus-lipsync-unity/) and accept its terms. The ZIP contains `OculusLipSync.unitypackage`.

For preparation before class, keep this download ready. In Part 1 Hour 3, import the package with **Assets > Import Package > Custom Package...**, then follow the lesson to copy `to_import/VisemeDriver.cs` into `UnityProject/Assets/Scripts/` and apply `to_import/VisemePreset.txt` to the component. Missing OVRLipSync types can appear in the Console before this dependency is imported.

Download this component yourself. It is not included in our combined archive.

## 5. Create the Python 3.12 environment

Open **`VH_Starter_Project/PythonProject`** in VS Code. Open its integrated terminal and check that you are in the folder containing `main.py` and `requirements.txt`.

On Windows PowerShell:

```powershell
py -3.12 --version
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

These commands use the environment's Python directly, so PowerShell script activation is optional. Copy `.env.example` only when creating your configuration for the first time, to preserve any existing settings.

On macOS/Linux:

```bash
python3.12 --version
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
```

In VS Code, run **Python: Select Interpreter** and select `PythonProject/.venv`. Install from this project's `requirements.txt`, which includes the speech packages. Installing only the requirements at the cognitive architectures repository root will not prepare the Part 1 server.

## 6. Start Ollama and test the model

Keep the Ollama app running, sign in and test it in a terminal:

```text
ollama signin
ollama run gpt-oss:120b-cloud "Say hello in one sentence"
```

This is the model specified by Part 1. It runs remotely through the local Ollama app, subject to the provider's account limits. The Python project connects to the app at `http://localhost:11434` by default. This path uses the app's signed-in session.

You can make the settings explicit in `PythonProject/.env`:

```dotenv
LLM_MODEL=gpt-oss:120b-cloud
LLM_HOST=http://localhost:11434
TTS_LANGUAGE=en
```

The cognitive architectures notebooks' `llm_provider_api_key.yaml` is a separate configuration. The original Part 1 server reads its own `.env`.

## 7. Download the speech models

The server loads local model files when it starts. Both Whisper and Piper are needed even when testing the text endpoint, because `main.py` imports the speech modules.

- [Whisper small](https://huggingface.co/Systran/faster-whisper-small/tree/main): download `config.json`, `model.bin`, `tokenizer.json` and `vocabulary.txt`.
- [Piper English voice](https://huggingface.co/rhasspy/piper-voices/tree/main/en/en_US/hfc_female/medium): download `en_US-hfc_female-medium.onnx` and `en_US-hfc_female-medium.onnx.json`.

Place the actual files, rather than web pages or an extra nested model directory, in this layout:

```text
PythonProject/models/
  faster-whisper-small/
    config.json
    model.bin
    tokenizer.json
    vocabulary.txt
  piper-voice-en_US-hfc_female-medium/
    en_US-hfc_female-medium.onnx
    en_US-hfc_female-medium.onnx.json
```

For Italian speech, optionally download [Piper Serena high](https://huggingface.co/rhasspy/piper-voices/tree/main/it/it_IT/serena/high) into `models/piper-voice-it_IT-serena-high/`, with its `.onnx` and `.onnx.json` files together. Set `TTS_LANGUAGE=it` and `WHISPER_LANGUAGE=it` in `.env`.

No GPU is required by the course setup. Whisper's supplied implementation can fall back to the CPU. If necessary, set `WHISPER_DEVICE=cpu` in `.env`.

## 8. Start and check the server

From **`PythonProject`**, run on Windows:

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

On macOS/Linux:

```bash
.venv/bin/python -m uvicorn main:app --reload --port 8000
```

Keep the terminal open. Open <http://127.0.0.1:8000/docs> in a browser. Use `GET /` to check the server's status and brain mode. In `POST /chat`, choose **Try it out** and submit:

```json
{"text": "Hello Camila"}
```

The uncompleted starter deliberately echoes the text and returns no generated speech from this endpoint. A successful HTTP response confirms that the API is running. It does not establish that the LLM, voice loop or Unity scene have been connected. Those connections are the marked `LIVE` and `TURN` exercises.

You can test the speech components separately from the same directory:

```powershell
.\.venv\Scripts\python.exe tts.py "Hello from Camila"
.\.venv\Scripts\python.exe stt.py "C:/path/to/your/recording.m4a"
```

The TTS test prints a path to a generated WAV under `static/audio`; play it to check the voice. The STT test requires your own recording. Allow microphone access in your operating system and Unity when setting up the later live voice loop.

## 9. Connect the completed Part 1 scene

Follow [Stefano's Part 1 materials](https://github.com/stevieTheTurtle/AI_powered_VH_2026-Part_1) for scene construction and the marked code blocks. Once those exercises are completed, start the Python server, open the scene you created and press **Play**. Check its API connection against the server running on port **8000**.

The Part 2 cognitive architecture will replace the reasoning behind `brain.py` through the existing `think(text)` interface and the response schema. Keep the working Part 1 project as a checkpoint before changing the agent.

## Troubleshooting

| Symptom | Check |
|---|---|
| Unity asks to upgrade the project | Install and choose **6000.3.26f1** |
| Camila is pink | Select `Camila_URP`, let imports finish and check URP settings before changing materials |
| No scene or character in Game view | The starter scene must be created during Part 1 |
| Missing OVRLipSync types | Import Meta's package at the lesson step before adding the dependent driver |
| Speech dependencies fail to install | Check that the interpreter is **Python 3.12** inside `PythonProject/.venv` |
| Whisper or Piper file not found | Compare the exact filenames and folder layout in step 7 |
| Server cannot import `main` | Run from `PythonProject`, where `main.py` is located |
| Port 8000 is already in use | Stop the previous course server with Ctrl+C in its terminal |
| Brain reports `echo` | Check the Ollama app is running and reachable at `LLM_HOST` |
| `/chat` echoes even though brain reports `llm` | The starter's server connection is still a placeholder until its exercise is completed |
| API works but the character does not speak | Finish the Part 1 scene, audio and pipeline connections |

Original installation reference: [Software_&_Downloads.md](Software_%26_Downloads.md). This guide adapts its paths to our combined Release download. Character and third-party licences are described in the [folder README](README.md#source-and-licences).
