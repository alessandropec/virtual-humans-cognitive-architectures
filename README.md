# AI-Powered Virtual Humans

**LLM-Powered Cognitive Architectures**

<img src="assets/course-teaser.png" alt="A virtual human holding a brain, connecting human cognition and artificial intelligence" width="960">

Build the Python agent behind a virtual human: from a first LLM call to conversation memory, structured behaviour and tools. The course connects psychological models of memory with the cognitive architectures used to give a virtual character continuity across interactions.

The course project connects a talking browser avatar to a Python cognitive architecture through a JSON API.

## Programme

| Module | Topics |
|---|---|
| **0 · Introduction and Setup** | Course project, model providers, Python environment and first LLM calls |
| **1 · Cognitive Architectures and Large Language Models** | Psychological foundations · LLMs, working memory and prompting · Introduction to LangChain |
| **2 · From Large Language Models to Virtual Humans** | LangGraph workflows · Stateful agents and conversation memory · Integration with the virtual human |
| **Webinar · The Virtual Meteorologist** | Extend the virtual human with tools and live weather data |

## Quick start

1. Clone this repository or choose **Code > Download ZIP**, then extract it. Keep the complete folder structure.
2. Open the installer inside the repository:
   - **Windows:** `virtual_human_project/vh_embodiment_server/dist/win/VirtualHuman-Setup.exe`.
   - **Mac:** extract `virtual_human_project/vh_embodiment_server/dist/mac/VirtualHuman-Mac-CPU-preview.zip` in that folder, then open `Install Virtual Human.app`.
3. If setup detects a compatible NVIDIA GPU, you can enable speech acceleration; otherwise use CPU. Click **Install**, then launch **VH Embodiment Server**: `virtual_human_project/installation/VirtualHuman.exe` on Windows, or `Virtual Human.app` in your user Applications folder on Mac.

The default mock agent replies **"Hello world"** to every message, so you can test the connection without an LLM or API key.

Setup prepares the shared Python environment and downloads the speech models automatically. For notebooks, select `virtual_human_project/.venv-vh-course` as the VS Code kernel.

## Project guides

- [Project overview](virtual_human_project/README.md): components and message flow.
- [Installation and first launch](virtual_human_project/vh_embodiment_server/README.md): requirements, setup and avatar controls.
- [Programming the agent](virtual_human_project/vh_cognitive_architecture_server/README.md): edit the Python agent and connect an LLM.

## Course materials

Slides and notebooks follow the `Module_*/Chapter_*` structure. Open a chapter README for its slide and code links.

Use VS Code with the Python and Jupyter extensions. Hosted LLM examples need your own provider key; the mock agent and API Playground do not.
