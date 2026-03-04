import os
from dotenv import load_dotenv
from google import genai
from logger import get_logger

MODEL = "gemini-2.5-flash-lite"

logger = get_logger(__name__)
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found! Check your .env file.")

class LLM:
    def __init__(self, system_prompt, response_schema, callback):
        self.callback = callback
        self.client = genai.Client(api_key)
        self.chat = self.client.chats.create(
            model=MODEL,
            config={
                'system_instruction': system_prompt,
                'response_mime_type': "application/json",
                'response_schema': response_schema,
            }
        )
        logger.info("Started Gemini with system prompt")

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
        self.chat = self.model.start_chat(history=[])
        logger.info("Gemini chat history reset.")