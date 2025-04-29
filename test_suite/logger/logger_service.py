import sys
import logging
import warnings
import functools
from .log_enum import LogLevel


class LoggerService:
    """Centralized logging service with flexible levels."""
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Singleton implementation to ensure only one logger instance."""
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._initialize(*args, **kwargs)
        return cls._instance

    def _initialize(self, level: LogLevel, output_file: str | None = None):
        if not output_file or len(output_file) == 0 or not isinstance(output_file, str):
            logging.basicConfig(level=logging.NOTSET)
            self.logger = logging.getLogger("LoggerService")
            log_level = LogLevel.get_level_value(level)
            self.logger.setLevel(log_level)

            # Stream handler (logs to console)
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(log_level)
            stream_handler.setFormatter(logging.Formatter('%(message)s'))
            self.logger.addHandler(stream_handler)

            # Redirect print() to logger
            sys.stdout = self

        # File handler (logs to a file if output_file is provided)
        if output_file:
            self.logger = logging.getLogger("LoggerService")
            log_level = LogLevel.get_level_value(level)
            self.logger.setLevel(log_level)

            file_handler = logging.FileHandler(output_file)
            file_handler.setLevel(log_level)
            file_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s -- %(asctime)s'))
            self.logger.addHandler(file_handler)

            warnings.showwarning = lambda message, category, filename, lineno, file=None, line=None: (
                logging.getLogger("LoggerService").warning(f"{category.__name__} in {filename}:{lineno}: {message}"))

    def write(self, message):
        """Redirect print() calls to logger."""
        if message.strip():  # Avoid logging empty messages
            self.logger.info(message.strip())

    def flush(self):
        """Flush method for compatibility with sys.stdout."""
        pass

    def log(self, message: str, level: str = "INFO"):
        """Log a message with a specified level."""
        log_method = getattr(self.logger, level.lower(), None)
        if callable(log_method):
            log_method(message)
        else:
            self.logger.info(message)


class LoggingMeta(type):
    """Metaclass to inject logging into methods."""
    def __new__(cls, name, bases, dct):
        for attr_name, attr_value in dct.items():
            if callable(attr_value):
                # Check if the attribute is a static method
                if isinstance(attr_value, staticmethod):
                    # Use a special wrapper for static methods
                    wrapped_method = cls.wrap_static_with_logging(attr_name, attr_value.__func__)
                    dct[attr_name] = staticmethod(wrapped_method)
                else:
                    # Use the standard wrapper for instance or class methods
                    dct[attr_name] = cls.wrap_with_logging(attr_name, attr_value)
        return super().__new__(cls, name, bases, dct)

    @staticmethod
    def wrap_with_logging(method_name, method):
        """Wrap instance or class methods with logging."""
        @functools.wraps(method)
        def wrapped(*args, **kwargs):
            logger = logging.getLogger("LoggerService")
            logger.debug(f"Calling method: {method_name} with args: {args}, kwargs: {kwargs}")
            try:
                result = method(*args, **kwargs)
                logger.info(f"Method {method_name} returned: {result}")
                return result
            except Exception as e:
                logger.error(f"Error in method {method_name}: {e}")
                raise
        return wrapped

    @staticmethod
    def wrap_static_with_logging(method_name, method):
        """Wrap static methods with logging."""
        @functools.wraps(method)
        def wrapped(*args, **kwargs):
            logger = logging.getLogger("LoggerService")
            logger.debug(f"Calling static method: {method_name} with args: {args}, kwargs: {kwargs}")
            try:
                result = method(*args, **kwargs)
                logger.info(f"Static method {method_name} returned: {result}")
                return result
            except Exception as e:
                logger.error(f"Error in static method {method_name}: {e}")
                raise
        return wrapped
