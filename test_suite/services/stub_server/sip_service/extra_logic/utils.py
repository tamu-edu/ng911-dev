import random  # nosec B311
import re
import string


def generate_identifier(identifier_type: str, fqdn: str) -> str:
    if identifier_type.lower() not in ["callid", "incidentid", "logid"]:
        return ""
    id_length = random.randint(10, 32)
    id_chars = string.ascii_letters + string.digits
    id_string = "".join(random.choice(id_chars) for _ in range(id_length))
    return f"urn:emergency:uid:{identifier_type.lower()}:{id_string}:{fqdn}"


def add_header_field(
    message_text: str,
    header_name: str,
    header_value: str,
    parameters: dict = None,
    add_on_top: bool = False,
) -> str:
    lines = message_text.splitlines()
    params = ""
    if parameters:
        for param, value in parameters.items():
            params += f";{param}={value}"
    index = 0
    headers_group = [line for line in lines if line.startswith(f"{header_name}: ")]
    for index, line in enumerate(lines):
        if add_on_top and line.startswith(f"{header_name}: "):
            break
        elif headers_group and headers_group[-1] == line:
            index += 1
            break
        elif all(not c.isalnum() for c in line):
            break
    lines.insert(index, f"{header_name}: {header_value}{params}")
    return "\r\n".join(lines)


def add_header_field_on_top(
    message_text: str, header_name: str, header_value: str, parameters: dict = None
) -> str:
    return add_header_field(
        message_text, header_name, header_value, parameters, add_on_top=True
    )


def replace_header_field_value(
    message_text: str,
    header_name: str,
    header_value: str,
    parameters: dict = None,
    header_contains: str = "",
) -> str:
    if not message_text:
        return ""
    out = message_text.splitlines()
    params = ""
    if parameters:
        for param, value in parameters.items():
            params += f";{param}={value}"
    if header_name.lower() == "request_uri":
        elements = out[0].split(" ")
        elements[1] = header_value
        out[0] = " ".join(elements)
    else:
        for index, line in enumerate(out):
            if line.startswith(f"{header_name}:") and header_contains in line:
                out[index] = f"{header_name}: {header_value}{params}"
    return "\r\n".join(out)


def add_or_replace_header_field(
    message_text: str,
    header_name: str,
    header_value: str,
    parameters: dict = None,
    header_contains: str = "",
) -> str:
    for line in message_text.splitlines():
        if f"{header_name}: " in line and header_contains in line:
            return replace_header_field_value(
                message_text, header_name, header_value, parameters, header_contains
            )
    return add_header_field(message_text, header_name, header_value, parameters)


def add_header_field_if_not_exist(
    message_text: str,
    header_name: str,
    header_value: str,
    parameters: dict = None,
    header_contains: str = "",
) -> str:
    for line in message_text.splitlines():
        if line.startswith(f"{header_name.removesuffix(':')}: "):
            if (header_contains and header_contains in line) or header_value in line:
                return message_text
    return add_header_field(message_text, header_name, header_value, parameters)


def add_message_body_if_not_exist(
    message_text: str, content_type: str, content_body: str, content_id: str = ""
) -> str:
    if (
        re.sub(r"\s+", "", content_body).lower()
        in re.sub(r"\s+", "", message_text).lower()
    ):
        return message_text
    out = message_text
    length = len(content_body.encode("utf-8"))

    boundary = ""

    multipart_header = [
        marker
        for marker in message_text.splitlines()
        if "Content-Type: multipart/mixed" in marker
    ]
    if multipart_header:
        boundary = multipart_header[0].split("boundary=")[1].split(";")[0]
    elif "Content-Type: " in message_text:
        boundary = "ng911"

        # Preparing existing message for additional content - transforming to multipart/mixed
        existing_headers_and_body = ""
        for index, line in enumerate(message_text.splitlines()):
            if (
                "Content-Type: " in line
                or "Content-Length: " in line
                or "Content-ID: " in line
            ):
                existing_headers_and_body += line + "\r\n"
            elif all(not c.isalnum() for c in line):
                existing_headers_and_body += "\r\n" + "\r\n".join(
                    message_text.splitlines()[(index + 1) :]
                )
                out = "\r\n".join(message_text.splitlines()[:index])
        out = replace_header_field_value(
            out, "Content-Type", "multipart/mixed", {"boundary": boundary}
        )
        out = "\r\n".join(
            marker for marker in out.splitlines() if "Content-Length: " not in marker
        )
        out += "\r\n\r\n" + "--" + boundary + "\r\n" + existing_headers_and_body

    out = out.rstrip() + "\r\n"
    if boundary:
        out += "\r\n" + "--" + boundary + "\r\n"
    out += f"Content-Type: {content_type}\r\n"
    out += f"Content-Length: {str(length)}\r\n"
    if content_id:
        out += f"Content-ID: {content_id}\r\n"
    out += "\r\n" + content_body
    return out
