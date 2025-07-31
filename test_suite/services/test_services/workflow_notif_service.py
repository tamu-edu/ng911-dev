import uuid
import datetime
from typing import Optional, List
from services.integrations.notification_service import NotificationService


def skip_if_disabled(func):
    def wrapper(self, *args, **kwargs):
        if self.sender is None:
            return
        return func(self, *args, **kwargs)
    return wrapper


class WorkflowNotificationService:
    sender: NotificationService = None

    def __init__(self, sender: NotificationService = None):
        self.sender = sender
        self.sequence_counter = 1  # for message tracing

    @skip_if_disabled
    def on_test_start(self, test_id: str):
        self.sender.notify_test_started(test_id)
        self.sender.notify_test_status(test_id, status="running")

    @skip_if_disabled
    def on_test_finish(self, test_id: str, verdict: str, reason: Optional[str] = None):
        self.sender.notify_test_status(test_id, status="done", verdict=verdict, reason=reason)

    @skip_if_disabled
    def on_variation_start(self, step_id: str):
        self.sender.notify_step_started(step_id)

    @skip_if_disabled
    def on_variation_finish(self, step_id: str, status: str):
        self.sender.notify_step_status(step_id, status=status)

    @skip_if_disabled
    def on_manual_instruction(self, message: str, timelimit: int = 30) -> str:
        instruction_id = str(uuid.uuid4())
        self.sender.send_instruction(instruction_id, message, timelimit=timelimit)
        return instruction_id

    @skip_if_disabled
    def on_verification_request(self, message: str, options: List[str], timelimit: int = 30) -> str:
        verification_id = str(uuid.uuid4())
        self.sender.send_verification(verification_id, message, options, timelimit=timelimit)
        return verification_id

    @skip_if_disabled
    def send_message_configuration(self, components: List[str]):
        self.sender.send_message_configuration(components)

    @skip_if_disabled
    def trace_message(self, sender: str, receiver: str, label: str, protocol: str,
                      category: str, content: Optional[str] = None,
                      file_name: Optional[str] = None, line: Optional[int] = None):
        timestamp = datetime.datetime.utcnow().isoformat() + "Z"
        self.sender.send_message(
            sequenceNr=self.sequence_counter,
            timestamp=timestamp,
            sender=sender,
            receiver=receiver,
            label=label,
            protocol=protocol,
            category=category,
            content=content,
            file_name=file_name,
            line=line
        )
        self.sequence_counter += 1
