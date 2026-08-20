import re
import types
import difflib
import linecache

_SUBSCRIPT_RE = re.compile(r"([A-Za-z_]\w*)\s*\[([^\[\]]+)\]")
_INT_LITERAL_RE = re.compile(r"invalid literal for int\(\) with base (\d+): (.+)$")
_FLOAT_LITERAL_RE = re.compile(r"could not convert string to float: (.+)$")
_UNPACK_MANY_RE = re.compile(r"too many values to unpack \(expected (\d+)\)")
_UNPACK_FEW_RE = re.compile(
    r"not enough values to unpack \(expected (\d+), got (\d+)\)"
)
_NOT_IN_LIST_RE = re.compile(r"^(.+) is not in list$")


class ErrorHintService:
    """Builds a short human hint explaining the likely cause of an exception."""

    @classmethod
    def build(cls, e: BaseException, frames: list) -> list | None:
        """Return hint lines for the exception, or None if nothing useful."""
        local_vars = frames[-1][0].f_locals if frames else {}

        if isinstance(e, KeyError):
            return cls._key_error(e, local_vars)
        if isinstance(e, AttributeError):
            return cls._attribute_error(e, local_vars)
        if isinstance(e, IndexError):
            return cls._index_error(frames)
        if isinstance(e, ValueError):
            return cls._value_error(e, local_vars)
        return None

    # ------------------------------------------------------------ per type

    @classmethod
    def _key_error(cls, e: KeyError, local_vars: dict) -> list | None:
        if not e.args:
            return None
        key = e.args[0]
        missing = [
            (name, value)
            for name, value in local_vars.items()
            if isinstance(value, dict)
            and cls._is_plain_value(name, value)
            and key not in value
        ]
        if not missing:
            return [f"key {key!r} not found in any local dict"]

        name, data = missing[0]
        lines = [f"key {key!r} not found in '{name}'"]

        mismatch = next((k for k in data if k != key and str(k) == str(key)), None)
        if mismatch is not None:
            lines.append(
                f"type mismatch: dict has key {mismatch!r} "
                f"({type(mismatch).__name__}), you asked for {key!r} "
                f"({type(key).__name__})"
            )
        else:
            close = difflib.get_close_matches(
                str(key), [str(k) for k in data], n=3, cutoff=0.6
            )
            if close:
                lines.append(f"did you mean: {', '.join(repr(c) for c in close)}?")

        if isinstance(key, str):
            case_match = next(
                (
                    k
                    for k in data
                    if isinstance(k, str) and k.lower() == key.lower() and k != key
                ),
                None,
            )
            if case_match:
                lines.append(f"case mismatch: dict has {case_match!r}")

        preview = ", ".join(cls._clip(cls._safe_repr(k), 30) for k in list(data)[:8])
        more = f", … {len(data) - 8} more" if len(data) > 8 else ""
        lines.append(f"available keys: {preview}{more}")
        return lines

    @classmethod
    def _attribute_error(cls, e: AttributeError, local_vars: dict) -> list | None:
        name = getattr(e, "name", None)
        if name is None:
            return None
        obj = getattr(e, "obj", None)

        if obj is None:
            return [
                f"'.{name}' accessed on None — something above returned None",
                "typical culprits: dict.get() miss, re.match() miss, "
                "a function without an explicit return",
            ]

        owner = next(
            (
                n
                for n, v in local_vars.items()
                if v is obj and cls._is_plain_value(n, v)
            ),
            None,
        )
        who = (
            f"'{owner}' ({type(obj).__name__})"
            if owner
            else f"object of type {type(obj).__name__}"
        )
        lines = [f"{who} has no attribute '{name}'"]

        if isinstance(obj, dict) and name in obj:
            ref = owner or "obj"
            lines.append(f"it's a dict — use {ref}[{name!r}] instead of {ref}.{name}")
            return lines

        attrs = [a for a in dir(obj) if not a.startswith("_")]
        close = difflib.get_close_matches(name, attrs, n=3, cutoff=0.6)
        if close:
            lines.append(f"did you mean: {', '.join('.' + c for c in close)}?")
        elif attrs:
            lines.append(f"available: {', '.join(attrs[:10])}")
        return lines

    @classmethod
    def _index_error(cls, frames: list) -> list | None:
        if not frames:
            return None
        frame, lineno = frames[-1]
        local_vars = frame.f_locals
        sequences = {
            name: value
            for name, value in local_vars.items()
            if isinstance(value, (list, tuple)) and cls._is_plain_value(name, value)
        }

        lines = []
        source = linecache.getline(frame.f_code.co_filename, lineno)
        for match in _SUBSCRIPT_RE.finditer(source):
            base, index_expr = match.group(1), match.group(2).strip()
            if base not in sequences:
                continue
            sequence = sequences[base]
            index = cls._resolve_index(index_expr, local_vars)
            valid = (
                f"0..{len(sequence) - 1} (or -{len(sequence)}..-1)"
                if sequence
                else "none — it's empty"
            )
            if index is not None:
                lines.append(
                    f"tried {base}[{index}], but len({base}) = {len(sequence)}; "
                    f"valid: {valid}"
                )
            else:
                lines.append(f"len({base}) = {len(sequence)}; valid indices: {valid}")
            if not sequence:
                lines.append(
                    f"'{base}' is empty — check where it should have been filled"
                )
            elif index == len(sequence):
                lines.append(
                    "off-by-one: the last element is at len-1 — "
                    f"use {base}[-1] or range(len({base}))"
                )
            break

        if not lines and sequences:
            lines.append(
                "index out of range; sequences in scope: "
                + ", ".join(f"{n} (len={len(v)})" for n, v in sequences.items())
            )
        return lines or None

    @classmethod
    def _value_error(cls, e: ValueError, local_vars: dict) -> list | None:
        message = str(e)

        match = _INT_LITERAL_RE.search(message) or _FLOAT_LITERAL_RE.search(message)
        if match and match.lastindex:
            raw = match.group(match.lastindex)
            value = (
                raw[1:-1]
                if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "'\""
                else raw
            )
            lines = [f"cannot parse {raw} as a number"]
            if value == "":
                lines.append("it's an empty string — check the data source")
            elif value != value.strip():
                lines.append(
                    f"whitespace around the value — "
                    f"try int({value.strip()!r}) after .strip()"
                )
            elif "," in value:
                lines.append(
                    "comma as decimal separator — try value.replace(',', '.') first"
                )
            elif "int()" in message:
                try:
                    float(value)
                    lines.append(
                        f"it's a float string — use int(float({value!r})) or round()"
                    )
                except ValueError:
                    pass
            owner = next(
                (n for n, v in local_vars.items() if v == value and isinstance(v, str)),
                None,
            )
            if owner:
                lines.append(f"the value came from '{owner}'")
            return lines

        match = _UNPACK_MANY_RE.search(message)
        if match:
            expected = int(match.group(1))
            lines = [f"unpacking expected {expected} values but got more"]
            candidates = [
                f"{n} (len={len(v)}) = {cls._clip(cls._safe_repr(v), 60)}"
                for n, v in local_vars.items()
                if isinstance(v, (list, tuple))
                and len(v) > expected
                and cls._is_plain_value(n, v)
            ]
            if candidates:
                lines.append("oversized candidates: " + "; ".join(candidates[:3]))
            lines.append("consider: a, b, *rest = … to absorb the extras")
            return lines

        match = _UNPACK_FEW_RE.search(message)
        if match:
            expected, got = int(match.group(1)), int(match.group(2))
            lines = [f"unpacking expected {expected} values, got only {got}"]
            candidates = [
                f"{n} (len={len(v)}) = {cls._clip(cls._safe_repr(v), 60)}"
                for n, v in local_vars.items()
                if isinstance(v, (list, tuple))
                and len(v) == got
                and cls._is_plain_value(n, v)
            ]
            if candidates:
                lines.append("undersized candidates: " + "; ".join(candidates[:3]))
            return lines

        match = _NOT_IN_LIST_RE.match(message)
        if match:
            needle = match.group(1)
            lines = [f"{needle} is not in the list (from list.index())"]
            for name, value in local_vars.items():
                if isinstance(value, list) and cls._is_plain_value(name, value):
                    close = difflib.get_close_matches(
                        needle.strip("'\""), [str(i) for i in value], n=3, cutoff=0.6
                    )
                    if close:
                        lines.append(
                            f"in '{name}' did you mean: "
                            f"{', '.join(repr(c) for c in close)}?"
                        )
                        break
            lines.append("tip: guard with `if x in lst:` or use a try/except")
            return lines

        if "substring not found" in message:
            return [
                "str.index() miss — use str.find() (returns -1) "
                "or check with `in` first"
            ]

        return None

    # -------------------------------------------------------------- helpers

    @staticmethod
    def _is_plain_value(name: str, value) -> bool:
        """Keep only real data: skip dunders, imports, functions, classes."""
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
        return True

    @staticmethod
    def _resolve_index(expr: str, local_vars: dict) -> int | None:
        """Resolve a subscript expression to an int: literal or simple local name."""
        try:
            return int(expr)
        except ValueError:
            pass
        negative = expr.startswith("-")
        name = expr[1:].strip() if negative else expr
        if name.isidentifier() and isinstance(local_vars.get(name), int):
            return -local_vars[name] if negative else local_vars[name]
        return None

    @staticmethod
    def _safe_repr(value) -> str:
        try:
            return repr(value)
        except Exception as e:
            return f"<{type(value).__name__}: repr failed ({type(e).__name__})>"

    @staticmethod
    def _clip(text: str, limit: int) -> str:
        return text if len(text) <= limit else text[: limit - 1] + "…"
