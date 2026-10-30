"""The HTTP server stays the same: select one agent import below."""
import sys
import json
import asyncio
import logging
from fastapi import FastAPI, Request, HTTPException
from schemas import AgentRequest, AgentReply

# Keep exactly one response import active.
from agents.Module_0.Chapter_01.mock_agent import response
# from agents.Module_0.Chapter_01.naive_agent import response
# from agents.Module_1.Chapter_03.langchain_naive_agent import response
# from agents.Module_1.Chapter_03.langchain_structured_agent import response
# from agents.Module_2.Chapter_03.langgraph_avatar_agent import response

app = FastAPI(title='VH Cognitive Architecture Server')
instance = None


class QuietHeartbeat(logging.Filter):
    def filter(self, record):
        return not (isinstance(record.args, tuple) and len(record.args) > 2 and str(record.args[2]).split('?')[0] == '/heartbeat')


logging.getLogger('uvicorn.access').addFilter(QuietHeartbeat())


@app.post('/shutdown')
async def shutdown(request: Request):
    if request.headers.get('x-virtual-human') != 'shutdown' or request.client.host not in ('127.0.0.1', '::1'):
        raise HTTPException(403, 'Local shutdown only.')
    if instance is None:
        raise HTTPException(409, 'Stop this server through its process manager.')
    asyncio.get_running_loop().call_later(0.1, setattr, instance, 'should_exit', True)
    return {'status': 'stopping'}


@app.post('/agent', response_model=AgentReply)
@app.post('/chat', response_model=AgentReply)
def agent(request: AgentRequest):
    print('RECEIVED:', request.text, flush=True)
    reply = response(request.text)
    print('SENT:', json.dumps(reply.model_dump(), ensure_ascii=True), flush=True)
    return reply


@app.post('/conversation/clear')
def clear_conversation():
    # Agents with conversation memory define clear_conversation() next to response().
    selected_agent = sys.modules[response.__module__]
    clear_agent_memory = getattr(selected_agent, 'clear_conversation', None)
    if callable(clear_agent_memory):
        clear_agent_memory()
    return {'status': 'ok'}


@app.get('/heartbeat')
@app.get('/')
def status():
    return {'status': 'ok', 'service': 'VH Cognitive Architecture Server'}


if __name__ == '__main__':
    import uvicorn
    import os
    import sys
    import threading
    port = int(os.environ.get('VH_AGENT_PORT', '8000'))
    print(f'VH Cognitive Architecture Server: http://127.0.0.1:{port}', flush=True)
    instance = uvicorn.Server(uvicorn.Config(app, host='127.0.0.1', port=port))
    if os.environ.get('VH_AGENT_MANAGED') == '1':
        # The parent holds stdin open. EOF means the embodiment has exited.
        def parent_closed():
            sys.stdin.buffer.read()
            instance.should_exit = True
        threading.Thread(target=parent_closed, daemon=True).start()
    instance.run()
