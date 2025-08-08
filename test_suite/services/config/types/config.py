import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from functools import wraps
from typing import Callable
from typing import List, Optional, Dict

from logger.logger_service import LoggingMeta


class Config(ABC):
    """
    Abstract base class for all configuration types.
    Enforces the implementation of required methods.
    """
    _is_validated = False

    @staticmethod
    def validated(method: Callable):
        """
        Decorator to ensure the configuration is validated before running a method.

        Args:
            method (Callable): The method to wrap.

        Returns:
            Callable: The wrapped method.
        """

        @wraps(method)
        def wrapper(self, *args, **kwargs):
            if not self._is_validated:
                raise ValueError(f"{self.__class__.__name__} has not been validated yet. Call self.validate() before")
            return method(self, *args, **kwargs)

        return wrapper

    @abstractmethod
    def validate(self) -> bool:
        """
        Validate the configuration.
        Must be implemented in derived classes.
        """
        pass

    @abstractmethod
    def to_dict(self) -> Dict:
        """
        Convert the configuration object to a dictionary.
        Must be implemented in derived classes.
        """
        pass

    @validated
    def pretty_print(self):
        """
        Print the configuration.
        Should be implemented in derived classes.
        """
        print(json.dumps(self.to_dict(), indent=4))
