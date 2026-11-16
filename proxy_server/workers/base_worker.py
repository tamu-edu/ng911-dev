import threading

EGRESS_PORT_OFFSET = 300


class BaseProxyWorker:
    """
    Base class for all proxy workers.
    """

    def __init__(self):
        self._running = False
        self._lock = threading.Lock()

        self._ready_event = threading.Event()
        self._startup_error: Exception | None = None

    def start(self) -> None:
        raise NotImplementedError

    def stop(self) -> None:
        with self._lock:
            self._running = False

        self._on_stop()

    def wait_until_ready(self, timeout: float) -> bool:
        return self._ready_event.wait(timeout)

    def wait_until_stopped(self, timeout: float) -> bool:
        """
        Wait until worker-owned asynchronous resources have stopped.

        Workers that do not create child threads are considered stopped
        once stop() has completed.
        """
        return True

    @property
    def startup_error(self) -> Exception | None:
        return self._startup_error

    def _set_running(self) -> None:
        with self._lock:
            self._running = True

    def _set_ready(self) -> None:
        self._ready_event.set()

    def _set_startup_error(self, error: Exception) -> None:
        self._startup_error = error
        self._ready_event.set()

    def _is_running(self) -> bool:
        with self._lock:
            return self._running

    def _on_stop(self) -> None:
        pass

    @staticmethod
    def _get_egress_port(bind_port: int) -> int:
        return bind_port + EGRESS_PORT_OFFSET
