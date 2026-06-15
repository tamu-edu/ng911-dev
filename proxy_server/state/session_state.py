import threading
from typing import Optional, Dict, Any

from .enums import State


class SessionState:
    """
    Central FSM holder.

    Guarantees:
    - single active session
    - strict state transitions
    - thread-safe access
    """

    def __init__(self):
        self._lock = threading.Lock()

        self._state: State = State.READY
        self._session_id: Optional[str] = None
        self._config: Optional[Dict[str, Any]] = None
        self._artifacts: Optional[Dict[str, str]] = None

    # =========================
    # Basic getters
    # =========================

    def get_state(self) -> State:
        with self._lock:
            return self._state

    def get_session_id(self) -> Optional[str]:
        with self._lock:
            return self._session_id

    def get_artifacts(self) -> Optional[Dict[str, str]]:
        with self._lock:
            return self._artifacts

    # =========================
    # Session validation
    # =========================

    def validate_session(self, session_id: str) -> None:
        with self._lock:
            if self._state == State.READY:
                raise ValueError("No active session")

            if self._session_id != session_id:
                raise PermissionError("Invalid session_id")

    # =========================
    # State transitions
    # =========================

    def start(self, session_id: str, config: Dict[str, Any]) -> None:
        with self._lock:
            if self._state != State.READY:
                raise RuntimeError("Session already active")

            self._session_id = session_id
            self._config = config
            self._artifacts = None

            self._state = State.RUNNING

    def mark_stopping(self, session_id: str) -> None:
        with self._lock:
            self._validate_active(session_id)

            if self._state != State.RUNNING:
                # idempotent behavior
                return

            self._state = State.STOPPING

    def mark_retrieve_ready(self, session_id: str, artifacts: Dict[str, str]) -> None:
        with self._lock:
            self._validate_active(session_id)

            if self._state != State.STOPPING:
                raise RuntimeError("Invalid transition to RETRIEVE_READY")

            self._artifacts = artifacts
            self._state = State.RETRIEVE_READY

    def mark_resetting(self, session_id: str) -> None:
        with self._lock:
            self._validate_active(session_id)

            if self._state != State.RETRIEVE_READY:
                raise RuntimeError("Invalid transition to RESETTING")

            self._state = State.RESETTING

    def mark_ready(self, session_id: str) -> None:
        with self._lock:
            self._validate_active(session_id)

            if self._state != State.RESETTING:
                raise RuntimeError("Invalid transition to READY")

            self._session_id = None
            self._config = None
            self._artifacts = None

            self._state = State.READY

    # =========================
    # Helpers
    # =========================

    def _validate_active(self, session_id: str) -> None:
        if self._state == State.READY:
            raise ValueError("No active session")

        if self._session_id != session_id:
            raise PermissionError("Invalid session_id")
