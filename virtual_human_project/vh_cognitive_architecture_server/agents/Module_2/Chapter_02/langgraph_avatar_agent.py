"""LangGraph agent for the avatar: structured replies and conversation memory."""
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, SystemMessagePromptTemplate
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.memory import InMemorySaver
from schemas import AgentReply, ModelReply
from datetime import datetime
from pathlib import Path
import json
import yaml

MODEL = 'gpt-oss:120b'
KEY_FILE = Path(__file__).resolve().parents[3] / 'llm_provider_api_key.yaml'
API_KEY = yaml.safe_load(KEY_FILE.read_text(encoding='utf-8'))['ollama']['api_key']

# Backend configuration: the browser sends only text, so every request
# continues this conversation thread. Clear conversation deletes it.
THREAD_ID = 'avatar'
# Rolling buffer: only the most recent messages are sent to the model.
MAX_MESSAGES = 20
FALLBACK = ModelReply(speech_text='Sorry, I did not catch that. Could you say it again?', gesture='shrug')


client = ChatOllama(
    model=MODEL,
    base_url='https://ollama.com',
    client_kwargs={
        'headers': {'Authorization': f'Bearer {API_KEY}'},
        'timeout': 45,
    },
)
structured_client = client.with_structured_output(ModelReply, method='function_calling')
FORMAT_INSTRUCTIONS = 'Return ModelReply using this schema:\n' + json.dumps(ModelReply.model_json_schema())
prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(
        'You are a conversational virtual human. Reply briefly in the user\'s language. '
        'Always call ModelReply. Write only spoken words in speech_text, without emoji, emoticons or written actions. '
        'Choose catalog values from the output schema. '
        'Use null for unused emotion, expression and gesture. '
        'Choose one gesture at a time. The current time is {current_time}.\n'
        '{format_instructions}'
    ),
    MessagesPlaceholder('messages'),
]).partial(format_instructions=FORMAT_INSTRUCTIONS)


class AvatarState(MessagesState):
    reply: dict


def respond(state: AvatarState):
    current_time = datetime.now().strftime('%H:%M')
    try:
        messages = prompt.format_messages(
            current_time=current_time,
            messages=state['messages'][-MAX_MESSAGES:],
        )
        answer = structured_client.invoke(messages) or FALLBACK
    except Exception as error:
        # A failed model call must not break the avatar or the saved conversation.
        print('MODEL ERROR:', type(error).__name__, error, flush=True)
        answer = FALLBACK
    # Store only the spoken text in the history; return the full reply to the avatar.
    return {'messages': [AIMessage(answer.speech_text or '')], 'reply': answer.model_dump()}


builder = StateGraph(AvatarState)
builder.add_node('respond', respond)
builder.add_edge(START, 'respond')
builder.add_edge('respond', END)

checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)
config = {'configurable': {'thread_id': THREAD_ID}}


def response(text: str) -> AgentReply:
    result = graph.invoke({'messages': [HumanMessage(text)]}, config)
    return AgentReply(**result['reply'], whiteboard=None)


def clear_conversation():
    # Called by the server when the browser clears the conversation.
    checkpointer.delete_thread(THREAD_ID)
