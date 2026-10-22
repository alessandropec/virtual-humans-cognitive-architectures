# AI-Powered Virtual Humans

**LLM-Powered Cognitive Architectures**

<img src="assets/course-teaser.png" alt="A virtual human holding a brain, connecting human cognition and artificial intelligence" width="960">

Build the Python agent behind a virtual human: from a first LLM call to conversation memory, structured behaviour and tools. The course connects psychological models of memory with the cognitive architectures used to give a virtual character continuity across interactions.

The course uses our [VH Embodiment Server](virtual_human_project/README.md), built on TalkingHead and HeadAudio. The browser avatar connects to the Python cognitive architecture through a JSON API. Follow the [installation guide](virtual_human_project/vh_embodiment_server/README.md) to get started.

## Programme

| Module | Topics |
|---|---|
| **0 · Introduction and Setup** | Course project, model providers, Python environment and first LLM calls |
| **1 · Cognitive Architectures and Large Language Models** | Psychological foundations · LLMs, working memory and prompting · Introduction to LangChain |
| **2 · From Large Language Models to Virtual Humans** | LangGraph workflows · Stateful agents and conversation memory · Integration with the virtual human |
| **Webinar · The Virtual Meteorologist** | Extend the virtual human with tools and live weather data |

## Quick start

1. Clone or download the [course repository](https://github.com/alessandropec/virtual-humans-cognitive-architectures), then extract the ZIP if needed. Keep the complete folder structure.
2. Open the installer inside the repository:
   - **Windows:** `virtual_human_project/vh_embodiment_server/dist/win/VirtualHuman-Setup.exe`.
   - **Mac:** extract `virtual_human_project/vh_embodiment_server/dist/mac/VirtualHuman-Mac-CPU-preview.zip` in that folder, then open `Install Virtual Human.app`.
3. If setup detects a compatible NVIDIA GPU, you can enable speech acceleration; otherwise use CPU. Click **Install**, then launch **VH Embodiment Server**: `virtual_human_project/installation/VirtualHuman.exe` on Windows, or `Virtual Human.app` in your user Applications folder on Mac.

The public download starts with a mock agent: every chat message receives **"Hello world"**. To program your own agent, follow the [Cognitive Architecture Server guide](virtual_human_project/vh_cognitive_architecture_server/README.md).

Setup prepares the shared Python environment, both speech models and the avatar voices. Speech model release files are downloaded automatically; no separate manual download is needed. See the [installation and first-launch guide](virtual_human_project/vh_embodiment_server/README.md#installation) for requirements and details. For notebooks, select `virtual_human_project/.venv-vh-course` as the VS Code kernel.

## Course materials

Slides and notebooks follow the `Module_*/Chapter_*` structure. Open a chapter README for its slide and code links. Published materials are added to the same folders as they become available.

Use VS Code with the Python and Jupyter extensions. Hosted LLM examples need your own provider key; the mock agent and API Playground do not.
