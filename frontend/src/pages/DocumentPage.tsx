import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { StatusBadge } from "../components/StatusBadge";
import { api } from "../services/api";
import type { DocumentRecord, Extraction } from "../types";

export function DocumentPage() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const [document, setDocument] = useState<DocumentRecord | null>(null);
  const [extraction, setExtraction] = useState<Extraction | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      const [doc, data] = await Promise.all([api.getDocument(id), api.getExtraction(id).catch(() => null)]);
      setDocument(doc); setExtraction(data);
    } catch (err) { setError(err instanceof Error ? err.message : "Unable to load document"); }
  }, [id]);
  useEffect(() => { void load(); }, [load]);
  async function runExtraction() { setBusy(true); setError(""); try { await api.extract(id); navigate(`/documents/${id}/review`); } catch (err) { setError(err instanceof Error ? err.message : "Extraction failed"); void load(); } finally { setBusy(false); } }
  async function runAutomation() { setBusy(true); setError(""); try { await api.automate(id); navigate(`/documents/${id}/result`); } catch (err) { setError(err instanceof Error ? err.message : "Automation failed"); void load(); } finally { setBusy(false); } }
  if (!document) return <div className="empty">{error || "Loading document…"}</div>;

  return <>
    <Link className="back-link" to="/">← Back to overview</Link>
    <section className="document-hero"><div><p className="eyebrow">SHIPPING DOCUMENT</p><h1>{document.original_filename}</h1><StatusBadge status={document.status} /></div><div className="hero-actions">
      {document.status === "AUTOMATED" ? <Link className="button" to={`/documents/${id}/result`}>View result</Link>
        : document.status === "APPROVED" ? <><Link className="secondary" to={`/documents/${id}/review`}>View approved data</Link><button className="button" disabled={busy} onClick={() => void runAutomation()}>{busy ? "Automating…" : "Run automation"}</button></>
          : extraction ? <Link className="button" to={`/documents/${id}/review`}>Review extraction</Link>
            : document.status === "PROCESSING" ? <button className="button" disabled>Processing…</button>
              : <button className="button" disabled={busy} onClick={() => void runExtraction()}>{busy ? "Extracting…" : "Run extraction"}</button>}
    </div></section>
    {error && <div className="alert error">{error}</div>}
    <section className="detail-cards"><article><span>Created</span><strong>{new Date(document.created_at).toLocaleString()}</strong></article><article><span>Confidence</span><strong>{extraction?.confidence ? `${Math.round(Number(extraction.confidence) * 100)}%` : "—"}</strong></article><article><span>ERP reference</span><strong>{document.erp_reference || "Not submitted"}</strong></article></section>
    <section className="panel text-panel"><div className="panel-heading"><div><h2>Extracted PDF text</h2><p>Digital text captured by PyMuPDF</p></div><a className="text-link" href={document.file_url} target="_blank" rel="noreferrer">Open original PDF ↗</a></div><pre>{document.raw_text || "Extraction has not run yet."}</pre></section>
  </>;
}
