from __future__ import annotations
from typing import Callable, Any, Dict
from . import methods


class LogicError(RuntimeError):
    pass


def load_callable(path: str) -> Callable[[str, Dict[str, Any]], str]:
    """
    Accepts either 'func' (from methods.py) or 'module:func'.
    Returns a callable: func(message_text: str, context: dict) -> str
    """
    # allow both "func" and "methods:func" syntaxes
    func_name = path.split(":", 1)[-1]  # if colon absent, returns path as-is
    try:
        fn = getattr(methods, func_name)
    except Exception as e:
        raise LogicError(f"Function '{func_name}' not found in 'methods': {e}") from e
    if not callable(fn):
        raise LogicError(f"'{path}' is not callable")
    return fn
