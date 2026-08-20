class DocumentParseError(Exception):
    """Raised when a document cannot be read or parsed."""

    DEFAULT_USER_MESSAGE = (
        "The file could not be read; it may be corrupt or in an unsupported format."
    )

    def __init__(self, detail, *, user_message=None):
        super().__init__(detail)
        self.user_message = user_message or self.DEFAULT_USER_MESSAGE


class AnalysisStorageError(Exception):
    """Raised when an analysis artifact cannot be persisted."""


class ReportGenerationError(AnalysisStorageError):
    """Raised when the analysis PDF cannot be generated."""
