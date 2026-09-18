import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../services/api";
import type { DocumentRecord } from "../types";

export function ResultPage() {
  const { id = "" } = useParams();
  const [document, setDocument] = useState<DocumentRecord | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    api.getDocument(id)
      .then((data) => { if (!cancelled) setDocument(data); })
      .catch((err: Error) => { if (!cancelled) setError(err.message); });
    return () => { cancelled = true; };
  }, [id]);

  if (error) return <section className="result-page"><div className="alert error">{error}</div><Link className="secondary" to="/">Back to overview</Link></section>;
  if (!document) return <div className="empty">Loading result…</div>;
  if (document.status !== "AUTOMATED" || !document.erp_reference) return <section className="result-page"><p className="eyebrow">AUTOMATION NOT COMPLETE</p><h1>No ERP result yet</h1><p>This document has not completed automation.</p><div className="result-actions"><Link className="button" to={`/documents/${id}`}>Return to document</Link></div></section>;

  return <section className="result-page"><div className="success-mark">✓</div><p className="eyebrow">AUTOMATION COMPLETE</p><h1>Order created successfully</h1><p>The reviewed shipment data was submitted to the local demo ERP portal.</p><div className="reference"><span>ERP reference</span><strong>{document.erp_reference}</strong></div><div className="result-actions"><Link className="button" to={`/documents/${id}`}>View document</Link><Link className="secondary" to="/">Back to overview</Link></div></section>;
}
