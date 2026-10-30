# Virtual Human Course

Course slides and notebooks are organised by module and chapter.

**Module 0: Introduction and Setup** covers the project, installation, VS Code, provider keys and first LLM calls.

- [Slides (PDF)](Module_0/Chapter_01/Slides/Module_0_Chapter_01_Introduction_and_Setup.pdf)
- [PowerPoint](Module_0/Chapter_01/Slides/Module_0_Chapter_01_Introduction_and_Setup.pptx)
- [First-call notebook](Module_0/Chapter_01/Code/00_first_call.ipynb)

After the notebook, use the [Agent guide](../virtual_human_project/vh_cognitive_architecture_server/README.md) to switch from the fixed mock reply to the supplied naive agent. Restart the cognitive server in Settings and try a conversation with the avatar.

**Module 1: Cognitive architectures, LLMs and LangChain** connects memory models to prompts and executable agents. Follow the chapters in order:

1. [Psychological Foundations of Cognitive Architectures](Module_1/Chapter_01/Slides/Module_1_Chapter_01_Psychological_Foundations.pdf)
2. [LLMs, Working Memory and Prompting](Module_1/Chapter_02/Slides/Module_1_Chapter_02_LLMs_Working_Memory_and_Prompting.pdf)
3. [Introduction to LangChain](Module_1/Chapter_03/Slides/Module_1_Chapter_03_Introduction_to_LangChain.pdf)

In Chapter 03, follow each slide block, then open the indicated section of [01: Calls, chains and chat prompts](Module_1/Chapter_03/Code/01_langchain.ipynb) or [02: Structured output and conversation memory](Module_1/Chapter_03/Code/02_structured_output.ipynb). The notebooks link to the corresponding avatar agents.

**Module 2: From LLMs to virtual humans** turns agents into LangGraph graphs with conversation memory:

1. [Agentic Frameworks and LangGraph](Module_2/Chapter_01/README.md): state, nodes and edges in [01: LangGraph basics](Module_2/Chapter_01/Code/01_langgraph.ipynb)
2. [Memory and the Virtual Human](Module_2/Chapter_02/README.md): build memory in the [notebook](Module_2/Chapter_02/Code/01_memory.ipynb), then select the [avatar agent](../virtual_human_project/vh_cognitive_architecture_server/agents/Module_2/Chapter_02/langgraph_avatar_agent.py) and test speech, gestures and Clear conversation
3. [Tools and Coding Agents](Module_2/Chapter_03/README.md): extend the working avatar with current weather and the whiteboard using Codex
