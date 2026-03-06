import json
import schedule
import textwrap
import time
from datetime import date

import tasks_db
# from llm_gemini import LLMGemini
from llm_local import LLMLocal
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
                "enum": [
                    "send_message",
                    "schedule_message",
                    "create_task",
                    "edit_task",
                    "complete_task",
                    "delete_task"
                ]
            },
            "content": {"type": "STRING", "nullable": True},
            "time": {"type": "STRING", "nullable": True},
            "task_id": {"type": "INTEGER", "nullable": True},
            "title": {"type": "STRING", "nullable": True},
            "notes": {"type": "STRING", "nullable": True},
            "priority": {"type": "INTEGER", "nullable": True},
            "target_date": {"type": "STRING", "nullable": True}
        },
        "required": ["operation"]
    }
}

tasks_db.init_db()

def load_prompt(name: str) -> str:
    with open(f"prompts/{name}.txt", "r", encoding="utf-8") as f:
        prompt = f.read()

    if "{all_open_tasks}" in prompt:
        tasks = tasks_db.get_formatted_open_tasks()
        prompt = prompt.replace("{all_open_tasks}", tasks)
    
    if "{today}" in prompt:
        today = date.today()
        formatted_date = today.strftime("%Y-%m-%d (%A)")
        prompt = prompt.replace("{today}", formatted_date)

    return prompt

class Vector:
    def __init__(self):
        logger.info("Launching Vector!")
        self.messenger = Messenger()
        self.messenger.set_default_callback(self.handle_user_response)
        schedule.every(10).seconds.do(self.messenger.receive_messages)
        system_prompt = load_prompt("system_prompt_short")
        # self.llm = LLMGemini(system_prompt, response_schema, self.handle_llm_response)
        self.llm = LLMLocal(system_prompt, self.handle_llm_response)

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
        if self.handle_command(message):
            return
        self.messenger.show_typing_indicator()
        blockquoted_message = textwrap.indent(message, '> ')
        llm_prompt = load_prompt("user_response").replace("{blockquoted_message}", blockquoted_message)
        self.llm.send_message(llm_prompt)

    def handle_command(self, message: str) -> bool:
        lower = message.strip().lower()

        if lower.startswith("list tasks"):
            formatted = tasks_db.get_formatted_open_tasks()
            self.send_user_message(f"Here are your open tasks:\n{formatted}")
            return True

        if lower.startswith("add task"):
            task_info = message[len("add task"):].strip().split('\n')
            if len(task_info) != 4:
                self.send_user_message("Please provide all task info separated by new lines. e.g...")
                self.send_user_message("Add task\nCreate POC of project\nWe need to make sure to use the right API.\n2\n2026-03-05")
                return True
            title,notes,priority,target_date = task_info
            task = tasks_db.create_task(title=title, notes=notes, priority=int(priority), target_date=target_date)
            self.send_user_message(f"Task added: [{task['id']}] ✅\n{task['title']}\n{task['notes']}\n{task['priority']}\n{task['target_date']}")
            return True

        if lower.startswith("complete task"):
            arg = message[len("complete task"):].strip()
            try:
                task_id = int(arg)
                task = tasks_db.complete_task(task_id=task_id)
                if task:
                    self.send_user_message(f"Marked complete: [{task['id']}] {task['title']} 🏁")
                else:
                    self.send_user_message(f"Couldn't find task {task_id}.")
            except ValueError:
                self.send_user_message("Please provide a task ID. e.g. 'Complete task 3'")
            return True

        if lower.startswith("delete task"):
            arg = message[len("delete task"):].strip()
            try:
                task_id = int(arg)
                tasks_db.delete_task(task_id=task_id)
                self.send_user_message(f"Task {task_id} deleted. 🗑️")
            except ValueError:
                self.send_user_message("Please provide a task ID. e.g. 'Delete task 3'")
            return True

        if lower.startswith("edit task"):
            task_info = message[len("edit task"):].strip().split('\n')
            if len(task_info) != 5:
                self.send_user_message("Please provide all task info separated by new lines. e.g...")
                self.send_user_message("Edit task 3\nCreate POC of project\nWe need to make sure to use the right API.\n2\n2026-03-05")
                return True
            id,title,notes,priority,target_date = task_info
            task = tasks_db.edit_task(task_id=int(id), title=title, notes=notes, priority=int(priority), target_date=target_date)
            self.send_user_message(f"Task [{task['id']}] edited: ✅\n{task['title']}\n{task['notes']}\n{task['priority']}\n{task['target_date']}")
            return True

        return False

    def handle_llm_response(self, message):
        try:
            operations = json.loads(message)
            
            for op in operations:
                operation_type = op.get("operation")

                match operation_type:
                    case "send_message":
                        self.send_user_message(op.get("content"))

                    case "schedule_message":
                        schedule.every().day.at(op.get("time")).do(self.schedule_send_user_message, message=op.get("content"))

                    case "create_task":
                        created_task = tasks_db.create_task(
                            title=op.get("title"),
                            notes=op.get("notes"),
                            priority=op.get("priority"),
                            target_date=op.get("target_date")
                        )
                        self.llm.send_message(f"Created task successfully: {json.dumps(created_task)}")

                    case "edit_task":
                        updated_task = tasks_db.edit_task(
                            task_id=op.get("task_id"),
                            title=op.get("title"),
                            notes=op.get("notes"),
                            priority=op.get("priority"),
                            target_date=op.get("target_date")
                        )
                        self.llm.send_message(f"Updated task successfully: {json.dumps(updated_task)}")

                    case "complete_task":
                        updated_task = tasks_db.complete_task(task_id=op.get("task_id"))
                        self.llm.send_message(f"Updated task successfully: {json.dumps(updated_task)}")

                    case "delete_task":
                        task_deleted = tasks_db.delete_task(task_id=op.get("task_id"))
                        if task_deleted:
                            self.llm.send_message("Successfully deleted task")

                    case _:
                        logger.error(f"Unknown operation received: {operation_type}")

        except json.JSONDecodeError:
            logger.error("Error: Received invalid JSON from the model.")
        except Exception as e:
            logger.error(f"An error occurred: {e}")