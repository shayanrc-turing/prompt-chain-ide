import openai
from typing import Dict, List
from prompt_chain.event import Event

# openai.api_key = OPENAI_API_KEY

def chat_completion(LLM_dict: Dict[str, any], 
                    prompt_messages: List[Dict[str, str]], 
                    chat_history: List[Dict[str, str]],
                    user_message: Dict[str, str],
                    events: List[Event]=[]) -> Dict[str, any]:
    partial = {'function_name': '', 'function_arguments': '', 'content': ''}

    messages = prompt_messages + chat_history + [user_message]

    processed_messages = []
    for message in messages:
        message_events = list(filter(lambda event: 'Message' in event.scope_functions, events))
        message_events_mask = list(map(lambda event: event.scope_functions['Message']['filter'](message), message_events))

        # Filter out message_events based on message_events_mask
        message_events = [event for event, mask in zip(message_events, message_events_mask) if mask]

        for event in message_events:
            message = event.scope_functions['Message']['func'](message)
        processed_messages.append(message)
        print(message)


    api_response = openai.ChatCompletion.create(
        model=LLM_dict["model"],
        temperature=LLM_dict["temperature"],
        messages=messages,
        stream=True
    )
    for chunk in api_response:
        choices = chunk['choices']
        choice = choices[0]
        delta = choice['delta']

        content = delta.get('content', '')
        partial['content'] += content if isinstance(content, str) else ''

        if 'function_call' in delta:
            delta_function_name = delta['function_call'].get('name', '')
            if len(delta_function_name):
                partial['function_name'] = delta_function_name
            argument_part = delta['function_call']['arguments']
            partial['function_arguments'] += argument_part if isinstance(argument_part, str) else ''

        partial.update({
            'object': chunk['object'],
            'model': chunk['model'],
            'role': delta.get('role', None),
            'finish_reason': choice.get('finish_reason', None)
        })

        yield partial