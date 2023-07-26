import re
from dataclasses import dataclass
from typing import Any, Callable, Union, Dict, List, Literal
from abc import ABC, abstractmethod

@dataclass
class Event(ABC):
    value: Any = None
    scope_functions: Dict[Literal["Chain", "Node", "LLM", "Message", "Response", "Partial"], 
                         Dict[Literal['filter', 'func'], Callable]] = None
    llm_representation: Union[str, Callable] = lambda value: str(value)
    human_representation: Union[str, Callable] = lambda value: str(value)

@dataclass
class LoadFileEvent(Event):
    def __post_init__(self):
        self.scope_functions = {
            "Message": {
                "filter": lambda msg: self.find_load_file_pattern(msg['content']),
                "func": self.load_file_from_message
            }
        }

    def load_file_from_message(self, message):
        # Extract the file name from the message using regex
        match = self.find_load_file_pattern(message['content'])
        if match:
            file_name = match.group(1)

            try:
                # Read the contents of the file
                with open(file_name, "r") as file:
                    file_contents = file.read()

                # Replace the regex pattern with the file contents in the message
                message['content'] = re.sub(r"{{LOAD_FILE, (.+?)}}", file_contents, message['content'])
                return message

            except FileNotFoundError:
                # Handle the case where the file is not found
                raise FileNotFoundError(f"File '{file_name}' not found.")
            except Exception as e:
                # Handle other exceptions that may occur during file reading
                raise Exception(f"Error reading file '{file_name}': {str(e)}")
        else:
            # Handle the case where the LOAD_FILE pattern is not found in the message
            raise ValueError("Invalid message format. Couldn't find LOAD_FILE pattern.")

    @staticmethod
    def find_load_file_pattern(content):
        return re.search(r"{{LOAD_FILE, (.+?)}}", content)