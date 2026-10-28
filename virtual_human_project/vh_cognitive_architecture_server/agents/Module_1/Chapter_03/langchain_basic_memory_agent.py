# Exercise: build an agent with conversation memory.
# Use langchain_naive_agent.py in this folder as your starting point.
#
# Write the code yourself:
# - Keep the model setup, system instruction and current time.
# - Retain human and AI messages between requests, in order.
# - Send the conversation history to the model and save each new reply.
# - Expose response(text: str) -> AgentReply, as in the naive agent.
#
# When your implementation is ready, select it in vh_cognitive_server.py:
# from agents.Module_1.Chapter_03.langchain_basic_memory_agent import response
# Keep only one response import active, save and restart the cognitive server.
#
# Test: tell the avatar your name and favourite colour, then ask for both.
# An in-memory history is cleared when the server restarts.
