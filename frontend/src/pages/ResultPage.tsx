import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../services/api";
import type { DocumentRecord } from "../types";

export function ResultPage() {
  const { id = "" } = useParams();
  const [document, setDocument] = useState<DocumentRecord | null>(null);
  useEffect(() => { void api.getDocument(id).then(setDocument); }, [id]);
  return <section className="result-page"><div className="success-mark">✓</div><p className="eyebrow">AUTOMATION COMPLETE</p><h1>Order created successfully</h1><p>The reviewed shipment data was submitted to the local demo ERP portal.</p><div className="reference"><span>ERP reference</span><strong>{document?.erp_reference || "Loading…"}</strong></div><div className="result-actions"><Link className="button" to={`/documents/${id}`}>View document</Link><Link className="secondary" to="/">Back to overview</Link></div></section>;
}
