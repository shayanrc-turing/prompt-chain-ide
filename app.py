import streamlit as st
import openai
# from litechain.contrib import OpenAIChatChain, OpenAIChatMessage, OpenAIChatDelta
# import asyncio
import tiktoken
import glob






st.title('Prompt IDE')

openai.api_key = st.secrets['OPANAI_API_KEY']

# @st.cache(ttl=360)
def get_available_models():
    resp = openai.Model.list()
    models = []
    if 'data' in resp:
        for model in resp['data']:
            if 'gpt' in model['id']:
                models.append(model['id'])
    return models



import glob

def get_available_system_prompts():
    available_prompts = {}

    for prompt_file in glob.glob("prompts/system_prompts/*.md"):
        prompt_name = prompt_file.split("/")[-1].split(".md")[0]
        with open(prompt_file, "r") as file:
            prompt_text = file.read()
        available_prompts[prompt_name] = prompt_text

    return available_prompts





available_models = get_available_models()
available_models = sorted(available_models)

if 'default_first_message' not in st.session_state:
    st.session_state['default_first_message'] = "Hi! How can I help you?"

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize usage stats
if "usage" not in st.session_state:
    model_usage = {}
    for model in available_models:
        model_usage[model] = {"prompt_tokens":0,
                              "completion_tokens":0,
                              "total_tokens":0}

    st.session_state.usage = model_usage

if "available_system_prompts" not in st.session_state:
    st.session_state["available_system_prompts"] = get_available_system_prompts()

# if "system_prompt" not in st.session_state:
#     # with open('prompts/system_prompts/default_assistant.md') as f:
        
#         st.session_state['system_prompt'] = st.session_state["available_system_prompts"].get("default_assistant", "")
        



with st.sidebar:
    st.session_state['selected_model'] = st.selectbox('Open AI Models', 
                                                      available_models)
    
    st.session_state['selected_system_prompt'] = st.selectbox('System Prompts', 
                                                              st.session_state["available_system_prompts"].keys(),
                                                              index=2
                                                              )
    
    system_text = st.session_state["available_system_prompts"][st.session_state['selected_system_prompt']]

    

    

    
    
    
    st.session_state['temperature'] = st.slider("Temperature", 
                                                min_value=0,
                                                max_value=2, 
                                                value=1)
    
    st.session_state["system_prompt"] = st.text_area("System Message", system_text)


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

def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens
    







