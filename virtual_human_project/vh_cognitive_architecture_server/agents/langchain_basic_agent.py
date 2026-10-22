"""Basic LangChain agent: text in, AgentReply out."""
from langchain_ollama import ChatOllama
from pathlib import Path
from schemas import AgentReply
import yaml

MODEL = 'gpt-oss:120b'
KEY_FILE = Path(__file__).resolve().parents[1] / 'llm_provider_api_key.yaml'
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
    reply = client.invoke([('human', text)])
    answer = reply.content.strip()
    return AgentReply(speech_text=answer, whiteboard=None)


