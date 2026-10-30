# Memory and the Virtual Human

Build conversation memory in the notebook, then run the same pattern in the avatar.

- [Slides](Slides/Module_2_Chapter_02_Memory_and_the_Virtual_Human.pdf)
- [Student PowerPoint](Slides/Module_2_Chapter_02_Memory_and_the_Virtual_Human.pptx)
- [Notebook: conversation memory](Code/01_memory.ipynb)
- [Ready-to-run avatar agent](../../../virtual_human_project/vh_cognitive_architecture_server/agents/Module_2/Chapter_02/langgraph_avatar_agent.py)

## Sequence

1. Slides 2–4: messages in state and reducers. Run notebook section 1.
2. Slides 5–6: a chatbot without a checkpointer. Run section 2 and compare two separate calls.
3. Slides 7–11: checkpoints, separate threads and deleting one conversation. Run section 3.
4. Slides 12–13: rolling context and the two-visitors exercise. Complete section 4.
5. Slides 14–21: apply memory to the avatar, preserve structured speech and animation, then connect Clear conversation. Follow section 5 and open the supplied agent.
6. Slide 22: the working avatar is the starting point for Chapter 03.

Run notebook cells in order with the course Python kernel. The notebook reads `virtual_human_course/llm_provider_api_key.yaml`; the server reads its own provider file.

## Select and test the agent

Keep one response import active in `vh_cognitive_architecture_server/vh_cognitive_server.py`:

```python
from agents.Module_2.Chapter_02.langgraph_avatar_agent import response
```

Save and restart the cognitive server in the avatar Settings. Introduce yourself, ask for your name, request a happy greeting with a raised hand, then press **Clear conversation** and ask for your name again.

The supplied agent combines `MessagesState`, a rolling buffer, `InMemorySaver`, message/chat prompt templates and the structured `ModelReply` from Module 1. Its `clear_conversation()` hook and the server route are complete; reconstruct the route together while following the slides. `InMemorySaver` also loses its data when the server restarts.

Use `MAX_MESSAGES` to compare what the model sees with what remains saved. A previous reply may repeat a fact, so there is no fixed number of turns before it disappears from context.

## Next chapter

[Tools and Coding Agents](../Chapter_03/README.md) starts from this working avatar. Use Codex to add current weather, then extend the result with a whiteboard image.

References: [Persistence](https://docs.langchain.com/oss/python/langgraph/persistence), [Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api), [Memory](https://docs.langchain.com/oss/python/langgraph/add-memory).
