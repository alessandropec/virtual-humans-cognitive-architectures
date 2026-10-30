# Tools and Coding Agents

Extend the working [Chapter 02 avatar](../../../virtual_human_project/vh_cognitive_architecture_server/agents/Module_2/Chapter_02/langgraph_avatar_agent.py) with current weather and a whiteboard image.

- [Slides](Slides/Module_2_Chapter_03_Tools_and_Coding_Agents.pdf)
- [Student PowerPoint](Slides/Module_2_Chapter_03_Tools_and_Coding_Agents.pptx)

The avatar already has conversation memory, structured speech and animations, and Clear conversation. This chapter works directly in the project; it has no separate notebook.

## Sequence

1. Slide 2 recalls the working Chapter 02 base.
2. Slides 3–7 explain tools and their execution loop at a high level, then show an OpenWeather request, JSON and API-key setup. Tool implementation code is added by Codex during the exercise.
3. Slides 8–10 compare Claude Code and Codex, install the official Codex VS Code extension and create a small browser game in a separate folder.
4. Slides 11–13 discuss AI, cognitive effort and choosing what to practise.
5. Slides 14–16 supply the meteorologist prompt and tests. Read the Chapter 02 base and create `agents/Module_2/Chapter_03/weather_avatar_agent.py`, preserving memory and animations and leaving the board unused.
6. Slides 17–19 introduce the Playground and whiteboard goal. Students write their own Codex prompt, providing the agent path, API documentation and the YAML key-file path.
7. The closing slides contain references, webinar and mentorship registration, and the Part 2 feedback questionnaire.

Save the OpenWeather key in a YAML file wherever you prefer and tell Codex its path. Select the generated weather agent in `vh_cognitive_server.py`, keep one response import active and restart the cognitive server. The supplied prompt asks Codex to explain that selection and test it.

The public project provides the Chapter 02 memory agent. Students create the Chapter 03 weather agent during the lab; completed instructor solutions are private.

Webinar: 3 November 2026, 17:00–18:00. Mentorship: 11 November 2026, from 14:30. Registration and feedback links are in the slides.
