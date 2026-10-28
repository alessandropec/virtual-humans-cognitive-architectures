"""Naive agent using LangChain: one model call, without conversation memory."""
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from datetime import datetime
from pathlib import Path
from schemas import AgentReply
import yaml

MODEL = 'gpt-oss:120b'
STYLE_PROMPT = 'Reply briefly.'
KEY_FILE = Path(__file__).resolve().parents[3] / 'llm_provider_api_key.yaml'
API_KEY = yaml.safe_load(KEY_FILE.read_text(encoding='utf-8'))['ollama']['api_key']


client = ChatOllama(
    model=MODEL,
    base_url='https://ollama.com',
    client_kwargs={
        'headers': {'Authorization': f'Bearer {API_KEY}'},
        'timeout': 45,
    },
)


def response(text: str) -> AgentReply:
    current_time = datetime.now().strftime('%H:%M')
    reply = client.invoke([
        SystemMessage(STYLE_PROMPT + f' The current time is {current_time}.'),
        HumanMessage(text),
    ])
    answer = reply.content.strip()
    return AgentReply(speech_text=answer, whiteboard=None)


