import re
import sys
import logging
import inspect
import warnings
import functools
from datetime import datetime
from .log_enum import LogLevel


class TeeStream:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for s in self.streams:
            try:
                s.write(data)
                s.flush()
            except Exception as e:
                _logger = logging.getLogger("LoggerService")
                _logger.debug(e)

    def flush(self):
        for s in self.streams:
            try:
                s.flush()
            except Exception as e:
                _logger = logging.getLogger("LoggerService")
                _logger.debug(e)


_DISPLAY_NAMES = {
    "LoggerService": "main",
    "CheckLoggerService": "check",
    "TestAssessLoggerService": "assess",
    "MethodLoggerService": "method",
}
_NAME_WIDTH = max(len(name) for name in _DISPLAY_NAMES.values())


_ADDR_RE = re.compile(r"<([A-Za-z_][\w.]*) object at 0x[0-9a-fA-F]+>")


class ReadableFileFormatter(logging.Formatter):
    _LEVEL_WIDTH = 8

    def __init__(self):
        super().__init__(
            fmt="%(asctime)s | %(levelname)-8s | %(paddedname)s | %(message)s",
            datefmt="%H:%M:%S",
        )

    def format(self, record):
        display = _DISPLAY_NAMES.get(record.name, record.name)
        name_width = max(_NAME_WIDTH, len(display))
        record.paddedname = f"{display:<{name_width}}"

        original_msg = record.msg
        if isinstance(record.msg, str):
            record.msg = record.msg.strip("\n")
        try:
            result = super().format(record)
        finally:
            record.msg = original_msg

        result = _ADDR_RE.sub(lambda m: f"<{m.group(1).rsplit('.', 1)[-1]}>", result)

        if "\n" in result:
            first, *rest = result.split("\n")
            # Prefix width = time + " | " + level + " | " + name + " | "
            prefix_width = 8 + 3 + self._LEVEL_WIDTH + 3 + name_width + 1
            pad = " " * prefix_width
            rest = [f"{pad}| {line}" for line in rest]
            result = "\n".join([first, *rest])
        return result


class LoggerService:
    """Centralized logging service with flexible levels."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        """Singleton implementation to ensure only one logger instance."""
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._initialize(*args, **kwargs)
        return cls._instance

    def _initialize(
        self,
        level: LogLevel,
        output_file: str | None = None,
        dev_mode: bool | None = False,
    ):
        self.dev_mode = bool(dev_mode)

        if not output_file or len(output_file) == 0 or not isinstance(output_file, str):
            logging.basicConfig(level=logging.NOTSET)
            self.logger = logging.getLogger("LoggerService")
            log_level = LogLevel.get_level_value(level)
            self.logger.setLevel(log_level)

            # Stream handler (logs to console)
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(log_level)
            stream_handler.setFormatter(logging.Formatter("%(message)s"))
            self.logger.addHandler(stream_handler)

            # Redirect print() to logger
            sys.stdout = self

        # File handler (logs to a file if output_file is provided)
        if output_file:
            self.logger = logging.getLogger("LoggerService")
            log_level = LogLevel.get_level_value(level)
            self.logger.setLevel(log_level)

            with open(output_file, "a", encoding="utf-8") as _f:
                _f.write(f"===== Test Suite log | {datetime.now():%Y-%m-%d} =====\n")

            file_handler = logging.FileHandler(output_file, encoding="utf-8")
            file_handler.setLevel(log_level)
            file_handler.setFormatter(ReadableFileFormatter())
            self.logger.addHandler(file_handler)

            warnings.showwarning = (
                lambda message, category, filename, lineno, file=None, line=None: (
                    logging.getLogger("LoggerService").warning(
                        f"{category.__name__} in {filename}:{lineno}: {message}"
                    )
                )
            )

        check_logger = logging.getLogger("CheckLoggerService")
        check_logger.setLevel(logging.DEBUG)

        asses_logger = logging.getLogger("TestAssessLoggerService")
        asses_logger.setLevel(logging.DEBUG)

        method_logger = logging.getLogger("MethodLoggerService")
        method_logger.setLevel(logging.DEBUG)

        for handler in self.logger.handlers:
            check_logger.addHandler(handler)
            asses_logger.addHandler(handler)
            method_logger.addHandler(handler)

        if dev_mode:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(LogLevel.get_level_value(level))
            console_handler.setFormatter(logging.Formatter("%(message)s"))

            # only for specific loggers
            for name in [
                "CheckLoggerService",
                "TestAssessLoggerService",
                "MethodLoggerService",
            ]:
                logger = logging.getLogger(name)
                logger.addHandler(console_handler)

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

    @staticmethod
    def shutdown_logging():
        """Flush and close all logging handlers safely."""
        root = logging.getLogger("LoggerService")

        for handler in root.handlers[:]:
            try:
                handler.flush()
                handler.close()
            except Exception as e:
                _logger = logging.getLogger("LoggerService")
                _logger.debug(e)
            root.removeHandler(handler)


def _indent(text: str, prefix: str = "    ") -> str:
    return "\n".join(prefix + line for line in text.split("\n"))


def _describe_call(method, method_name, args, kwargs, is_static=False):
    """Build a readable 'Calling: Class.method' block with named args, self skipped."""
    try:
        sig = inspect.signature(method)
        bound = sig.bind_partial(*args, **kwargs)
        items = list(bound.arguments.items())
    except (TypeError, ValueError):
        items = [(f"arg{i}", a) for i, a in enumerate(args)] + list(kwargs.items())

    cls_name = ""
    if not is_static and items and items[0][0] in ("self", "cls"):
        first = items[0][1]
        cls_name = (
            type(first).__name__
            if items[0][0] == "self"
            else getattr(first, "__name__", "")
        )
        items = items[1:]

    label = f"{cls_name}.{method_name}" if cls_name else method_name
    if not items:
        return label, f"Calling: {label}()"

    lines = []
    for name, value in items:
        text = str(value)
        if "\n" in text:
            lines.append(f"  {name} =\n{_indent(text)}")
        else:
            lines.append(f"  {name} = {text}")
    return label, f"Calling: {label}\n" + "\n".join(lines)


def _describe_result(label, result) -> str:
    text = str(result)
    if "\n" in text or len(text) > 100:
        return f"{label} returned:\n{_indent(text, '  ')}"
    return f"{label} returned: {text}"


class LoggingMeta(type):
    """Metaclass to inject logging into methods."""

    def __new__(cls, name, bases, dct):
        for attr_name, attr_value in dct.items():
            if callable(attr_value):
                # Check if the attribute is a static method
                if isinstance(attr_value, staticmethod):
                    # Use a special wrapper for static methods
                    wrapped_method = cls.wrap_static_with_logging(
                        attr_name, attr_value.__func__
                    )
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
            label, call_text = _describe_call(method, method_name, args, kwargs)
            logger.debug(call_text)
            try:
                result = method(*args, **kwargs)
                logger.info(_describe_result(label, result))
                return result
            except Exception as e:
                logger.error(f"Error in method {label}: {e}")
                raise

        return wrapped

    @staticmethod
    def wrap_static_with_logging(method_name, method):
        """Wrap static methods with logging."""

        @functools.wraps(method)
        def wrapped(*args, **kwargs):
            logger = logging.getLogger("LoggerService")
            label, call_text = _describe_call(
                method, method_name, args, kwargs, is_static=True
            )
            logger.debug(f"[static] {call_text}")
            try:
                result = method(*args, **kwargs)
                logger.info(_describe_result(label, result))
                return result
            except Exception as e:
                logger.error(f"Error in static method {label}: {e}")
                raise

        return wrapped
