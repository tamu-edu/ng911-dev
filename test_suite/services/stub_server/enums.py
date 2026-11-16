from enum import Enum


class StubServerProtocol(str, Enum):
    SIP = "SIP"
    HTTP = "HTTP"
    HTTPS = "HTTPS"

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


class StubServerRole(str, Enum):
    """
    Enum for possible roles of a lab config Entity.
    """

    SENDER = "SENDER"
    RECEIVER = "RECEIVER"
    IUT = "IUT"
    OTHER = "OTHER"
    PROXY_SERVER = "PROXY_SERVER"
    FORWARD_SERVER = "FORWARD_SERVER"

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))
