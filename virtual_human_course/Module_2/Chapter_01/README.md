# Agentic Frameworks and LangGraph

Build a graph from ordinary Python functions, then control how its nodes run.

- [Slides](Slides/Module_2_Chapter_01_Agentic_Frameworks_and_LangGraph_Introduction.pdf)
- [Student PowerPoint](Slides/Module_2_Chapter_01_Agentic_Frameworks_and_LangGraph_Introduction.pptx)
- [Notebook: LangGraph basics](Code/01_langgraph.ipynb)

## Sequence

1. Why agentic frameworks, four frameworks compared, LangChain components and LangGraph building blocks, and the connection to the [memory exercise](../../Module_1/Chapter_03/Code/02_structured_output.ipynb) from Module 1.
2. State, nodes, directed edges, and a sequential graph. Open notebook section 1 after slide 14.
3. Conditional paths. Open section 2 after slide 16 and add another language.
4. Parallel paths and joining their results. Open section 3 after slide 18.
5. Together: put the Module 1 model call with its list of messages inside a graph. Open section 4 after slide 19.
6. Exercise: a dialogue manager that detects the intent, chooses an emotion and replies with it. Open section 5 after slide 20.

Select the course Python environment and run the notebook cells in order. Sections 1–3 run without a model. Sections 4 and 5 call the model with the course key `virtual_human_course/llm_provider_api_key.yaml`. There is no new server agent for this chapter.

## Next chapter

State in these examples lasts for one invocation. [Chapter 02](../Chapter_02/README.md) will add messages, reducers and checkpoints to continue conversations across calls.

The examples follow the [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api) and the construction steps in the [official quickstart](https://docs.langchain.com/oss/python/langgraph/quickstart). Tool calling comes later.
