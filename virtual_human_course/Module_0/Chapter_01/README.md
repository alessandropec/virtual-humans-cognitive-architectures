# Chapter 01: Course Introduction and Setup

This chapter introduces the provided virtual human, conversation memory, the course tools and the first LLM calls.

## Chapter contents

- `Slides/`: presentation slides in PowerPoint and PDF formats.
- `Code/`: notebook. The shared API-key template is in virtual_human_course.

## Slides

- [Student PowerPoint](Slides/Module_0_Chapter_01_Introduction_and_Setup.pptx)
- [Slide-only PDF](Slides/Module_0_Chapter_01_Introduction_and_Setup.pdf)

## Virtual human project

Use the [Project overview](../../../virtual_human_project/README.md): the browser-based VH Embodiment Server and the Python VH Cognitive Architecture Server. Follow the [Installation guide](../../../virtual_human_project/vh_embodiment_server/README.md#installation). Setup prepares speech models and the shared course environment automatically.

## Setup in VS Code

1. Clone or download the course repository and extract it.
2. Run the Windows or Mac installer inside `virtual_human_project/vh_embodiment_server/dist/`.
3. Open the repository root in [VS Code](https://code.visualstudio.com/download) with the Microsoft Python and Jupyter extensions.
4. Select `virtual_human_project/.venv-vh-course` as the interpreter and notebook kernel.
5. Open [00_first_call.ipynb](Code/00_first_call.ipynb). Use this same environment throughout the course.

For notebooks without the virtual human, create a Python 3.12 environment with the course [requirements.txt](../../requirements.txt).

## Private keys

Before running the provider examples:

1. Duplicate [llm_provider_api_key.example.yaml](../../llm_provider_api_key.example.yaml) in `virtual_human_course` and name the copy `llm_provider_api_key.yaml`. Keep the example unchanged.
2. Open the copy and replace the placeholders with your own API keys.
3. Run the first code cell in the notebook to load the keys.

For project LLM agents, repeat these steps in `virtual_human_project/vh_cognitive_architecture_server`, as explained in the [Agent guide](../../../virtual_human_project/vh_cognitive_architecture_server/README.md). The mock agent needs no key.

The YAML file is a convenience used in this course. Environment variables are another option; a `.env` file can also be used with an appropriate loader. The notebook follows the YAML approach.

## Provider accounts and API keys

- [Ollama Cloud API keys](https://ollama.com/settings/keys)
- [Google AI Studio](https://aistudio.google.com/)
- [Groq console](https://console.groq.com/)
- [OpenRouter API keys](https://openrouter.ai/settings/keys)

For optional local inference, [download and install Ollama](https://ollama.com/download). Local Ollama does not require an API key.

Reuse the same shared environment in all modules; do not create a separate environment per chapter.
