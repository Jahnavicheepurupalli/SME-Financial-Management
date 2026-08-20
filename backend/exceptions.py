class DocumentParseError(Exception):
    """Raised when a document cannot be read or parsed."""


class AnalysisStorageError(Exception):
    """Raised when an analysis artifact cannot be persisted."""


class ReportGenerationError(AnalysisStorageError):
    """Raised when the analysis PDF cannot be generated."""
