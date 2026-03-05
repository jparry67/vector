from abc import ABC, abstractmethod

class LLMBase(ABC):
    @abstractmethod
    def send_message(self, message: str):
        pass

    @abstractmethod
    def reset(self):
        pass
