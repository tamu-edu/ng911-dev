import traceback

from services.stub_server.sip_service.rtp_registry import stop_all_rtp_senders
from services.stub_server.stub_server_service import StubServerService
from services.cleanup_registry import run_cleanup, register_cleanup

register_cleanup("Stop all RTP audio/text senders", stop_all_rtp_senders)
register_cleanup("Stop all StubServerService instances", StubServerService.stop_all)

_SHUTDOWN_ALREADY_RUN = False
_TS_SHUTDOWN = True
_PS_SHUTDOWN = False


def graceful_shutdown(reason: str = "", exc: Exception | None = None) -> None:
    """
    Gracefully shuts down Test Suite execution.
    This function is safe to call multiple times; cleanup hooks run only once.
    """
    global _SHUTDOWN_ALREADY_RUN
    if _SHUTDOWN_ALREADY_RUN:
        return
    _SHUTDOWN_ALREADY_RUN = True

    try:
        print("\n[!] Graceful shutdown initiated")
        if reason:
            print(f"[!] Reason: {reason}")

        if exc is not None:
            print("[!] Unhandled exception (traceback):")
            traceback.print_exception(type(exc), exc, exc.__traceback__)

        # Execute registered cleanup hooks
        run_cleanup()

        print("[+] Cleanup completed")

        if reason:
            print(f"[!] Reason: {reason}")

        print("[!] Please Contact Dev team in cause of Error")

    except Exception as cleanup_exc:
        # Must never raise from shutdown
        print("[!] ERROR during graceful shutdown (ignored):", cleanup_exc)
