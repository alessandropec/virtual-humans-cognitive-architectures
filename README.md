# AI-Powered Virtual Humans

**LLM-Powered Cognitive Architectures**

<img src="assets/course-teaser.png" alt="A virtual human holding a brain, connecting human cognition and artificial intelligence" width="960">

**Alessandro Emmanuel Pecora · October 2026**

Build the Python agent behind a virtual human: from a first LLM call to conversation memory, structured behaviour and tools. The course connects psychological models of memory with the cognitive architectures used to give a virtual character continuity across interactions.

[Programme](#programme) · [Available materials](#available-materials) · [Getting started](#getting-started)

## Programme

| Module | Topics |
|---|---|
| **0 · Introduction and Setup** | Course project, model providers, Python environment and first LLM calls |
| **1 · Cognitive Architectures and Large Language Models** | Psychological foundations · LLMs, working memory and prompting · Introduction to LangChain |
| **2 · From Large Language Models to Virtual Humans** | LangGraph workflows · Stateful agents and conversation memory · Integration with the virtual human |
| **Webinar · The Virtual Meteorologist** | Extend the virtual human with tools and live weather data |

The course uses the Unity project from the previous virtual humans course through a Python API. Previous attendance is not required; the focus here is the agent behind the character.

## Part 1: Virtual Humans Foundations

The Unity and Python starter project from [Stefano Calzolari's Part 1 course](https://github.com/stevieTheTurtle/AI_powered_VH_2026-Part_1) is available in [Part_1_Virtual_Humans/](Part_1_Virtual_Humans/). Follow that folder's guide for Unity **6000.3.26f1**, character import and the original Python **3.12** environment.

[Download the starter project and Camila together](https://github.com/alessandropec/virtual-humans-cognitive-architectures/releases/download/part1-2026-10-21/Part_1_Project_and_Camila.zip). Camila is hosted in this repository's GitHub Releases and is not included in **Code > Download ZIP**. Speech models and Meta OVRLipSync are separate downloads.

The current starter is a placeholder. After Part 1 ends, it will be replaced here by the completed project for the integration demonstration. Camila is already the definitive course character.

## Available materials

- [Part 1: Virtual Humans Foundations (Stefano Calzolari)](Part_1_Virtual_Humans/) · version 1.0.1

Each released chapter includes a README with instructions, slides in PowerPoint and PDF, and notebooks or code where applicable. You can also find chapter packages under [Releases](https://github.com/alessandropec/virtual-humans-cognitive-architectures/releases).

## Getting started

- Basic Python knowledge is helpful. Use **Python 3.13** and **VS Code** with the Python and Jupyter extensions.
- When Module 0 is available, follow its setup instructions. Use one Python environment at the repository root across all chapters.
- Hosted model examples use your own provider API key. Local inference with Ollama is optional.

The main tools are **LangChain**, **LangGraph**, **Pydantic** and **FastAPI**, with **Unity** providing the virtual character.

## Further reading

[A Survey of Memory Models for Virtual Agents and Humans: From Psychological Foundations to Computational Architectures](https://doi.org/10.1007/978-3-031-97778-7_8) — Pecora, Strada and Bottino, XR Salento 2025.
