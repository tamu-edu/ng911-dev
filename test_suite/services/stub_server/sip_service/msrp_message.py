from __future__ import annotations

import secrets
from dataclasses import dataclass, field

CRLF = b"\r\n"
END_PREFIX = b"-------"

CONTINUATION_COMPLETE = "$"
CONTINUATION_MORE = "+"
CONTINUATION_ABORT = "#"

CONTINUATION_FLAGS = (
    CONTINUATION_COMPLETE,
    CONTINUATION_MORE,
    CONTINUATION_ABORT,
)


@dataclass
class MSRPMessage:
    """
    Parsed MSRP request or response.

    MSRP is a stream protocol. Framing is based on the transaction ID
    carried by the start line and repeated in the terminating end-line.
    """

    transaction_id: str

    method: str | None = None

    status_code: int | None = None
    comment: str = ""

    headers: dict[str, str] = field(default_factory=dict)

    body: bytes = b""

    continuation: str = CONTINUATION_COMPLETE

    @property
    def is_request(self) -> bool:
        return self.method is not None

    @property
    def is_response(self) -> bool:
        return self.status_code is not None

    def header(
        self,
        name: str,
        default: str = "",
    ) -> str:
        return self.headers.get(
            name.lower(),
            default,
        )

    def body_text(
        self,
        encoding: str = "utf-8",
    ) -> str:
        return self.body.decode(
            encoding,
            errors="replace",
        )


def generate_transaction_id() -> str:
    """
    Generate an MSRP transaction ID.

    RFC 4975 requires at least 64 bits of randomness.
    """

    return secrets.token_hex(8)


def generate_message_id() -> str:
    """
    Generate an MSRP Message-ID with sufficient uniqueness
    for TestSuite runtime usage.
    """

    return secrets.token_hex(12)


def _generate_safe_transaction_id(
    body: bytes,
) -> str:
    """
    Generate a transaction ID whose MSRP end-line cannot collide
    with message content.
    """

    while True:
        transaction_id = generate_transaction_id()

        marker = END_PREFIX + transaction_id.encode("ascii")

        if all(
            marker + flag.encode("ascii") not in body for flag in CONTINUATION_FLAGS
        ):
            return transaction_id


def build_send_request(
    *,
    to_path: str,
    from_path: str,
    text: str,
    content_type: str = "text/plain",
    transaction_id: str | None = None,
    message_id: str | None = None,
) -> bytes:
    """
    Build one complete MSRP SEND request.

    The current implementation sends the supplied text as one complete
    MSRP chunk using the '$' continuation flag.
    """

    body = (text or "").encode("utf-8")

    transaction_id = transaction_id or _generate_safe_transaction_id(body)

    message_id = message_id or generate_message_id()

    body_length = len(body)

    byte_range = f"1-{body_length}/{body_length}" if body_length else "1-0/0"

    start_line = (f"MSRP {transaction_id} SEND").encode("utf-8")

    headers = [
        f"To-Path: {to_path}".encode("utf-8"),
        f"From-Path: {from_path}".encode("utf-8"),
        f"Message-ID: {message_id}".encode("utf-8"),
        f"Byte-Range: {byte_range}".encode("ascii"),
        f"Content-Type: {content_type}".encode("utf-8"),
    ]

    end_line = (
        END_PREFIX
        + transaction_id.encode("ascii")
        + CONTINUATION_COMPLETE.encode("ascii")
        + CRLF
    )

    return start_line + CRLF + CRLF.join(headers) + CRLF + CRLF + body + CRLF + end_line


def build_response(
    request: MSRPMessage,
    status_code: int = 200,
    comment: str = "OK",
) -> bytes:
    """
    Build an MSRP response for an incoming request.

    For endpoint-to-endpoint SEND handling:
    - response To-Path uses the request From-Path;
    - response From-Path uses the request To-Path;
    - transaction ID is preserved.
    """

    request_from_path = request.header("from-path")
    request_to_path = request.header("to-path")

    if not request_from_path:
        raise ValueError("Cannot build MSRP response: request From-Path is missing")

    if not request_to_path:
        raise ValueError("Cannot build MSRP response: request To-Path is missing")

    response_to_path = request_from_path.split()[0]

    response_from_path = request_to_path.split()[0]

    start_line = (
        f"MSRP {request.transaction_id} "
        f"{int(status_code):03d}" + (f" {comment}" if comment else "")
    ).encode("utf-8")

    headers = [
        f"To-Path: {response_to_path}".encode("utf-8"),
        f"From-Path: {response_from_path}".encode("utf-8"),
    ]

    end_line = (
        END_PREFIX
        + request.transaction_id.encode("ascii")
        + CONTINUATION_COMPLETE.encode("ascii")
        + CRLF
    )

    return start_line + CRLF + CRLF.join(headers) + CRLF + end_line


