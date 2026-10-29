# Course agents

Use notebooks to try the concepts while following the slides. Then apply the same code in an agent and test it with the avatar. Agent folders follow the same module and chapter numbers as the course notebooks.

During setup, first test the mock, then select the supplied naive agent and restart the cognitive server. You can try its LLM replies before studying or changing the code.

| Course chapter | Agent files | What to try |
| --- | --- | --- |
| Module 0 / Chapter 01 | [mock_agent.py](Module_0/Chapter_01/mock_agent.py) | Change the fixed reply; no model or key is needed |
| Module 0 / Chapter 01 | [naive_agent.py](Module_0/Chapter_01/naive_agent.py) | Apply the notebook's direct Ollama Cloud call to the avatar |
| Module 1 / Chapter 03 | [langchain_naive_agent.py](Module_1/Chapter_03/langchain_naive_agent.py) | Replace the direct SDK call with a LangChain call |
| Module 1 / Chapter 03 | [langchain_structured_agent.py](Module_1/Chapter_03/langchain_structured_agent.py) | Return speech and avatar behaviour with structured output |
| Module 1 / Chapter 03 | [langchain_basic_memory_agent.py](Module_1/Chapter_03/langchain_basic_memory_agent.py) | Exercise: write your memory agent in this comment-only file before selecting its import |
| Module 1 / Chapter 03 | [langchain_structured_memory_agent.py](Module_1/Chapter_03/langchain_structured_memory_agent.py) | Final exercise: combine conversation memory with structured control of speech, emotion, expression and gesture |

For example, the notebook folder `virtual_human_course/Module_1/Chapter_03/Code/` corresponds to `agents/Module_1/Chapter_03/` here. Chapters introducing concepts do not need a separate agent. Add agents to the corresponding folders as the practical chapters develop.

Select an agent with one import in `vh_cognitive_server.py`, for example:

```python
from agents.Module_1.Chapter_03.langchain_naive_agent import response
```

Keep exactly one response import active. After saving, stop and start the cognitive server in the avatar's Settings.

Every agent keeps the same `response(text: str) -> AgentReply` interface. The server routes and `schemas.py` remain shared. Provider keys stay in `vh_cognitive_architecture_server/llm_provider_api_key.yaml`, outside the module/chapter folders; notebook keys stay in `virtual_human_course/llm_provider_api_key.yaml`.

See the [Agent guide](../README.md) for configuration and switching agents.
