"""LangChain agent: text in, structured avatar reply out."""
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
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


prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(
        "You are a conversational virtual human. Reply briefly in the user's language. "
        "Always call ModelReply. Put only spoken words in speech_text, no emoji or written actions. "
        "Choose catalog values from the output schema. "
        "Use null for unused emotion, expression and gesture. "
        "Choose one gesture at a time.\n{format_instructions}"
    ),
    HumanMessagePromptTemplate.from_template('{text}'),
]).partial(format_instructions=FORMAT_INSTRUCTIONS)


def response(text: str) -> AgentReply:
    answer = structured_client.invoke(prompt.format_messages(text=text))
    if answer is None:
        answer = ModelReply(speech_text='Could you say that again?', gesture='shrug')
    return AgentReply(**answer.model_dump(), whiteboard=None)
