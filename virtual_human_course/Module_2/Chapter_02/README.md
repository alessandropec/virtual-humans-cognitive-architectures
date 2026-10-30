# Building Stateful Agents with Memory

Maintain a conversation across successive requests.

- [Slides](Slides/Module_2_Chapter_02_Building_Stateful_Agents_with_Memory.pdf)
- [Student PowerPoint](Slides/Module_2_Chapter_02_Building_Stateful_Agents_with_Memory.pptx)
- [Notebook: conversation memory](Code/01_memory.ipynb)

## Sequence

1. From the list of messages in the Module 1 [memory exercise](../../Module_1/Chapter_03/Code/02_structured_output.ipynb) to messages in graph state. Open notebook section 1 after slide 4.
2. A chatbot node without a checkpointer forgets between calls. Open section 2 after slide 6.
3. A checkpointer and `thread_id` continue a conversation; a different thread is a separate conversation. Open section 3 after slide 9.
4. Delete one thread after slide 11, using the end of section 3.
5. A rolling buffer limits what the model sees. Open section 4 after slide 13 and complete the two-visitors exercise.

Select the course Python kernel and run the cells in order. The notebook uses the same Ollama Cloud key as Module 1: `virtual_human_course/llm_provider_api_key.yaml`.

## Topics

- Messages and reducers
- Rolling conversation buffers
- Checkpointers and conversation threads

## Next chapter

[Chapter 03](../Chapter_03/README.md) runs the same graph inside the cognitive server, so the avatar remembers the conversation.

References: [Persistence](https://docs.langchain.com/oss/python/langgraph/persistence), [Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api), [Memory](https://docs.langchain.com/oss/python/langgraph/add-memory).
