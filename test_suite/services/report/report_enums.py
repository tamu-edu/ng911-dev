from enum import Enum


class ReportType(str, Enum):
    """
    Enum for Report types.
    """

    PDF = "pdf"
    DOCUMENT = "docx"
    XML = "xml"
    HTML = "html"
    CSV = "csv"
    JSON = "json"

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))

    @classmethod
    def not_io_list(cls):
        return [cls.PDF.value, cls.DOCUMENT.value, cls.XML.value, cls.CSV.value]