def extract_msrp_message(
    buffer: bytes,
) -> tuple[MSRPMessage | None, bytes]:
    """
    Extract one complete MSRP frame from a TCP stream buffer.

    Returns:

        (None, original_buffer)

    when the frame is incomplete.

    Otherwise returns:

        (parsed_message, remaining_buffer)
    """

    if not buffer:
        return None, buffer

    first_line_end = buffer.find(CRLF)

    if first_line_end < 0:
        return None, buffer

    first_line = buffer[:first_line_end].decode(
        "utf-8",
        errors="strict",
    )

    parts = first_line.split(" ", 3)

    if len(parts) < 3 or parts[0] != "MSRP":
        raise ValueError(f"Invalid MSRP start line: {first_line!r}")

    transaction_id = parts[1]

    marker_prefix = CRLF + END_PREFIX + transaction_id.encode("ascii")

    candidates: list[tuple[int, int]] = []

    for flag in CONTINUATION_FLAGS:
        marker = marker_prefix + flag.encode("ascii") + CRLF

        position = buffer.find(
            marker,
            first_line_end,
        )

        if position >= 0:
            candidates.append(
                (
                    position,
                    position + len(marker),
                )
            )

    if not candidates:
        return None, buffer

    _, frame_end = min(
        candidates,
        key=lambda item: item[0],
    )

    frame = buffer[:frame_end]
    remaining = buffer[frame_end:]

    return (
        parse_msrp_message(frame),
        remaining,
    )


def parse_msrp_message(
    frame: bytes,
) -> MSRPMessage:
    """
    Parse one complete MSRP frame.
    """

    first_line_end = frame.find(CRLF)

    if first_line_end < 0:
        raise ValueError("MSRP frame has no complete start line")

    first_line = frame[:first_line_end].decode(
        "utf-8",
        errors="strict",
    )

    parts = first_line.split(" ", 3)

    if len(parts) < 3 or parts[0] != "MSRP":
        raise ValueError(f"Invalid MSRP start line: {first_line!r}")

    transaction_id = parts[1]
    third_token = parts[2]

    method: str | None = None
    status_code: int | None = None
    comment = ""

    if len(third_token) == 3 and third_token.isdigit():
        status_code = int(third_token)

        if len(parts) == 4:
            comment = parts[3]
    else:
        method = third_token

    continuation = None
    marker_start = None

    for flag in CONTINUATION_FLAGS:
        suffix = (
            END_PREFIX + transaction_id.encode("ascii") + flag.encode("ascii") + CRLF
        )

        if frame.endswith(suffix):
            continuation = flag
            marker_start = len(frame) - len(suffix)
            break

    if continuation is None or marker_start is None:
        raise ValueError("MSRP frame does not contain a valid matching end-line")

    payload_section = frame[first_line_end + len(CRLF) : marker_start]

    headers_blob: bytes
    body = b""

    separator = CRLF + CRLF

    if separator in payload_section:
        headers_blob, body_with_framing = payload_section.split(
            separator,
            1,
        )

        if not body_with_framing.endswith(CRLF):
            raise ValueError("MSRP body is not followed by the required framing CRLF")

        body = body_with_framing[: -len(CRLF)]

    else:
        headers_blob = payload_section

        if headers_blob.endswith(CRLF):
            headers_blob = headers_blob[: -len(CRLF)]

    headers: dict[str, str] = {}

    if headers_blob:
        for raw_header in headers_blob.split(CRLF):
            try:
                name_raw, value_raw = raw_header.split(
                    b":",
                    1,
                )
            except ValueError as exc:
                raise ValueError(f"Invalid MSRP header: {raw_header!r}") from exc

            name = (
                name_raw.decode(
                    "utf-8",
                    errors="strict",
                )
                .strip()
                .lower()
            )

            value = value_raw.decode(
                "utf-8",
                errors="strict",
            ).strip()

            headers[name] = value

    if "to-path" not in headers:
        raise ValueError("MSRP To-Path header is missing")

    if "from-path" not in headers:
        raise ValueError("MSRP From-Path header is missing")

    return MSRPMessage(
        transaction_id=transaction_id,
        method=method,
        status_code=status_code,
        comment=comment,
        headers=headers,
        body=body,
        continuation=continuation,
    )
