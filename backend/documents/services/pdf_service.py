import re

import fitz

from .exceptions import InvalidPdfError, PdfTextExtractionError


def normalize_whitespace(text: str) -> str:
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def extract_pdf_text(uploaded_file) -> str:
    try:
        uploaded_file.seek(0)
        payload = uploaded_file.read()
        uploaded_file.seek(0)
        with fitz.open(stream=payload, filetype="pdf") as pdf:
            if pdf.page_count == 0:
                raise InvalidPdfError("PDF has no pages")
            text = "\n".join(page.get_text("text") for page in pdf)
    except InvalidPdfError:
        raise
    except Exception as exc:
        raise InvalidPdfError("Unable to open the uploaded PDF") from exc

    normalized = normalize_whitespace(text)
    if not normalized:
        raise PdfTextExtractionError("No digital text was found; OCR is outside the MVP scope")
    return normalized
