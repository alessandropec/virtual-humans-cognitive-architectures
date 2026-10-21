# Part 1: Virtual Humans Foundations

Course material by **Stefano Calzolari, Politecnico di Torino**. This folder provides the Part 1 starter project alongside the cognitive architectures course.

- [Original Part 1 repository](https://github.com/stevieTheTurtle/AI_powered_VH_2026-Part_1), including slides published during the course.
- [Download project and Camila together](https://github.com/alessandropec/virtual-humans-cognitive-architectures/releases/download/part1-2026-10-21/Part_1_Project_and_Camila.zip).
- [Download Camila only](https://github.com/alessandropec/virtual-humans-cognitive-architectures/releases/download/part1-2026-10-21/Camila_Character.unitypackage) (about 249 MB).
- [Download page](https://github.com/alessandropec/virtual-humans-cognitive-architectures/releases/tag/part1-2026-10-21).

The character is hosted in this repository's **GitHub Releases**, rather than the Git file tree. **Code > Download ZIP** includes the starter project but not Camila. Use the combined download above to get both. Speech models and Meta OVRLipSync require separate downloads, as explained in the [software guide](Software_%26_Downloads.md).

Follow the [complete setup guide](SETUP.md) for installation, model downloads, server checks and troubleshooting.

## Open the Unity project

1. Install Unity Hub and **Unity 6000.3.26f1**.
2. Download and extract the combined ZIP to a short path without spaces, for example `C:/VH/`.
3. In Unity Hub, add and open `Part_1_Virtual_Humans/VH_Starter_Project/UnityProject`.
4. In Unity, choose **Assets > Import Package > Custom Package**, select `Part_1_Virtual_Humans/Camila_Character.unitypackage` and import it. If you downloaded the character separately, select that file instead.
5. Select `Assets/Characters/Camila_URP`. Its materials should look normal, rather than pink.

This is the **starter template**, not the completed Part 1 solution. The `Assets/Scenes` folder is initially empty, and blocks marked `LIVE` and `TURN` are course exercises. Follow Stefano's Part 1 materials to build the scene and connect the pipeline. Importing Camila alone does not produce a finished conversational agent.

## Part 1 Python server

The original Part 1 project requires **Python 3.12** and its own environment. The cognitive architectures notebooks use **Python 3.13** and the environment at the repository root. Keep these environments separate.

From `Part_1_Virtual_Humans/VH_Starter_Project/PythonProject`:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m uvicorn main:app --reload --port 8000
```

On macOS/Linux, use `python3.12 -m venv .venv`, `source .venv/bin/activate` and `cp .env.example .env`. Before starting the server, install Ollama and download the required speech models using the [original software guide](Software_%26_Downloads.md). API documentation: <http://127.0.0.1:8000/docs>. The starter still contains placeholder behaviour until the exercises are completed.

## Source and licences

Snapshot of upstream commit [`9490ebae66a7`](https://github.com/stevieTheTurtle/AI_powered_VH_2026-Part_1/tree/9490ebae66a7d2be017dbd271e965e252b577752), retrieved on 21 October 2026. The `VH_Starter_Project` files and original documents are copied without edits. This README and the download packaging are additions by Alessandro Emmanuel Pecora.

See [LICENSE.md](LICENSE.md) for the original code, document and third-party licences. Character Creator and Camila are credited to Reallusion and the original course authors. The character package retains its original `Assets/Characters/CHARACTER_LICENSE.md`. The course organiser confirms additional permission to distribute the package here; this does not place the character under the code's MIT licence or grant unrestricted reuse.

Camila SHA-256: `6edbe5e3275124e6073f4fdd01795a8180a1c970738b8c2a400f84315e743585`.

The [upstream README](UPSTREAM_README.md) documents the original distribution, in which Camila was supplied separately to participants. This repository's download arrangement is described above.
