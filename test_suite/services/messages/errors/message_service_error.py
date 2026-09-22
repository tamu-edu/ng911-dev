class MessageServiceError(Exception):
    """
    Custom exception raised when a pyshark packet can't be turned into a
    known SIP/HTTP message: a required header is missing, or a present one
    has an unparsable format.

    Attributes:
        message (str): Short description of what went wrong.
        errors (list): Detailed context lines (packet number, layer, field, raw value, ...).
    """

    def __init__(
        self,
        message: str = "Message service error occurred.",
        errors: list | None = None,
    ):
        """
        Initialize the exception.

        Args:
            message (str): A short description of the error.
            errors (list): A list of detailed context strings (optional).
        """
        super().__init__(message)
        self.message = message
        self.errors = errors or []

    def __str__(self):
        """
        String representation of the exception.

        Returns:
            str: Error message and details if available.
        """
        error_details = (
            "\n".join(self.errors) if self.errors else "No additional details."
        )
        return f"{self.message}\nDetails:\n{error_details}"
