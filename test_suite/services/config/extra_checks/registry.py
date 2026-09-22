# extra_checks/registry.py

from typing import Type, Dict, Callable, TypeVar, Any

F = TypeVar("F", bound=Callable[..., Any])

CHECK_REGISTRY: Dict[str, Type] = {}


def register(method: F) -> F:
    """
    Decorator to register extra check classes by their class name.
    Prevents duplicates.
    """
    name = method.__name__

    if name in CHECK_REGISTRY:
        raise RuntimeError(f"Duplicate check registration detected: {name}")

    CHECK_REGISTRY[name] = method
    return method


def has_check(name: str) -> bool:
    """
    Equivalent of hasattr(checks, name)
    """
    return name in CHECK_REGISTRY


def get_check(name: str) -> Callable[..., Any]:
    """
    Safe resolver. Raises explicit error if missing.
    """
    try:
        return CHECK_REGISTRY[name]
    except KeyError:
        raise ValueError(f"Unknown extra check: {name}") from None
