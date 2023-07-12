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


def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

    
def num_tokens_from_messages(messages, model="gpt-3.5-turbo-0613", excluded_keys=['num_tokens']):
    """Return the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    
    if model in {
        "gpt-3.5-turbo-0613",
        "gpt-3.5-turbo-16k-0613",
        "gpt-4-0314",
        "gpt-4-32k-0314",
        "gpt-4-0613",
        "gpt-4-32k-0613",
        }:
        tokens_per_message = 3
        tokens_per_name = 1
    elif model == "gpt-3.5-turbo-0301":
        tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_name = -1  # if there's a name, the role is omitted
    elif "gpt-3.5-turbo" in model:
        print("Warning: gpt-3.5-turbo may update over time. Returning num tokens assuming gpt-3.5-turbo-0613.")
        return num_tokens_from_messages(messages, model="gpt-3.5-turbo-0613")
    elif "gpt-4" in model:
        print("Warning: gpt-4 may update over time. Returning num tokens assuming gpt-4-0613.")
        return num_tokens_from_messages(messages, model="gpt-4-0613")
    else:
        raise NotImplementedError(
            f"""num_tokens_from_messages() is not implemented for model {model}. See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens."""
        )
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            if key == "name":
                num_tokens += tokens_per_name
            elif key in excluded_keys:
                continue
            num_tokens += len(encoding.encode(value))
            
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens

available_models = sorted(get_available_models())


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
                              "total_tokens":0,
                              "num_requests":0}

    st.session_state.usage = model_usage

if "available_system_prompts" not in st.session_state:
    st.session_state["available_system_prompts"] = get_available_system_prompts()




with st.sidebar:
    st.session_state['selected_model'] = st.selectbox('Open AI Models', 
                                                      available_models)
    
    st.session_state['selected_system_prompt'] = st.selectbox('System Prompts', 
                                                              st.session_state["available_system_prompts"].keys(),
                                                              index=2
                                                              )
    
    system_text = st.session_state["available_system_prompts"][st.session_state['selected_system_prompt']]


    
    
    st.session_state['temperature'] = st.slider("Temperature", 
                                                step=5,
                                                min_value=0,
                                                max_value=200, 
                                                value=100)
    
    st.session_state["system_prompt"] = st.text_area("System Message", system_text)


# # Chat message history
# with st.container():
#     for message in st.session_state.messages:
#         with st.chat_message(message["role"]):
#             st.markdown(message["content"])
    
# with st.container():
#     if user_input := st.chat_input():
#         st.session_state.messages.append({"role": "user", "content": user_input})
#         with st.chat_message("user"):
#             st.markdown(user_input)

#         with st.chat_message("assistant"):
#             message_placeholder = st.empty()
#             full_response = ""

#             chat_messages = [{"role": m["role"], "content": m["content"]}
#                     for m in st.session_state.messages
#                 ]
            
#             messages = [{"role":'system', "content":st.session_state['system_prompt']}]
#             messages.extend(chat_messages)
            
#             for response in openai.ChatCompletion.create(
#                 model=st.session_state["selected_model"],
#                 messages=messages,
#                 stream=True,
#             ):
#                 full_response += response.choices[0].delta.get("content", "")
#                 # print(response)
#                 message_placeholder.markdown(full_response + "▌")
#             message_placeholder.markdown(full_response)
#         st.session_state.messages.append({"role": "assistant", "content": full_response})

    
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

            prompt_tokens_count = num_tokens_from_messages(messages, model=st.session_state["selected_model"])  # count tokens here
            st.session_state.usage[st.session_state["selected_model"]]["prompt_tokens"] += prompt_tokens_count
            st.session_state.usage[st.session_state["selected_model"]]["total_tokens"] += prompt_tokens_count

            for response in openai.ChatCompletion.create(
                model=st.session_state["selected_model"],
                temperature=st.session_state['temperature']/100,
                messages=messages,
                stream=True,
            ):
                full_response += response.choices[0].delta.get("content", "")
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
        
        response_message = {"role": "assistant", "content": full_response}
        st.session_state.messages.append(response_message)
        completion_tokens_count = num_tokens_from_messages([response_message], model=st.session_state["selected_model"])  # count tokens here
        st.session_state.usage[st.session_state["selected_model"]]["prompt_tokens"] += completion_tokens_count
        st.session_state.usage[st.session_state["selected_model"]]["total_tokens"] += completion_tokens_count
        st.session_state.usage[st.session_state["selected_model"]]["num_requests"] += 1

        

        st.write(f"Consumed prompt tokens: {prompt_tokens_count} ")  # displaying the prompt tokens count
        st.write(f"Consumed prompt tokens: {completion_tokens_count} ")  # displaying the generated tokens count
        num_reqs = st.session_state.usage[st.session_state["selected_model"]]["num_requests"]
        st.write(f"Consumed prompt tokens: {num_reqs} ")  # displaying the consumed tokens






