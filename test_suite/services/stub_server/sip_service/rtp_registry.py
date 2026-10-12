import threading
from typing import Any

_MEDIA_RESOURCES: set[Any] = set()
_lock = threading.Lock()


def register_media_resource(
    resource: Any,
) -> None:
    """
    Register a runtime media resource exposing stop().
    """
    with _lock:
        _MEDIA_RESOURCES.add(resource)


def unregister_media_resource(
    resource: Any,
) -> None:
    with _lock:
        _MEDIA_RESOURCES.discard(resource)


def stop_all_media_resources() -> None:
    """
    Stop all registered RTP, SRTP and DTLS-SRTP resources.
    """
    print("[cleanup] Stopping all media resources")

    with _lock:
        resources = list(_MEDIA_RESOURCES)

        _MEDIA_RESOURCES.clear()

    # Stop outside the registry lock. A resource may unregister itself
    # while shutting down.
    for resource in resources:
        try:
            resource.stop()
        except Exception as exc:
            print("[cleanup] Failed stopping media resource: " f"{exc}")


# Existing API retained for backward compatibility.


def register_rtp_sender(
    sender: Any,
) -> None:
    register_media_resource(sender)


def unregister_rtp_sender(
    sender: Any,
) -> None:
    unregister_media_resource(sender)


def stop_all_rtp_senders() -> None:
    stop_all_media_resources()
