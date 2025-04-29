from enum import Enum


class ReportType(str, Enum):
    """
    Enum for Report types.
    """
    PDF = "pdf"
    DOCUMENT = "docx"
    XML = "xml"
    CSV = "csv"
    JSON = "json"

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))

