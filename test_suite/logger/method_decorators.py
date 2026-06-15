import logging
import functools
import inspect
import traceback


def _pretty(value, indent=0):
    space = "  " * indent

    # Packet (pyshark)
    if hasattr(value, "layers") and hasattr(value, "number"):
        return f"\n{str(value)}"

    # dict
    if isinstance(value, dict):
        items = []
        for k, v in value.items():
            items.append(f"{space}{k}: {_pretty(v, indent + 1)}")
        return "\n".join(items)

    # list / tuple
    if isinstance(value, (list, tuple)):
        items = []
        for i, v in enumerate(value):
            items.append(f"{space}[{i}] {_pretty(v, indent + 1)}")
        return "\n".join(items)

    # fallback
    return str(value)


def log_method_args(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger("MethodLoggerService")

        sig = inspect.signature(func)
        bound = sig.bind_partial(*args, **kwargs)
        bound.apply_defaults()

        params = "\n".join(
            f"{name} = {value}" for name, value in bound.arguments.items()
        )

        logger.debug(f"\n--- Method: {func.__name__} ---\n{params}\n")

        return func(*args, **kwargs)

    return wrapper


def log_method_result(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger("MethodLoggerService")

        try:
            result = func(*args, **kwargs)

            pretty = _pretty(result)

            logger.debug(
                f"\n--- Method: {func.__name__} RETURN ---\n" f"{str(pretty)}\n"
            )

            return result

        except Exception as e:
            logger.error(
                f"\n--- Method: {func.__name__} EXCEPTION ---\n"
                f"{type(e).__name__}: {e}\n"
                f"{traceback.format_exc()}"
            )
            raise

    return wrapper
