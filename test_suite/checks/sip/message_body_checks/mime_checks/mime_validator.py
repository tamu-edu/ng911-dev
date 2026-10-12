import re
from dataclasses import dataclass


@dataclass
class MimePart:
    """A single MIME part: its headers text and body text."""

    headers: str
    body: str
    content_type: str | None


class MimeStructureValidator:
    """
    Verifies that a Content-Type header correctly declares a multipart
    subtype and boundary, and that the boundary is actually used as a
    part delimiter in the body, recursing into any nested multipart parts.
    """

    def verify(self, content_type_raw: str, body: str) -> str:
        """
        :param content_type_raw: Raw Content-Type header value, e.g.
            "multipart/mixed; boundary=simple-multipart-boundary".
        :param body: Raw multipart body (everything after the blank line).
        :return: "PASSED" if all checks succeed, otherwise "FAILED -> ...".
        """
        if not isinstance(content_type_raw, str) or not content_type_raw.strip():
            return (
                f"FAILED -> 'content_type_raw' must be a non-empty string, "
                f"got {type(content_type_raw).__name__}: {content_type_raw!r}"
            )

        if not isinstance(body, str) or not body.strip():
            return (
                f"FAILED -> 'body' must be a non-empty string, "
                f"got {type(body).__name__}: {body!r}"
            )

        try:
            error = self._verify_level(content_type_raw, body, level="top-level")
        except Exception as e:
            return f"FAILED -> Unexpected error while verifying MIME structure: {e!r}"

        return error or "PASSED"

    #  one multipart level

    def _verify_level(self, content_type_raw: str, body: str, level: str) -> str | None:
        content_type, params = self._parse_content_type_header(content_type_raw)

        if not content_type.startswith("multipart/"):
            return f"FAILED -> {level} Content-Type is not a multipart subtype. Actual: '{content_type}'"

        declared_boundary = params.get("boundary")
        if not declared_boundary:
            return f"FAILED -> {level} Content-Type has no boundary parameter"

        if not self._boundary_used_as_delimiter(body, declared_boundary):
            return (
                f"FAILED -> {level} boundary '{declared_boundary}' declared in "
                f"Content-Type is not used as an actual part delimiter in the body"
            )

        parts = self._split_mime_parts(body, declared_boundary)
        if not parts:
            return f"FAILED -> {level} body could not be split into parts using boundary '{declared_boundary}'"

        for i, part in enumerate(parts):
            if not part.content_type:
                return (
                    f"FAILED -> {level} part at index {i} missing Content-Type header"
                )

            if part.content_type.lower().startswith("multipart/"):
                nested_error = self._verify_level(
                    part.content_type, part.body, level=f"nested part {i}"
                )
                if nested_error:
                    return nested_error
            else:
                mismatch = self._content_matches_declared_type(
                    part.content_type.lower(), part.body
                )
                if mismatch:
                    return f"FAILED -> {level} part at index {i} ({part.content_type}) {mismatch}"

        return None

    # Content-Type header parsing

    @staticmethod
    def _parse_content_type_header(content_type_raw: str) -> tuple[str, dict[str, str]]:
        """
        Parses a raw Content-Type header value into (content_type, params).
        E.g. "multipart/mixed; boundary=simple-multipart-boundary" ->
        ("multipart/mixed", {"boundary": "simple-multipart-boundary"}).
        """
        content_type_raw = (content_type_raw or "").split(":", 1)[-1].strip()
        parts = [p.strip() for p in content_type_raw.split(";")]
        content_type = parts[0].lower()

        params: dict[str, str] = {}
        for param in parts[1:]:
            if "=" not in param:
                continue
            key, value = param.split("=", 1)
            value = value.strip()
            if len(value) >= 2 and value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            params[key.strip().lower()] = value

        return content_type, params

    #  boundary / part splitting

    @staticmethod
    def _boundary_used_as_delimiter(text: str, boundary: str) -> bool:
        """True if `--boundary` appears at the start of a line (with optional trailing '--')."""
        if not boundary:
            return False
        pattern = re.compile(rf"(?m)^--{re.escape(boundary)}(--)?\s*$")
        return bool(pattern.search(text))

    def _split_mime_parts(self, body: str, boundary: str) -> list[MimePart]:
        """Splits a multipart body into MimePart objects using the given boundary."""
        if not boundary:
            return []
        delimiter = f"--{boundary}"
        raw_parts = re.split(rf"(?m)^{re.escape(delimiter)}(--)?\s*$", body)
        raw_parts = [
            p.strip("\r\n") for p in raw_parts if p and p.strip() and p.strip() != "--"
        ]

        parts = []
        for raw_part in raw_parts:
            headers, part_body = self._split_headers_and_body(raw_part)
            content_type = self._extract_content_type_line(headers)
            parts.append(
                MimePart(headers=headers, body=part_body, content_type=content_type)
            )
        return parts

    @staticmethod
    def _split_headers_and_body(part_text: str) -> tuple[str, str]:
        """
        Splits a MIME part into (headers_text, body_text) on the blank-line
        separator. Any number of consecutive blank lines right after the
        headers is treated as a single separator.
        """
        if not part_text:
            return "", ""

        match = re.search(r"(?:\r?\n){2,}", part_text)
        if not match:
            return part_text, ""

        return part_text[: match.start()], part_text[match.end() :]

    @staticmethod
    def _extract_content_type_line(part_headers: str) -> str | None:
        """Extracts the full Content-Type header value (including params) from a part's headers."""
        if not part_headers:
            return None
        match = re.search(
            r"^Content-Type:\s*(.+)$", part_headers, re.IGNORECASE | re.MULTILINE
        )
        return match.group(1).strip() if match else None

    # leaf-content checks

    @staticmethod
    def _content_matches_declared_type(
        part_content_type: str, part_body: str
    ) -> str | None:
        """
        Checks that a leaf part's content looks like what
        its Content-Type declares. Returns None if it matches, otherwise a
        description of the mismatch.
        """
        if not part_content_type:
            return None

        stripped = (part_body or "").strip()

        if part_content_type == "application/sdp":
            if not stripped.startswith("v="):
                return "declared as application/sdp but content does not start with 'v=' (SDP version line)"

        elif part_content_type.endswith("+xml") or part_content_type in (
            "text/xml",
            "application/xml",
        ):
            if not (stripped.startswith("<?xml") or stripped.startswith("<")):
                return f"declared as '{part_content_type}' but content does not look like XML"

        return None


def verify_mime_structure(content_type_raw: str, body: str) -> str:
    """
    Verifies that Content-Type headers correctly reflect the boundary
    string and multipart subtype, at every multipart level.

    :param content_type_raw: Raw Content-Type header value.
    :param body: Raw multipart body.
    :return: "PASSED" if all checks succeed, otherwise "FAILED -> ...".
    """
    return MimeStructureValidator().verify(content_type_raw, body)
