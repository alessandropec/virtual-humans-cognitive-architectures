# Unity Virtual Human

**[Download Unity project and Camila](https://github.com/alessandropec/virtual-humans-cognitive-architectures/releases/download/unity-project/unity_virtual_human.zip)**

The download currently contains the definitive **Camila** character assets and a placeholder for the project. The final virtual human project will be added after Part 1 ends. Download it separately when you need Unity; the main course repository contains the guide and placeholder only.

Inside the downloaded ZIP:

```text
unity_virtual_human/
  Assets/Characters/   Camila model, prefab, materials and textures
  Project/             Placeholder for the final project
```

## Setup

1. Download the ZIP using the link above and extract it to a short path, for example `C:/VH/`. It contains the character assets. The normal course repository ZIP contains the notebooks, slides and this guide, with no large Unity assets.
2. Install [Unity Hub](https://unity.com/download), then install **Unity 6000.3.26f1** from the [editor archive](https://unity.com/releases/editor/archive).
3. The `Project/` folder is currently a placeholder. When the final project is added, open its Unity project folder through **Unity Hub > Add > Add project from disk**. Select the folder containing `Assets`, `Packages` and `ProjectSettings`.
4. If the project does not already contain Camila, copy this folder's `Assets/Characters` directory and `Assets/Characters.meta` into the Unity project's `Assets` directory. Keep every `.meta` file with its asset so prefab references remain intact.
5. Wait for Unity to finish importing. Select `Assets/Characters/Camila_URP` in the Project window and check that the character has normal colours. Use the URP prefab rather than the original HDRP model, which can appear pink.

To try the assets before the final project arrives, download the starter from the [Part 1 repository](https://github.com/stevieTheTurtle/AI_powered_VH_2026-Part_1), open `VH_Starter_Project/UnityProject` with the version above and copy the character assets as described in step 4. The starter scene and exercises are completed during Part 1.

## Python and voice setup

The original Part 1 server uses **Python 3.12**, while this course's cognitive architecture notebooks use **Python 3.13**. Keep their virtual environments separate.

For the Part 1 starter, open `VH_Starter_Project/PythonProject` in VS Code and run in PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Create `.env` only once, preserving any existing settings. On macOS/Linux, use `python3.12 -m venv .venv`, `.venv/bin/python -m pip install -r requirements.txt` and `cp .env.example .env`.

Install [Ollama](https://ollama.com/download), keep the app running, sign in and test the model used in Part 1:

```text
ollama signin
ollama run gpt-oss:120b-cloud "Say hello in one sentence"
```

Download [Whisper small](https://huggingface.co/Systran/faster-whisper-small/tree/main) and the [Piper English voice](https://huggingface.co/rhasspy/piper-voices/tree/main/en/en_US/hfc_female/medium). Place their files in the Python project's `models` folder:

```text
models/
  faster-whisper-small/
    config.json
    model.bin
    tokenizer.json
    vocabulary.txt
  piper-voice-en_US-hfc_female-medium/
    en_US-hfc_female-medium.onnx
    en_US-hfc_female-medium.onnx.json
```

From `PythonProject`, start the server:

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

On macOS/Linux, use `.venv/bin/python -m uvicorn main:app --reload --port 8000`. Open <http://127.0.0.1:8000/docs> to check the API. In the starter, `/chat` initially echoes the input until the Part 1 exercises are completed.

Download **OVRLipSync 29.0.0** separately from [Meta](https://developers.meta.com/horizon/downloads/package/oculus-lipsync-unity/) and follow the Part 1 lesson to import it. Speech models and OVRLipSync are not included in this folder.

The scene-opening and server instructions will be updated here when the final project is added. Camila will remain the same character.
