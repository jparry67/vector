import os
from dotenv import load_dotenv
from google import genai
from llm_base import LLMBase
from logger import get_logger

MODEL = "gemini-2.5-flash-lite"

logger = get_logger(__name__)
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found! Check your .env file.")


class LLMGemini(LLMBase):
    def __init__(self, system_prompt: str, response_schema: dict, callback):
        self.callback = callback
        self.system_prompt = system_prompt
        self.response_schema = response_schema
        self.client = genai.Client(api_key=api_key)
        self.chat = self._create_chat()
        logger.info("Started Gemini with system prompt.")

    def _create_chat(self):
        return self.client.chats.create(
            model=MODEL,
            config={
                "system_instruction": self.system_prompt,
                "response_mime_type": "application/json",
                "response_schema": self.response_schema,
            }
        )

    def send_message(self, message: str):
        try:
            logger.info(f"Sent message to Gemini: {message}")
            response = self.chat.send_message(message)
            reply = response.text
            logger.info(f"Got response from Gemini: {reply}")
            self.callback(reply)
        except Exception as e:
            logger.error(f"Gemini request failed: {e}")

    def reset(self):
        self.chat = self._create_chat()
        logger.info("Gemini chat history reset.")