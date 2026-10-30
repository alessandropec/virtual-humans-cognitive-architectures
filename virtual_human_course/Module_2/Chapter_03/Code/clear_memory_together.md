# Together: connect Clear conversation to graph memory

We will implement this connection together before the final weather exercise. The released server includes the completed route, so you can compare your work with it.

## 1. Delete a notebook conversation

In Chapter 02 we compile with a named saver:

```python
saver = InMemorySaver()
memory_graph = builder.compile(checkpointer=saver)
```

After storing a conversation for thread `lea`, run:

```python
saver.delete_thread("lea")
print(memory_graph.get_state(lea).values)
```

The state is empty. The next call on that thread starts a new conversation. Other threads remain available.

## 2. Add the agent hook

Open `langgraph_avatar_agent.py`. The program already owns its saver and thread identifier. Expose a small function next to `response`:

```python
def clear_conversation():
    checkpointer.delete_thread(THREAD_ID)
```

This is the same operation as the notebook. Keep it in the agent so the HTTP server does not need to know how the graph stores memory.

## 3. Complete the server route together

In `vh_cognitive_server.py`, the browser's Clear conversation button reaches `POST /conversation/clear`. We find the selected agent from its imported `response` function and call the hook when it exists:

```python
@app.post("/conversation/clear")
def clear_conversation():
    selected_agent = sys.modules[response.__module__]
    clear_agent_memory = getattr(selected_agent, "clear_conversation", None)
    if callable(clear_agent_memory):
        clear_agent_memory()
    return {"status": "ok"}
```

Start from the decorator and function signature when writing this live. Students supply the agent lookup and hook call. The existing mock agent has no memory hook and still works. An HTTP route named clear does not erase graph state until it actually calls the saver.

## 4. Test the complete path

1. Select the LangGraph agent and restart the cognitive server.
2. Tell the avatar your name, then ask for it. It should remember.
3. Press Clear conversation and ask again. It should no longer know your name.
4. Repeat with the weather agent in the final exercise. Preserve its memory, structured animation fields and clearing hook.

You can also POST an empty request to `/conversation/clear` on the cognitive server from its `/docs` page. The browser communicates through the embodiment server, which forwards the clear request. No frontend changes are needed.
