import type { DocumentStatus } from "../types";

const labels: Record<DocumentStatus, string> = {
  UPLOADED: "Uploaded", PROCESSING: "Processing", REVIEW_REQUIRED: "Review required",
  APPROVED: "Approved", AUTOMATED: "Automated", FAILED: "Failed",
};

export function StatusBadge({ status }: { status: DocumentStatus }) {
  return <span className={`badge badge-${status.toLowerCase()}`}>{labels[status]}</span>;
}
