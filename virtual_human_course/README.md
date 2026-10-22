# Virtual Human Course

Course slides and notebooks are organised by module and chapter.

| Module | Topics |
| --- | --- |
| Module 0 | Introduction and setup |
| Module 1 | Cognitive architectures, LLMs and LangChain |
| Module 2 | Agent workflows, memory and avatar integration |
| Webinar | The Virtual Meteorologist |

## Choose your setup

- **Avatar project and notebooks:** follow the [Installation guide](../virtual_human_project/vh_embodiment_server/README.md). The installer prepares `virtual_human_project/.venv-vh-course`; select it as the notebook kernel. No second environment is needed.
- **Notebooks only:** create your own Python 3.12 environment, install this folder's `requirements.txt` into it, and select that environment as the notebook kernel.

The two requirements files are independent. The project file also lists the course packages, so its environment can run the notebooks. This folder's file is for a notebooks-only setup.

For notebook provider keys, duplicate `llm_provider_api_key.example.yaml` here and name the copy `llm_provider_api_key.yaml`. Keep your key file private. Agent examples have their own key file in the cognitive server folder.
