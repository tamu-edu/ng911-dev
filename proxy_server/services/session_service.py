import threading
from typing import Dict

from proxy_server.state.session_state import SessionState
from proxy_server.state.enums import State
from proxy_server.models.session_models import StartSessionRequest

from proxy_server.services.capture_service import CaptureService
from proxy_server.services.proxy_worker_manager import ProxyWorkerManager
from proxy_server.services.fsh_service import FSHService


class SessionService:
    def __init__(self, state: SessionState):
        self._state = state

        self._capture_service: CaptureService | None = None
        self._proxy_manager: ProxyWorkerManager | None = None
        self._fsh_service: FSHService | None = None
        self._console_capture = None

    # =========================
    # START
    # =========================

    def start_session(self, request: StartSessionRequest) -> None:
        self._state.start(
            session_id=request.session_id,
            config=request.config.model_dump(),
        )

        threading.Thread(
            target=self._start_flow,
            args=(request,),
            daemon=True,
        ).start()

    def _start_flow(self, request: StartSessionRequest) -> None:
        try:
            session_id = request.session_id
            config = request.config

            from proxy_server.services.console_capture_service import (
                ConsoleCaptureService,
            )

            self._console_capture = ConsoleCaptureService(session_id)
            self._console_capture.start()

            # 1. Setup FSH
            self._fsh_service = FSHService(config.network, config.proxy.host_ip)
            self._fsh_service.apply_rules(config.conduits)

            # 2. Start capture
            self._capture_service = CaptureService(session_id)
            self._capture_service.start(conduits=config.conduits)

            # 3. Start proxy workers
            keylog_file = self._capture_service.get_keylog_path()

            self._proxy_manager = ProxyWorkerManager(keylog_file, config.proxy.host_ip)
            self._proxy_manager.start(config.conduits)

            self._state.mark_running(session_id)

            print(f"[MS] ✅ Session {session_id} started")

        except Exception as e:
            print(f"[MS] ❌ start flow failed: {e}")
            self.cleanup()
            self._state.abort_start(session_id)

    # =========================
    # STATUS
    # =========================

    def get_status(self, session_id: str) -> Dict:
        self._state.validate_session(session_id)

        state = self._state.get_state()

        response = {
            "status": state.value,
        }

        if state == State.RETRIEVE_READY:
            response["artifacts"] = self._state.get_artifacts()

        return response

    # =========================
    # STOP
    # =========================

    def stop_session(self, session_id: str) -> None:
        self._state.mark_stopping(session_id)

        threading.Thread(
            target=self._stop_flow,
            args=(session_id,),
            daemon=True,
        ).start()

    def _stop_flow(self, session_id: str) -> None:
        try:
            self._state.validate_session(session_id)

            # 1. Stop proxy
            if self._proxy_manager:
                self._proxy_manager.stop()

            print("[MS] Proxy worker shutdown completed")

            # 2. Stop capture
            if self._capture_service:
                self._capture_service.stop()

            # 3. Prepare artifacts
            artifacts = {}
            if self._capture_service:
                artifacts = self._capture_service.get_artifacts()

            # 4. Move state
            self._state.mark_retrieve_ready(session_id, artifacts)

            print(f"[MS] ✅ Session {session_id} stopped")

        except Exception as e:
            print(f"[MS] ❌ stop flow failed: {e}")

    # =========================
    # RESET
    # =========================

    def reset_session(self, session_id: str) -> None:
        self._state.mark_resetting(session_id)

        threading.Thread(
            target=self._reset_flow,
            args=(session_id,),
            daemon=True,
        ).start()

    def cleanup(self) -> None:
        """
        Best-effort cleanup of all active session resources.

        Intended for Management Server shutdown, interruption,
        or unexpected process-level termination.
        """
        print("[MS] Cleaning up active session resources...")

        if self._proxy_manager:
            try:
                self._proxy_manager.cleanup()
            except Exception as e:
                print(f"[MS] ⚠️ Proxy cleanup failed: {e}")
            finally:
                self._proxy_manager = None

        if self._fsh_service:
            try:
                self._fsh_service.cleanup()
            except Exception as e:
                print(f"[MS] ⚠️ FSH cleanup failed: {e}")
            finally:
                self._fsh_service = None

        if self._capture_service:
            try:
                self._capture_service.cleanup()
            except Exception as e:
                print(f"[MS] ⚠️ Capture cleanup failed: {e}")
            finally:
                self._capture_service = None

        if self._console_capture:
            try:
                self._console_capture.stop()
            except Exception as e:
                print(f"[MS] ⚠️ Console capture cleanup failed: {e}")
            finally:
                self._console_capture = None

        print("[MS] ✅ Active session resources cleaned up")

    def _reset_flow(self, session_id: str) -> None:
        try:
            self._state.validate_session(session_id)

            # 1. Cleanup proxy
            if self._proxy_manager:
                self._proxy_manager.cleanup()
                self._proxy_manager = None

            # 2. Cleanup FSH
            if self._fsh_service:
                self._fsh_service.cleanup()
                self._fsh_service = None

            # 3. Cleanup capture
            if self._capture_service:
                self._capture_service.cleanup()
                self._capture_service = None

            # 4. Reset state
            self._state.mark_ready(session_id)

            print(f"[MS] ✅ Session {session_id} reset complete")

            if self._console_capture:
                self._console_capture.stop()
                self._console_capture = None

        except Exception as e:
            print(f"[MS] ❌ reset flow failed: {e}")
