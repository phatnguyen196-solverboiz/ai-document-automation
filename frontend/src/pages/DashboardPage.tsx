import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { StatusBadge } from "../components/StatusBadge";
import { api } from "../services/api";
import type { DocumentRecord } from "../types";

export function DashboardPage() {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => { api.listDocuments().then(setDocuments).catch((err: Error) => setError(err.message)).finally(() => setLoading(false)); }, []);
  const stats = useMemo(() => ({
    processed: documents.length,
    review: documents.filter((item) => item.status === "REVIEW_REQUIRED").length,
    automated: documents.filter((item) => item.status === "AUTOMATED").length,
    failed: documents.filter((item) => item.status === "FAILED").length,
  }), [documents]);

  return <>
    <section className="page-heading"><div><p className="eyebrow">OPERATIONS</p><h1>Document processing</h1><p>Turn shipping PDFs into reviewed ERP orders.</p></div><Link className="button" to="/upload">Upload PDF</Link></section>
    <section className="metric-grid">
      <article><span>Documents processed</span><strong>{stats.processed}</strong><i className="teal" /></article>
      <article><span>Pending review</span><strong>{stats.review}</strong><i className="amber" /></article>
      <article><span>Automated</span><strong>{stats.automated}</strong><i className="green" /></article>
      <article><span>Failed</span><strong>{stats.failed}</strong><i className="red" /></article>
    </section>
    {error && <div className="alert error">{error}</div>}
    <section className="panel">
      <div className="panel-heading"><div><h2>Recent documents</h2><p>Human-reviewed extraction and automation status</p></div></div>
      {loading ? <div className="empty">Loading documents…</div> : documents.length === 0 ? <div className="empty"><strong>No documents yet</strong><span>Upload a sample shipping order to begin.</span></div> :
        <div className="table-wrap"><table><thead><tr><th>Filename</th><th>Status</th><th>Created</th><th>ERP reference</th><th>Action</th></tr></thead><tbody>{documents.map((document) => <tr key={document.id}><td><strong>{document.original_filename}</strong></td><td><StatusBadge status={document.status} /></td><td>{new Date(document.created_at).toLocaleString()}</td><td>{document.erp_reference || "—"}</td><td><Link className="text-link" to={`/documents/${document.id}`}>Open →</Link></td></tr>)}</tbody></table></div>}
    </section>
  </>;
}
