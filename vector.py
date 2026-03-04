import json
import schedule
import textwrap
import time
from llm import LLM
from logger import get_logger
from messenger import Messenger

logger = get_logger(__name__)

LLM_RESPONSE_SCHEMA = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            "operation": {
                "type": "STRING", 
                "enum": ["send_message", "schedule_message"]
            },
            "content": {"type": "STRING"},
            "time": {"type": "STRING", "nullable": True}
        },
        "required": ["operation", "content"]
    }
}

def load_prompt(name: str) -> str:
    with open(f"prompts/{name}.txt", "r", encoding="utf-8") as f:
        return f.read()

class Vector:
    def __init__(self):
        logger.info("Launching Vector!")
        self.messenger = Messenger()
        self.messenger.set_default_callback(self.handle_user_response)
        schedule.every(10).seconds.do(self.messenger.receive_messages)
        self.llm = LLM(load_prompt("system_prompt"), LLM_RESPONSE_SCHEMA, self.handle_llm_response)

    def kickoff_day(self):
        self.messenger.show_typing_indicator()
        self.llm.send_message(load_prompt("kickoff"))

    def wrapup_day(self):
        self.messenger.show_typing_indicator()
        self.llm.send_message(load_prompt("wrapup"))

    def send_user_message(self, message):
        self.messenger.show_typing_indicator()
        time.sleep(2)
        self.messenger.hide_typing_indicator()
        self.messenger.send_message(message)

    def schedule_send_user_message(self, message):
        self.send_user_message(message)
        return schedule.CancelJob

    def handle_user_response(self, message):
        self.messenger.show_typing_indicator()
        blockquoted_message = textwrap.indent(message, '> ')
        llm_prompt = load_prompt("user_response").replace("{blockquoted_message}", blockquoted_message)
        self.llm.send_message(llm_prompt)

    def handle_llm_response(self, message):
        try:
            operations = json.loads(message)
            
            for op in operations:
                operation_type = op.get("operation")
                content = op.get("content")
                time = op.get("time")

                match operation_type:
                    case "send_message":
                        self.send_user_message(content)

                    case "schedule_message":
                        schedule.every().day.at(time).do(self.schedule_send_user_message, message=content)

                    case _:
                        logger.error(f"Unknown operation received: {operation_type}")

        except json.JSONDecodeError:
            logger.error("Error: Received invalid JSON from the model.")
        except Exception as e:
            logger.error(f"An error occurred: {e}")