import requests
from typing import Optional, List

from services.integrations.notification_service import NotificationService


class GridGearsService(NotificationService):
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def notify_test_started(self, test_id: str):
        return requests.post(f"{self.base_url}/test", json={"id": test_id})

    def notify_test_status(self, test_id: str, status: str, verdict: Optional[str] = None, reason: Optional[str] = None):
        payload = {"status": status}
        if verdict:
            payload["verdict"] = verdict
        if reason:
            payload["reason"] = reason
        return requests.post(f"{self.base_url}/test/{test_id}/status", json=payload)

    def notify_step_started(self, step_id: str):
        return requests.post(f"{self.base_url}/step", json={"id": step_id})

    def notify_step_status(self, step_id: str, status: str):
        return requests.post(f"{self.base_url}/step/{step_id}/status", json={"status": status})

    def send_instruction(self, instruction_id: str, message: str, timelimit: int = 30):
        payload = {
            "id": instruction_id,
            "message": message,
            "timelimit": timelimit
        }
        return requests.post(f"{self.base_url}/instructions", json=payload)

    def send_verification(self, verification_id: str, message: str, options: List[str], timelimit: int = 30):
        payload = {
            "id": verification_id,
            "message": message,
            "options": options,
            "timelimit": timelimit
        }
        return requests.post(f"{self.base_url}/verifications", json=payload)

    def send_message_configuration(self, components: List[str]):
        return requests.post(f"{self.base_url}/messages/configuration", json={"components": components})

    def send_message(self, sequenceNr: int, timestamp: str, sender: str, receiver: str,
                     label: str, protocol: str, category: str,
                     content: Optional[str] = None,
                     file_name: Optional[str] = None, line: Optional[int] = None):
        payload = {
            "sequenceNr": sequenceNr,
            "timestamp": timestamp,
            "sender": sender,
            "receiver": receiver,
            "label": label,
            "protocol": protocol,
            "category": category,
        }
        if content:
            payload["content"] = content
        if file_name:
            payload["codeReference"] = {"fileName": file_name}
            if line:
                payload["codeReference"]["line"] = line

        return requests.post(f"{self.base_url}/messages", json=payload)
