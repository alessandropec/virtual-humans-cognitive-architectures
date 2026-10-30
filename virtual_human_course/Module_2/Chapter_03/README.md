# Integration with the Virtual Human

Connect the conversational agent with memory to the browser avatar using the [Virtual Human Project](../../../virtual_human_project/README.md).

- [Slides](Slides/Module_2_Chapter_03_Integration_with_the_Virtual_Human.pdf)
- [Student PowerPoint](Slides/Module_2_Chapter_03_Integration_with_the_Virtual_Human.pptx)
- [Agent: langgraph_avatar_agent.py](../../../virtual_human_project/vh_cognitive_architecture_server/agents/Module_2/Chapter_03/langgraph_avatar_agent.py)

## What the agent does

The agent is a LangGraph graph with one `respond` node and an `InMemorySaver` checkpointer. It combines the structured `ModelReply` from Module 1 Chapter 03 with the conversation memory from Chapter 02.

- The browser and the HTTP server are unchanged: the browser still sends only text.
- The conversation thread is configured in the backend: `THREAD_ID` in the agent file. Every request continues that thread.
- **Clear conversation** in the browser deletes the thread, so the next message starts a new conversation.
- If the model fails or returns no structured reply, the avatar answers with a short fallback instead of an error.
- Only the most recent `MAX_MESSAGES` are sent to the model; the full history stays in the checkpoint.

## Prompt templates

The agent uses `SystemMessagePromptTemplate` for instructions with variables, `MessagesPlaceholder` for the recent conversation and `ChatPromptTemplate` to assemble them. `partial()` binds the schema instructions once; `format_messages()` supplies the current time and recent messages for each call. These templates assemble model input. `InMemorySaver` and the thread preserve conversation history.

## Try it

1. In `vh_cognitive_architecture_server/vh_cognitive_server.py`, keep only this response import active:

   ```python
   from agents.Module_2.Chapter_03.langgraph_avatar_agent import response
   ```

2. Save, then stop and start the cognitive server in the avatar's Settings.
3. Tell the avatar your name and favourite colour, then ask for both.
4. Press **Clear conversation** and ask again: the avatar no longer knows them.

Use the shared `virtual_human_project/.venv-vh-course` environment. The checkpointer keeps conversations in memory: restarting the cognitive server also clears them.

## Your turn

- Give the avatar a persona by changing the system instruction.
- Set `MAX_MESSAGES = 4` and find when the avatar forgets your name.
- Optional: guide the gestures, for example raise a hand when greeting.

References: [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence), [ChatOllama structured output](https://reference.langchain.com/python/langchain-ollama/chat_models/ChatOllama/with_structured_output).

## Final lab: coding agents and weather tools

The final slides introduce tool calls, the assistant/tools loop, the whiteboard API and coding agents. Compare Claude Code and Codex, then follow the official desktop installation link and open the local project in Codex.

Use the [weather exercise brief](Code/weather_exercise.md) to transform the avatar into a current-weather presenter. The avatar calls OpenWeather, speaks about the observation and displays its condition icon on the whiteboard. First try upload and Apply in the existing API Playground. A temperature-and-wind image card is an optional extension.

The base avatar agent remains the memory example. Implement the weather extension as the final exercise.

Before the final lab, complete [Clear conversation together](Code/clear_memory_together.md): delete one saved thread, expose the agent hook, connect the server route and test the browser button. The final weather exercise combines memory, avatar animation and live weather.

Before the weather lab, follow the [OpenWeather key mini tutorial](Code/openweather_setup.md): account, email verification, API keys, activation and local configuration.
