# Architecture, trust boundaries, and state machine

## Request flow

```mermaid
sequenceDiagram
  participant U as User
  participant R as React UI
  participant D as Django API
  participant P as PDF service
  participant L as LLM service
  participant V as Pydantic
  participant E as ERP portal
  U->>R: Upload PDF
  R->>D: POST /documents/
  R->>D: POST /documents/{id}/extract/
  D->>P: extract digital text
  D->>L: strict JSON prompt
  L-->>D: untrusted JSON
  D->>V: validate and normalize
  D-->>R: review-required extraction
  U->>R: correct and approve
  R->>D: PATCH extraction + POST approve
  D->>V: validate again
  R->>D: POST automate
  D->>E: Selenium form submission
  E-->>D: ERP reference
```

## Trust boundaries

- PDF content is untrusted. Only PDFs up to 10 MB are accepted; PyMuPDF parsing failures are explicit.
- LLM output is untrusted. JSON mode improves shape but does not replace Pydantic validation.
- A passing validation result does not imply approval. Every extraction transitions to `REVIEW_REQUIRED`.
- The ERP write endpoint checks the persisted `APPROVED` state; the frontend cannot bypass it.
- Secrets exist only in environment variables. Mock mode requires no external credential.

## Document states

```mermaid
stateDiagram-v2
  [*] --> UPLOADED
  UPLOADED --> PROCESSING: extract
  PROCESSING --> REVIEW_REQUIRED: extraction saved
  PROCESSING --> FAILED: extraction error
  REVIEW_REQUIRED --> REVIEW_REQUIRED: edit and revalidate
  REVIEW_REQUIRED --> APPROVED: human approval
  APPROVED --> AUTOMATED: ERP success
  APPROVED --> FAILED: ERP failure
```

## Service boundaries

- `pdf_service.py`: binary PDF → normalized text
- `llm_service.py`: strict prompt, provider call/mock mode, JSON parsing
- `validation_service.py`: domain schema and storage-safe normalization
- `document_service.py`: extraction job orchestration and state changes
- `automation_service.py`: ERP job orchestration and transaction
- `portal_client.py`: selectors, waits, form submission, and browser cleanup

The orchestration stays out of Django views, and Selenium stays out of both views and domain services.
