export type DocumentStatus = "UPLOADED" | "PROCESSING" | "REVIEW_REQUIRED" | "APPROVED" | "AUTOMATED" | "FAILED";

export type DocumentRecord = {
  id: number;
  original_filename: string;
  file: string;
  file_url: string;
  raw_text: string;
  status: DocumentStatus;
  erp_reference: string;
  created_at: string;
  updated_at: string;
};

export type Extraction = {
  id: number;
  document: number;
  customer: string;
  container_number: string;
  origin: string;
  destination: string;
  weight_kg: string | null;
  delivery_date: string | null;
  confidence: string | null;
  is_valid: boolean;
  validation_errors?: Record<string, string>;
};

export type ProcessingJob = {
  id: number;
  document: number;
  job_type: "EXTRACTION" | "AUTOMATION";
  status: "PENDING" | "RUNNING" | "SUCCESS" | "FAILED";
  error_message: string;
};
