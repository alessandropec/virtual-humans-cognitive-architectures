# AI-Powered Virtual Humans

**LLM-Powered Cognitive Architectures**

<img src="assets/course-teaser.png" alt="A virtual human holding a brain, connecting human cognition and artificial intelligence" width="960">

Build the Python agent behind a virtual human: from a first LLM call to conversation memory, structured behaviour and tools. The course connects psychological models of memory with the cognitive architectures used to give a virtual character continuity across interactions.

The course project connects a talking browser avatar to a Python cognitive architecture through a JSON API.

For the foundations of virtual humans and how to build an embodiment in Unity, see [Part 1: Embodiment in Unity](https://github.com/stevieTheTurtle/AI_powered_VH_2026-Part_1). It is recommended, but not required for this course.

![VH Embodiment Server: browser avatar connected to the mock agent](virtual_human_project/docs/images/browser-ready.png)

## Repository folders

| Folder | Contents |
| --- | --- |
| [virtual_human_course](virtual_human_course/README.md) | Modules, slides, notebooks and course Python requirements |
| [virtual_human_project](virtual_human_project/README.md) | Avatar application, cognitive server and installers |

## Programme

| Module | Topics |
|---|---|
| **0 · Introduction and Setup** | Course project, model providers, Python environment and first LLM calls |
| **1 · Cognitive Architectures and Large Language Models** | Psychological foundations · LLMs, working memory and prompting · Introduction to LangChain |
| **2 · From Large Language Models to Virtual Humans** | LangGraph workflows · Stateful agents and conversation memory · Integration with the virtual human |
| **Webinar · The Virtual Meteorologist** | Extend the virtual human with tools and live weather data |

## Quick start

1. Choose **Code > Download ZIP** and extract the repository, or clone it. Keep both folders together.
2. Follow the [Installation guide](virtual_human_project/vh_embodiment_server/README.md). Run the installer for your computer; it prepares the application, Python and speech models.
3. Open the avatar and send a message. The default agent replies **"Hello world"**. No LLM account or API key is needed for this test.
4. Install [VS Code](https://code.visualstudio.com/download), our course IDE, and its Microsoft [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python) and [Jupyter](https://marketplace.visualstudio.com/items?itemName=ms-toolsai.jupyter) extensions. VS Code is installed separately from the project.
5. In VS Code, open the extracted repository folder and the [first notebook](virtual_human_course/Module_0/Chapter_01/Code/00_first_call.ipynb). Under **Select Kernel**, choose `virtual_human_project/.venv-vh-course`, the environment created by setup.
6. Follow [Module 0: Introduction and Setup](virtual_human_course/Module_0/Chapter_01/README.md) for the setup slides, provider keys and first LLM call.

To program the avatar's agent, follow the [Agent guide](virtual_human_project/vh_cognitive_architecture_server/README.md).

## Course materials

Slides and notebooks follow the `virtual_human_course/Module_*/Chapter_*` structure. Open a chapter README for its slide and code links.

For notebooks, use VS Code with the Python and Jupyter extensions and select the `virtual_human_project/.venv-vh-course` environment created by setup.
