import ollama
from llm_base import LLMBase
from logger import get_logger

MODEL = "llama3.1"

logger = get_logger(__name__)


class LLMLocal(LLMBase):
    def __init__(self, system_prompt: str, callback):
        self.callback = callback
        self.system_prompt = system_prompt
        self.history = []
        logger.info("Started local LLM with system prompt.")

    def send_message(self, message: str):
        self.history.append({"role": "user", "content": message})
        try:
            logger.info(f"Sent message to local LLM: {message}")
            response = ollama.chat(
                model=MODEL,
                messages=[{"role": "system", "content": self.system_prompt}] + self.history
            )
            reply = response["message"]["content"].strip().removeprefix("```json").removesuffix("```").strip()
            self.history.append({"role": "assistant", "content": reply})
            logger.info(f"Got response from local LLM: {reply}")
            self.callback(reply)
        except Exception as e:
            logger.error(f"Local LLM request failed: {e}")

    def reset(self):
        self.history = []
        logger.info("Local LLM chat history reset.")