"""Naive agent using LangChain: one model call, without conversation memory."""
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
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


prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template('{style} The current time is {current_time}.'),
    HumanMessagePromptTemplate.from_template('{text}'),
])


def response(text: str) -> AgentReply:
    messages = prompt.format_messages(
        style=STYLE_PROMPT, current_time=datetime.now().strftime('%H:%M'), text=text,
    )
    reply = client.invoke(messages)
    answer = reply.content.strip()
    return AgentReply(speech_text=answer, whiteboard=None)


