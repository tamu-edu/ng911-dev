import threading


class BaseProxyWorker:
    """
    Base class for all proxy workers.

    Defines:
    - lifecycle (start/stop)
    - running flag
    - stop signaling
    """

    def __init__(self):
        self._running = False
        self._lock = threading.Lock()

    # =========================
    # LIFECYCLE
    # =========================

    def start(self) -> None:
        """
        Entry point for worker thread.

        Must be overridden.
        """
        raise NotImplementedError

    def stop(self) -> None:
        """
        Signals worker to stop.
        """
        with self._lock:
            self._running = False

        self._on_stop()

    # =========================
    # INTERNAL
    # =========================

    def _set_running(self) -> None:
        with self._lock:
            self._running = True

    def _is_running(self) -> bool:
        with self._lock:
            return self._running

    def _on_stop(self) -> None:
        """
        Optional hook for subclasses.

        Used to:
        - close sockets
        - release resources
        """
        pass
