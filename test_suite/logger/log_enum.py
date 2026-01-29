from enum import Enum
from logging import (
    CRITICAL,
    FATAL,
    ERROR,
    WARNING,
    INFO,
    DEBUG,
    NOTSET,
)

_nameToLevel = {
    'CRITICAL': CRITICAL,
    'FATAL': FATAL,
    'ERROR': ERROR,
    'WARN': WARNING,
    'WARNING': WARNING,
    'INFO': INFO,
    'DEBUG': DEBUG,
    'NOTSET': NOTSET,
}


class LogLevel(str, Enum):
    """
    Enum for Log levels.
    """
    DEBUG = "DEBUG"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    FATAL = "FATAL"
    INFO = "INFO"
    NOTSET = "NOTSET"

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))

    @classmethod
    def get_level_value(cls, level) -> int:
        return _nameToLevel[level]

