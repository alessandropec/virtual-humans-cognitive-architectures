# Introduction to LangChain

Follow each slide block, then open the notebook section linked on its last slide.

- [Slides](Slides/Module_1_Chapter_03_Introduction_to_LangChain.pdf)
- [Student PowerPoint](Slides/Module_1_Chapter_03_Introduction_to_LangChain.pptx)
- [01: Calls, chains and chat prompts](Code/01_langchain.ipynb)
- [02: Structured output](Code/02_structured_output.ipynb)

Open notebooks from their `Code` folder and use the course Python kernel. Each has its own setup cell and reads `virtual_human_course/llm_provider_api_key.yaml` through a direct relative path.

## Exercises

1. Generate an answer, then review it with a second model. Replace football content with a fixed refusal and keep other text unchanged. Repeat the same chain with checking rules in system and dynamic text in human.
2. Use message templates and a dictionary to fill static/dynamic chat prompts. Choose a speaking style and supply the current time through a chat template. Copy the style into `STYLE_PROMPT` in the naive agent and try it in the server.
3. Tune the classifier prompt and field description. The [dataset](Code/visitor_intents.json) contains 15 labelled requests. If a request has multiple questions, classify its first question. Send all requests in one call, inspect errors and accuracy, then tune the prompt and description and rerun.

4. Keep previous human and AI messages in a list, pass the full history to each call and save the next reply. Then complete the comment-only `langchain_basic_memory_agent.py` using the naive agent as a starting point, implement the memory yourself and repeat the two turns with the avatar.

Format instructions are introduced immediately after the first structured reply and included in the email, classifier and avatar prompts. Model calls, schema definitions, prompt inspection and scoring are all in notebook cells. Keep the single JSON dataset beside the notebooks. It is a small synthetic exercise, not a benchmark.

## Try on the agent

Notebook links open the existing [naive agent](../../../virtual_human_project/vh_cognitive_architecture_server/agents/Module_1/Chapter_03/langchain_naive_agent.py) and [structured agent](../../../virtual_human_project/vh_cognitive_architecture_server/agents/Module_1/Chapter_03/langchain_structured_agent.py).
Select the matching import, save and restart the cognitive server. See the [Agent guide](../../../virtual_human_project/vh_cognitive_architecture_server/README.md).
The server uses its own provider-key file. The supplied agents start without conversation memory. The final exercise asks you to create your own memory agent; a comment-only file is supplied.

The framework comparison opens [Module 2 / Chapter 01](../../Module_2/Chapter_01/README.md), where we will revisit conversation memory using graph state and checkpoints.
