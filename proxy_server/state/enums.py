from enum import Enum


class State(str, Enum):
    READY = "READY"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    RETRIEVE_READY = "RETRIEVE_READY"
    RESETTING = "RESETTING"

    @classmethod
    def list_active_states(cls) -> list[str]:
        """
        States where session is actively processing.
        Used for polling logic.
        """
        return [
            cls.RUNNING.value,
            cls.STOPPING.value,
        ]

    @classmethod
    def list_terminal_states(cls) -> list[str]:
        """
        States where session reached terminal phase.
        """
        return [
            cls.RETRIEVE_READY.value,
            cls.READY.value,
        ]
