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
