"""One Ollama Cloud call, using the same SDK and model as Module 0."""

from pathlib import Path
from schemas import AgentReply
import yaml

MODEL = 'gpt-oss:120b'
KEY_FILE = Path(__file__).resolve().parents[1] / 'llm_provider_api_key.yaml'
API_KEY = yaml.safe_load(KEY_FILE.read_text(encoding='utf-8'))['ollama']['api_key']

from ollama import Client

client = Client(
    host='https://ollama.com',
    headers={'Authorization': f'Bearer {API_KEY}'},
    timeout=45,
)


def response(text: str) -> AgentReply:
    response = client.chat(
        model=MODEL,
        messages=[{'role': 'user', 'content': text}],
    )
    answer = response.message.content.strip()
    return AgentReply(speech_text=answer, whiteboard=None)
