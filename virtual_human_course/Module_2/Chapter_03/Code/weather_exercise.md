# Coding-agent lab: first a weather avatar, then your improvement

## Warm-up: a small Codex demo

Before opening the course repository, create an empty folder called `codex-demo` and open it in Codex. Use the installation link on the slides.

First prompt:

> Create a simple, lightweight game in the style of {game style}. Put HTML, CSS and JavaScript in one index.html file that opens directly in a browser. Add clear controls, a score and a restart button. Tell me how to open it.

Choose a style such as Snake, Pong, a platformer or an endless runner. Open the result in a browser, play and decide freely what you want to do with it. Then open the course project for the main exercise.

## Exercise 1: a weather avatar without the whiteboard

Start from `virtual_human_project/vh_cognitive_architecture_server/agents/Module_2/Chapter_03/langgraph_avatar_agent.py`. Keep the original example and create a new agent beside it.

The first version combines current weather, conversation memory and avatar behaviour. Leave the whiteboard unused. Obtain an OpenWeather key using the tutorial in the slides. Save it in a YAML file wherever you prefer and give the file path to Codex. The prompt needs the path, not the key itself.

### Complete Codex prompt

> Read `virtual_human_project/vh_cognitive_architecture_server/agents/Module_2/Chapter_03/langgraph_avatar_agent.py` and its schemas. Create `weather_avatar_agent.py` in the same folder, keeping the original unchanged. Turn the virtual human into a current-weather presenter using OpenWeather Geocoding and Current Weather. Read the API key from a YAML file at the path I provide; ask me for that path if it is missing, and do not display the key. Preserve conversation memory, `response(text)`, `clear_conversation()` and structured speech, emotion, expression and gesture. Put only words to be spoken in `speech_text`: no emoji, emoticons or written stage directions. Use the dedicated behaviour fields for animations. Use `ChatPromptTemplate`, message templates and `MessagesPlaceholder`. Keep the code simple and linear. Ask for unclear locations and explain API failures without inventing observations. Return `whiteboard=None`; do not add image downloads or whiteboard integration in this first version. First explain a short plan, then implement and run offline checks. Show the diff, the import needed to select the new agent and how to test it using the existing course Python environment.

### Try the working agent

1. Select its import in `vh_cognitive_server.py` and restart the cognitive server.
2. Tell the avatar your name and ask it to recall it.
3. Ask for current weather in Rome, Italy, then follow with "What about Milan?".
4. Ask for a happy greeting and a raised hand. Check speech and animation.
5. Press Clear conversation, then ask for your name again. See the [guided clearing exercise](clear_memory_together.md).
6. Check a missing location and an unavailable API using simulated responses. The agent must not invent weather.
7. Confirm that the agent does not update the whiteboard. Keep this working version before continuing.

## Exercise 2: write your own whiteboard prompt

Modify your working weather agent with Codex so that it displays an image representing the weather requested on the whiteboard. Explore the image controls in the API Playground first. For this task, write the prompt yourself.

Remember to tell the coding agent:

- Which course project folder you are working in.
- Which `weather_avatar_agent.py` you created and what it already does.
- Where to inspect the existing whiteboard API: `virtual_human_project/vh_embodiment_server/README.md` and, if useful, `app/assets/api-playground.js` inside the same server.
- Which YAML file contains the key.
- What must keep working: memory, animations, spoken text without emoticons and Clear conversation.
- What should appear on the board for the current weather request.

Check that the image represents the same place and conditions as the spoken answer. Try a second place and confirm that the display changes correctly. Review the code changes with the coding agent.

Hand in the working agent, the improvement you chose, a screenshot and a short explanation of what you checked. Explain which parts Codex changed and how memory, the tool and the avatar response fit together.

References: [OpenWeather Current Weather](https://openweathermap.org/api/current), [Geocoding](https://openweathermap.org/api/geocoding-api), [project API contract](../../../../virtual_human_project/vh_embodiment_server/README.md#api-reference).
