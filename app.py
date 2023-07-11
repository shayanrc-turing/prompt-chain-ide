import streamlit as st
import openai
from litechain.contrib import OpenAIChatChain, OpenAIChatMessage, OpenAIChatDelta
import asyncio




openai.api_key = st.secrets['OPANAI_API_KEY']

st.title('Prompt IDE')

# @st.cache(ttl=360)
def get_available_models():
    resp = openai.Model.list()
    models = []
    if 'data' in resp:
        for model in resp['data']:
            if 'gpt' in model['id']:
                models.append(model['id'])



    return models

available_models = get_available_models()
available_models = sorted(available_models)

if 'default_first_message' not in st.session_state:
    st.session_state['default_first_message'] = "Hi! How can I help you?"

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize usage stats
if "usage" not in st.session_state:
    st.session_state.usage = {"prompt_tokens":0,
                              "completion_tokens":0,
                              "total_tokens":0}

if "system_prompt" not in st.session_state:
    with open('prompts/default_assistant.md') as f:
        default_system_prompt = f.read()
        # print(default_system_prompt)
        st.session_state['system_prompt'] = default_system_prompt


with st.sidebar:
    st.session_state['selected_model'] = st.selectbox('Open AI Models', 
                                                      available_models)
    
    st.session_state['temperature'] = st.slider("Temperature", 
                                                min_value=0,
                                                max_value=2, 
                                                value=1)
    
    st.session_state["system_prompt"] = st.text_area("System Message", st.session_state["system_prompt"])


# Chat message history
with st.container():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    

with st.container():
    if user_input := st.chat_input():
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""

            chat_messages = [{"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ]
            
            messages = [{"role":'system', "content":st.session_state['system_prompt']}]
            messages.extend(chat_messages)
            
            for response in openai.ChatCompletion.create(
                model=st.session_state["selected_model"],
                messages=messages,
                stream=True,
            ):
                full_response += response.choices[0].delta.get("content", "")
                # print(response)
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
    







