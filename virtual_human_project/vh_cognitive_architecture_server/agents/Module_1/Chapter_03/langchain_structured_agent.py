"""LangChain agent: text in, structured avatar reply out."""
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from schemas import AgentReply, ModelReply
from pathlib import Path
import json
import yaml

MODEL = 'gpt-oss:120b'
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


# Ollama Cloud supports tool calling, but not native JSON-schema output.
structured_client = client.with_structured_output(ModelReply, method='function_calling')
FORMAT_INSTRUCTIONS = 'Return ModelReply using this schema:\n' + json.dumps(ModelReply.model_json_schema())


def response(text: str) -> AgentReply:
    answer = structured_client.invoke([
        SystemMessage('You are a conversational virtual human. Reply briefly in the user\'s language. '
         'Always call ModelReply. Write only spoken words in speech_text. '
         'Choose catalog values from the output schema. '
         'Use null for unused emotion, expression and gesture. '
         'Choose one gesture at a time.\n' + FORMAT_INSTRUCTIONS),
        HumanMessage(text),
    ])
    return AgentReply(**answer.model_dump(), whiteboard=None)
