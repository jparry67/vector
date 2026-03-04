import os
import requests
from dotenv import load_dotenv
from logger import get_logger

logger = get_logger(__name__)
load_dotenv()

signal_api_url = os.getenv("SIGNAL_API_URL")
if not signal_api_url:
    raise ValueError("SIGNAL_API_URL not found! Check your .env file.")

# your Signal number in international format
user_number = os.getenv("USER_NUMBER")
if not user_number:
    raise ValueError("USER_NUMBER not found! Check your .env file.")

# separate Signal number for Vector to control
vector_number = os.getenv("VECTOR_NUMBER")
if not vector_number:
    raise ValueError("VECTOR_NUMBER not found! Check your .env file.")

class Messenger:
    def __init__(self):
        self.all_messages = []
        self.last_callback = None
        self.default_callback = None

    def set_default_callback(self, callback):
        self.default_callback = callback

    def show_typing_indicator(self):
        url = f"{signal_api_url}/v1/typing-indicator/{vector_number}"
        payload = {
            "recipient": user_number,
        }
        try:
            response = requests.put(url, json=payload)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to show typing indicator: {e}")

    def hide_typing_indicator(self):
        url = f"{signal_api_url}/v1/typing-indicator/{vector_number}"
        payload = {
            "recipient": user_number,
        }
        try:
            response = requests.delete(url, json=payload)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to hide typing indicator: {e}")
    
    def send_message(self, message: str, callback=None) -> bool:
        url = f"{signal_api_url}/v2/send"
        payload = {
            "message": message,
            "number": vector_number,
            "recipients": [user_number]
        }
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            logger.info(f"Message sent: {message}")
            self.all_messages.append({"from": "Vector", "text": message})
            if callback:
                self.last_callback = callback
            return True
        except requests.RequestException as e:
            logger.error(f"Failed to send message: {e}")
            return False

    def receive_messages(self) -> bool:
        url = f"{signal_api_url}/v1/receive/{vector_number}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            raw = response.json()
            user_messages = [
                {"text": m.get("envelope", {}).get("dataMessage", {}).get("message"), "timestamp": m.get("envelope", {}).get("timestamp", 0)}
                for m in raw
                if m.get("envelope", {}).get("dataMessage", {}).get("message")
                and m.get("envelope", {}).get("sourceNumber") == user_number
            ]
            for m in user_messages:
                self.send_read_receipt(m["timestamp"])
            user_text = "\n".join([m["text"] for m in user_messages])
            if user_text:
                self.all_messages.append({"from": user_number, "text": user_text})
                logger.info(f"Received message: {user_text}")
                if self.last_callback:
                    self.last_callback(user_text)
                    self.last_callback = None
                elif self.default_callback:
                    self.default_callback(user_text)
                else:
                    logger.info(f"Message not handled: {user_text}")
                return True
            return False
        except requests.RequestException as e:
            logger.error(f"Failed to receive messages: {e}")
            return False

    def send_read_receipt(self, timestamp):
        url = f"{signal_api_url}/v1/receipts/{vector_number}"
        payload = {
            "receipt_type": "read",
            "recipient": user_number,
            "timestamp": timestamp,
        }
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to send read receipt: {e}")
