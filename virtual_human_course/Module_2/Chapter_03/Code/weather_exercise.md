# Final lab: memory, animation and weather

Extend `virtual_human_project/vh_cognitive_architecture_server/agents/Module_2/Chapter_03/langgraph_avatar_agent.py`. Connect the three pieces learned in the course: conversation memory, structured avatar behaviour and an OpenWeather tool. Start from the working memory avatar and add weather without losing its animations or Clear conversation. Use Codex to help inspect, edit and test the program. Explain each change before accepting it.

## Preparation

1. Follow the [official Codex desktop quickstart](https://learn.chatgpt.com/docs/quickstart), install the app for your operating system and sign in with ChatGPT. Open your local course project folder. Check [plan availability and usage](https://learn.chatgpt.com/docs/pricing) before the lab. API-key usage has separate billing. If access is unavailable, work in pairs or implement the brief manually.
2. [Claude Code](https://code.claude.com/docs/en/overview) is another coding agent. Both can inspect files, edit code and run commands with project access. For this lab we use Codex.
3. Follow the [mini tutorial: get and configure an OpenWeather key](openweather_setup.md). Create the account before class: activation can take up to two hours. Read the key from `openweather.api_key` in the existing local provider YAML, or from `OPENWEATHER_API_KEY` in the server environment.
4. Use the shared course Python environment. Inspect the agent, `schemas.py`, and the whiteboard API in the embodiment server README.

## Build it in this order

1. Test the existing memory avatar: name recall, a happy greeting with a raised hand, then Clear conversation.
2. Keep `ModelReply` for speech, emotion, expression and gesture. Keep `InMemorySaver` and the agent clearing hook.
3. Add the weather tool and the tool loop below. For this exercise, keep the complete message history rather than trimming tool exchanges.
4. Add the condition image on the whiteboard and test the complete avatar.

First complete [the guided Clear conversation exercise](clear_memory_together.md) together.

## The graph to build

```text
START -> assistant -- tool_calls --> tools
             ^                        |
             +------ ToolMessage -----+
             |
             +-- no tool_calls --> finalize --> END
```

- `assistant` invokes `client.bind_tools([get_weather])` and returns the complete AIMessage, including `tool_calls`.
- `ToolNode` executes requested calls and appends matching ToolMessages. `tools_condition` routes to tools when calls are present; map its `__end__` result to `finalize`.
- `finalize` uses the structured client to create `ModelReply` from the conversation and actual tool results. Keep structured formatting separate from weather-tool selection. Explain how internal tool messages and the final spoken response enter state.
- Keep `ChatPromptTemplate`, a system message template and `MessagesPlaceholder` for model input. The checkpointer preserves state; templates only assemble prompts.
- Preserve complete AI tool-call/ToolMessage pairs when selecting context. A simple slice can leave an orphan tool result. Set a finite tool-loop budget and handle exhaustion.
- Keep `response(text) -> AgentReply`, the checkpointer, configured thread and `clear_conversation()`. Non-weather messages should still work.

## The tool

Implement `get_weather(city: str, country: str)` with a clear docstring and typed inputs. It should:

1. Resolve a city and country code with the [Geocoding API](https://openweathermap.org/api/geocoding-api). Ask for clarification when the place is missing or ambiguous.
2. Call [Current Weather](https://openweathermap.org/api/current) using latitude, longitude, `appid` and `units=metric`.
3. Return a small result containing resolved location, temperature in Celsius, description, wind in m/s, observation timestamp and condition icon code. Do not return credentials or the entire HTTP request.
4. Handle missing credentials, no matching city, HTTP 401/429 and timeouts. Never invent observations. This endpoint reports current weather, not tomorrow's forecast.

## The whiteboard

Begin with the API Playground: upload an image and apply a reply. Then automate the same upload from Python:

1. Read the successful observation's icon code and download `https://openweathermap.org/img/wn/{icon}@2x.png`. See [condition icons](https://openweathermap.org/api/weather-conditions).
2. POST its bytes as multipart field `file` to the running embodiment server's `/api/whiteboard/images`. Configure that server's base URL for your setup.
3. Use the returned local URL in `AgentReply.whiteboard`:

```python
whiteboard = {"type": "image", "image_url": uploaded_image_url}
```

External icon URLs are not accepted directly. Valid URLs refer to an actual uploaded image, like `/media/board-<32 hexadecimal characters>.png`. Uploading alone does not display it. Return the command with `AgentReply`; the embodiment server applies it. Do not also call `/api/speak` from the cognitive agent.

`None` preserves the board; `{"type": "clear"}` clears it. If image upload fails, still provide a valid spoken weather response. Avoid displaying a previous turn's weather on an unrelated turn. An optional extension is a PNG card containing the city, temperature, observation time and icon. The board displays images, not raw HTML.

## Suggested Codex prompt

> Read the selected LangGraph avatar agent, its schemas and the whiteboard API contract. Explain how prompt templates, conversation memory and structured ModelReply work. Propose a short plan to implement this weather exercise, then make changes in small steps. Add an OpenWeather tool and assistant/tools/finalize graph. Preserve response(text), clear_conversation and the existing frontend contract. Read OPENWEATHER_API_KEY from the process environment, falling back to openweather.api_key in the existing local provider YAML, without printing its value. Download the condition icon and upload it to the embodiment server before returning its local URL in AgentReply.whiteboard. Handle missing/ambiguous locations and HTTP errors. Use mocked HTTP and model clients for checks. Show the diff and explain how to run it with the existing course environment.

## Acceptance checks and hand-in

- Introduce yourself, request a happy greeting with a raised hand, then ask for your name: check both memory and avatar behaviour.
- Ask for current weather in Rome, IT. Speech and board must match the same observation, with explicit units and time.
- Ask "What about Milan?" and check that the agent uses conversation context.
- Send a greeting: the agent must respond without an unnecessary weather call.
- Test missing city, ambiguous city, missing key, invalid key, rate limit and timeout using mocked responses. No invented weather or leaked secrets.
- Simulate image upload failure: speech still works. Clear conversation and confirm previous personal details are gone.
- Print the compiled graph using `graph.get_graph().print_ascii()` and explain each node and conditional route.
- Submit the edited agent, any new helper files, a sample tool result without credentials, a screenshot and a short explanation of your checks. Review the diff yourself.

References: [LangGraph tool workflows](https://docs.langchain.com/oss/python/langgraph/workflows-agents), [project whiteboard contract](../../../../virtual_human_project/vh_embodiment_server/README.md#api-reference).
