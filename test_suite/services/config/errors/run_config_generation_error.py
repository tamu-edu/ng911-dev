class RunConfigGenerationError(Exception):
    """
    Custom exception for handling Run Config Generation-related errors.

    Attributes:
        message (str): Description of the error.
        errors (list): List of detailed error messages.
    """
    def __init__(self, message: str = "Generation error occurred.", errors: list = None):
        """
        Initialize the exception.

        Args:
            message (str): A short description of the error.
            errors (list): A list of detailed error messages (optional).
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
        error_details = "\n".join(self.errors) if self.errors else "No additional details."
        return f"{self.message}\nDetails:\n{error_details}"
