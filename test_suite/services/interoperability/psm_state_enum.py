from enum import Enum


class State(str, Enum):
    """
    Enum for Scenario modes.
    """

    READY = "READY"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    RETRIEVE_READY = "RETRIEVE_READY"
    RESETTING = "RESETTING"

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))

    @classmethod
    def list_active_states(cls):
        return [cls.RUNNING.value, cls.STOPPING.value]
