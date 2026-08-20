from __future__ import annotations

import re
from typing import Any

from services.messages.errors.message_service_error import MessageServiceError

_HEX_COLON_RE = re.compile(r"^([0-9a-fA-F]{2}:)*[0-9a-fA-F]{2}$")


def get_field_values(layer: Any, field_name: str) -> list[str]:
    """
    :param layer: pyshark layer (e.g. packet.sip)
    :param field_name: sanitized field name
    :return: all raw string values for this field, empty list if absent
    """
    if not hasattr(layer, field_name):
        return []
    container = getattr(layer, field_name)
    occurrences = getattr(container, "all_fields", None)
    if occurrences:
        return [_field_str(o) for o in occurrences]
    return [_field_str(container)]


def get_field_value(layer: Any, field_name: str) -> str | None:
    """
    :param layer: pyshark layer (e.g. packet.sip)
    :param field_name: sanitized field name
    :return: raw string value, or None if absent
    :raises MessageServiceError: field occurs more than once (expected at most once per RFC)
    """
    values = get_field_values(layer, field_name)
    if len(values) > 1:
        raise MessageServiceError(
            f"Header '{field_name}' expected once per RFC, got {len(values)} occurrences.",
            errors=[
                f"layer: {getattr(layer, 'layer_name', layer.__class__.__name__)}",
                f"field: {field_name}",
                f"occurrences: {values}",
            ],
        )
    return values[0] if values else None


def ensure_present(
    value: str | None, *, packet_number: int, layer_name: str, field_name: str
) -> str:
    """
    :raises MessageServiceError: value is None or empty
    """
    if value is None or value == "":
        raise MessageServiceError(
            f"Required header '{field_name}' is missing from {layer_name} message.",
            errors=[
                f"packet_number: {packet_number}",
                f"layer: {layer_name}",
                f"field: {field_name}",
                "reason: attribute not present on parsed pyshark packet",
            ],
        )
    return value


def require_non_empty_list(
    items: list, *, packet_number: int, layer_name: str, field_name: str
) -> list:
    """
    :raises MessageServiceError: items is empty
    """
    if not items:
        raise MessageServiceError(
            f"Required header '{field_name}' is missing from {layer_name} message "
            f"(expected at least one occurrence).",
            errors=[
                f"packet_number: {packet_number}",
                f"layer: {layer_name}",
                f"field: {field_name}",
                "reason: zero occurrences found on parsed pyshark packet",
            ],
        )
    return items


def list_or_none(items: list) -> list | None:
    """Repeatable-header convention: list if there's 1+ occurrence, None if none."""
    return list(items) if items else None


def parse_int_or_raise(
    value: str | None, *, packet_number: int, layer_name: str, field_name: str
) -> int:
    """
    :raises MessageServiceError: value is not a valid integer
    """
    try:
        return int(value)  # type: ignore[arg-type]  # None handled below
    except (TypeError, ValueError) as exc:
        raise MessageServiceError(
            f"Header '{field_name}' in {layer_name} message is not a valid integer.",
            errors=[
                f"packet_number: {packet_number}",
                f"layer: {layer_name}",
                f"field: {field_name}",
                f"raw_value: {value!r}",
                f"underlying_exception: {exc!r}",
            ],
        ) from exc


def get_body_value(layer: Any, field_name: str) -> str:
    """
    Like get_field_value, but for message-body fields specifically
    (SIP msg_body / HTTP file_data).

    :param layer: pyshark layer (e.g. packet.sip / packet.http)
    :param field_name: "msg_body" or "file_data"
    :return: decoded body text, or "" if absent
    """
    raw = get_field_value(layer, field_name)
    if not raw:
        return ""
    if _HEX_COLON_RE.match(raw):
        try:
            return bytes.fromhex(raw.replace(":", "")).decode("utf-8", errors="ignore")
        except ValueError:
            return raw
    return raw


def parse_params(raw: str) -> dict[str, str]:
    """Parses ';key=value' parameters shared by SIP and HTTP header values."""
    params: dict[str, str] = {}
    for part in raw.split(";")[1:]:
        part = part.strip()
        if not part:
            continue
        key, _, value = part.partition("=")
        params[key.strip().lower()] = value.strip()
    return params


# Internal helper for the public helpers above (get_field_value/get_field_values
# only) - not meant to be imported or called from outside this file.
def _field_str(field_like: Any) -> str:
    # pyshark quirk: .showname_value on a bare LayerField is sometimes None
    # even when the field has a value (e.g. Content-Length) - .show is the
    # reliable one. Never bare str(obj): that returns a debug repr, not the value.
    for attr in ("show", "showname_value"):
        value = getattr(field_like, attr, None)
        if value is not None:
            return str(value)
    return str(field_like)
