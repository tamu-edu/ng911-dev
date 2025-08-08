from typing import Optional, List
from abc import ABC, abstractmethod


class NotificationService(ABC):
    @abstractmethod
    def notify_test_started(self, test_id: str): ...

    @abstractmethod
    def notify_test_status(self, test_id: str, status: str, verdict: Optional[str] = None, reason: Optional[str] = None): ...

    @abstractmethod
    def notify_step_started(self, step_id: str): ...

    @abstractmethod
    def notify_step_status(self, step_id: str, status: str): ...

    @abstractmethod
    def send_instruction(self, instruction_id: str, message: str, timelimit: int = 30): ...

    @abstractmethod
    def send_verification(self, verification_id: str, message: str, options: List[str], timelimit: int = 30): ...

    @abstractmethod
    def send_message_configuration(self, components: List[str]): ...

    @abstractmethod
    def send_message(self, sequenceNr: int, timestamp: str, sender: str, receiver: str,
                     label: str, protocol: str, category: str,
                     content: Optional[str] = None,
                     file_name: Optional[str] = None, line: Optional[int] = None): ...
