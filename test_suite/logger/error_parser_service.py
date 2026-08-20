import os
import re
import types
import logging
import linecache
import sysconfig

from logger.hint_error_service import ErrorHintService
from logger.logger_service import LoggerService

_SYS_PREFIXES = tuple(
    os.path.normcase(os.path.abspath(p)) + os.sep
    for p in {
        sysconfig.get_paths().get(k)
        for k in ("stdlib", "platstdlib", "purelib", "platlib")
    }
    if p
)
_THIS_FILE = os.path.normcase(os.path.abspath(__file__))
_EXCLUDED_BASENAMES = {"method_decorators.py", "error_hints.py"}


def _is_project_frame(filename: str) -> bool:
    if filename.startswith("<"):
        return not filename.startswith("<frozen")
    norm = os.path.normcase(os.path.abspath(filename))
    if norm == _THIS_FILE:
        return False
    if os.path.basename(norm) in _EXCLUDED_BASENAMES:
        return False
    if any(norm.startswith(p) for p in _SYS_PREFIXES):
        return False
    if f"{os.sep}site-packages{os.sep}" in norm:
        return False
    return True


class ErrorParserService:
    """Parses a caught exception into a readable report.

    Usage:
        try:
            ...
        except Exception as e:
            error = ErrorParserService(e, note="loading test config")
            error.pretty_print()   # print the report to the terminal
            error.send_to_log()    # send the report to the shared logfile
    """

    def __init__(
        self,
        e: BaseException,
        note: str | None = None,
        max_repr: int = 200,
        max_items: int = 3,
        show_source_line: bool = True,
        secret_pattern: str = (
            r"pass(word|wd)?|token|secret|api_?key|auth|credential|private_?key"
        ),
    ):
        self._exception = e
        self._note = note
        self.max_repr = max_repr
        self.max_items = max_items
        self.show_source_line = show_source_line
        self.secret_re = re.compile(secret_pattern, re.IGNORECASE)
        self._report: str | None = None

    # ----------------------------------------------------------- public API

    def get_report(self) -> str:
        """Parse the exception (once) and return the report text."""
        if self._report is None:
            try:
                self._report = self._parse()
            except Exception as internal:
                # the parser must never crash the application
                self._report = (
                    f"[ErrorParserService failed: "
                    f"{type(internal).__name__}: {internal}] "
                    f"original error: "
                    f"{type(self._exception).__name__}: {self._exception}"
                )
        return self._report

    def pretty_print(self) -> None:
        """Print the report to the terminal."""
        print(self.get_report())

    def send_to_log(self) -> None:
        """Send the report to the shared logfile via LoggerService."""
        self._log_error(self.get_report())

    @staticmethod
    def _log_error(report: str) -> None:
        logger = logging.getLogger("LoggerService")
        logger.error(report)

    # ------------------------------------------------------------- parsing

    def _parse(self) -> str:
        e = self._exception
        lines = [f"\n--- ❌ EXCEPTION: {type(e).__name__}: {e} ---"]
        if self._note:
            lines.append(f"note: {self._note}")

        frames = self._collect_project_frames(e)

        hint = ErrorHintService().build(e, frames)
        if hint:
            lines.append(f"💡 hint: {hint[0]}")
            lines.extend(f"         {h}" for h in hint[1:])

        if frames:
            lines.append("project frames (from caller to point of failure):")
            for depth, (frame, lineno) in enumerate(frames):
                lines.extend(self._format_frame(frame, lineno, depth, e))
        else:
            lines.append(
                "ℹ️ no project frames — the error is entirely inside a library"
            )

        lines.extend(self._format_cause_chain(e))
        lines.append("--- END EXCEPTION ---")
        return "\n".join(lines)

    @staticmethod
    def _collect_project_frames(e: BaseException) -> list:
        frames = []
        tb = e.__traceback__
        while tb is not None:
            if _is_project_frame(tb.tb_frame.f_code.co_filename):
                frames.append((tb.tb_frame, tb.tb_lineno))
            tb = tb.tb_next
        return frames

    @staticmethod
    def _dev_mode_active() -> bool:
        """True when LoggerService was started with dev_mode: true in launch_config."""
        instance = LoggerService._instance
        return bool(instance) and bool(getattr(instance, "dev_mode", False))

    def _format_frame(self, frame, lineno: int, depth: int, exc: BaseException) -> list:
        code = frame.f_code
        indent = "  " * depth
        qualname = getattr(code, "co_qualname", code.co_name)

        if self._dev_mode_active():
            # Dev/debug mode: classic Python traceback syntax so PyCharm's
            # built-in hyperlink filter turns "line N" into a clickable link
            # straight to the source. Full path is intentional - PyCharm
            # needs it to resolve the file unambiguously.
            lines = [
                f'{indent}→ File "{code.co_filename}", line {lineno}, in {qualname}'
            ]
        else:
            # Normal mode: unchanged - short, readable, non-clickable.
            filename = (
                os.path.basename(code.co_filename)
                if not code.co_filename.startswith("<")
                else code.co_filename
            )
            lines = [f"{indent}→ {qualname}()  {filename}:{lineno}"]

        if self.show_source_line:
            source = linecache.getline(code.co_filename, lineno).strip()
            if source:
                lines.append(f"{indent}    {source}")

        shown = [
            (name, value)
            for name, value in frame.f_locals.items()
            if self._is_worth_showing(name, value) and value is not exc
        ]
        if shown:
            lines.append(f"{indent}  locals:")
            for name, value in shown:
                lines.append(f"{indent}    {name} = {self._render_value(name, value)}")
        return lines

    @staticmethod
    def _format_cause_chain(e: BaseException) -> list:
        lines = []
        seen = {id(e)}
        current = e
        while True:
            cause = current.__cause__ or (
                None if current.__suppress_context__ else current.__context__
            )
            if cause is None or id(cause) in seen:
                break
            seen.add(id(cause))
            lines.append(f"caused by: {type(cause).__name__}: {cause}")
            current = cause
        return lines

    # ------------------------------------------------------------ rendering

    @staticmethod
    def _is_worth_showing(name: str, value) -> bool:
        """Drop infrastructure: dunders, comprehension artifacts, imports, self."""
        if name.startswith("__") or not name.isidentifier():
            return False
        if isinstance(
            value,
            (
                types.ModuleType,
                types.FunctionType,
                types.BuiltinFunctionType,
                types.MethodType,
                type,
            ),
        ):
            return False
        if isinstance(value, ErrorParserService):
            return False
        return True

    def _render_value(self, name: str, value) -> str:
        if self.secret_re.search(name):
            return "***masked***"
        try:
            if isinstance(value, str):
                if len(value) > self.max_repr:
                    return repr(value[: self.max_repr]) + f"… (length {len(value)})"
                return repr(value)

            if isinstance(value, dict):
                items = list(value.items())[: self.max_items]
                body = ", ".join(
                    f"{self._clip(self._safe_repr(k), 40)}: "
                    f"{self._clip(self._safe_repr(v), 60)}"
                    for k, v in items
                )
                extra = (
                    f", … {len(value) - self.max_items} more"
                    if len(value) > self.max_items
                    else ""
                )
                return f"dict(len={len(value)}) {{{body}{extra}}}"

            if isinstance(value, (list, tuple, set, frozenset)):
                items = list(value)[: self.max_items]
                body = ", ".join(self._clip(self._safe_repr(i), 60) for i in items)
                extra = (
                    f", … {len(value) - self.max_items} more"
                    if len(value) > self.max_items
                    else ""
                )
                return f"{type(value).__name__}(len={len(value)}) [{body}{extra}]"

            return self._clip(self._safe_repr(value), self.max_repr)
        except Exception:
            return f"<failed to render {type(value).__name__}>"

    @staticmethod
    def _safe_repr(value) -> str:
        try:
            return repr(value)
        except Exception as e:
            return f"<{type(value).__name__}: repr failed ({type(e).__name__})>"

    @staticmethod
    def _clip(text: str, limit: int) -> str:
        return text if len(text) <= limit else text[: limit - 1] + "…"
