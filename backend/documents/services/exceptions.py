class DocumentProcessingError(Exception):
    pass


class InvalidPdfError(DocumentProcessingError):
    pass


class PdfTextExtractionError(DocumentProcessingError):
    pass


class LLMServiceError(DocumentProcessingError):
    pass


class StructuredOutputError(DocumentProcessingError):
    pass


class InvalidWorkflowState(DocumentProcessingError):
    """Raised when an action is not valid for the document's current state."""
