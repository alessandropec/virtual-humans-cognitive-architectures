# Exercise: an avatar with conversation memory and embodiment control.
# Combine two agents of this chapter:
# - langchain_structured_agent.py: a structured ModelReply controls speech, emotion, expression and gesture.
# - langchain_basic_memory_agent.py, your memory exercise: human and AI messages are kept between requests.
#
# Write the code yourself, starting from langchain_structured_agent.py:
# - Keep the model setup, structured_client, FORMAT_INSTRUCTIONS and the system instruction.
# - Keep a list of messages between requests, in order.
# - Replace the human template with MessagesPlaceholder("messages").
# - Fill the chat template with the history and send it to structured_client.
# - Append the user's HumanMessage before the call and AIMessage(answer.speech_text) after it:
#   the history needs the spoken words, not the whole structured reply.
# - If the model returns None, use a short fallback ModelReply instead of failing.
# - Expose response(text: str) -> AgentReply, returning speech, emotion, expression and gesture.
#
# When your implementation is ready, select it in vh_cognitive_server.py:
# from agents.Module_1.Chapter_03.langchain_structured_memory_agent import response
# Keep only one response import active, save and restart the cognitive server.
#
# Test: tell the avatar your name and ask it to greet you happily with a raised hand.
# Then ask for your name: the avatar should remember it and move accordingly.
# An in-memory history is cleared when the server restarts.
