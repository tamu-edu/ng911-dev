from enum import Enum


class StubServerProtocol(str, Enum):
    SIP = "SIP"
    HTTP = "HTTP"

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


class StubServerRole(str, Enum):
    """
    Enum for possible roles of a Stub Server.
    """

    SENDER = "SENDER"
    RECEIVER = "RECEIVER"
    IUT = "IUT"
    OTHER = "OTHER"

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))

