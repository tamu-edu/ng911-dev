import re

from tests.ECRF_LVF_013.constants import APP_UNIQUE_STRING_PATTERN

PATH_BLOCK_PATTERN = re.compile(
    r"<(?:[\w.\-]+:)?path\b(?:[^>]*/>|[^>]*>.*?</(?:[\w.\-]+:)?path\s*>)",
    re.DOTALL,
)
VIA_SOURCE_PATTERN = re.compile(
    r"<(?:[\w.\-]+:)?via\b[^>]*?\bsource\s*=\s*\"([^\"]*)\"", re.DOTALL
)


def extract_path_block(xml: str) -> str:
    """
    Extracts the raw <path> element from a LoST XML message verbatim
    (whitespace and attribute formatting preserved).
    :param xml: LoST XML message body as a string
    :return: raw <path> element as a string or empty string if not found
    """
    if not isinstance(xml, str):
        return ""
    match = PATH_BLOCK_PATTERN.search(xml)
    return match.group(0) if match else ""


def extract_via_sources(xml: str) -> list:
    """
    Extracts 'source' attribute values of all <via> elements of the <path> element
    keeping the document order.
    :param xml: LoST XML message body as a string
    :return: list of 'source' values or empty list if not found
    """
    path_block = extract_path_block(xml)
    return VIA_SOURCE_PATTERN.findall(path_block) if path_block else []


def validate_via_source_format(via_source: str):
    """
    Validates that a <via> 'source' value conforms to the RFC 5222 'appUniqueString'
    token pattern (([a-zA-Z0-9\\-]+\\.)+[a-zA-Z0-9]+).
    :param via_source: value of the <via> 'source' attribute
    :return: "PASSED" or an error message
    """
    try:
        assert via_source, "FAILED -> 'via' source value not found."
        assert isinstance(
            via_source, str
        ), f"FAILED -> 'via' source is not a string. Actual: {type(via_source)}"
        assert re.match(APP_UNIQUE_STRING_PATTERN, via_source), (
            "FAILED -> 'via' source doesn't conform to the 'appUniqueString' pattern "
            f"'{APP_UNIQUE_STRING_PATTERN}'. Actual: {via_source}"
        )
        return "PASSED"
    except AssertionError as e:
        return str(e)
