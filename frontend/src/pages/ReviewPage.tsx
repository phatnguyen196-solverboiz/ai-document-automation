import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../services/api";
import type { DocumentRecord, Extraction } from "../types";

const empty: Extraction = { id: 0, document: 0, customer: "", container_number: "", origin: "", destination: "", weight_kg: null, delivery_date: null, confidence: null, is_valid: false };

export function ReviewPage() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const [document, setDocument] = useState<DocumentRecord | null>(null);
  const [form, setForm] = useState<Extraction>(empty);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => { Promise.all([api.getDocument(id), api.getExtraction(id)]).then(([doc, data]) => { setDocument(doc); setForm(data); }).catch((err: Error) => setMessage(err.message)); }, [id]);
  const change = (field: keyof Extraction, value: string) => setForm((current) => ({ ...current, [field]: value }));
  async function save(event?: FormEvent) { event?.preventDefault(); setBusy(true); setMessage(""); try { const updated = await api.updateExtraction(id, form); setForm(updated); setErrors(updated.validation_errors || {}); setMessage(updated.is_valid ? "Changes saved. Data is valid." : "Changes saved. Review the highlighted fields."); return updated; } catch (err) { setMessage(err instanceof Error ? err.message : "Save failed"); return null; } finally { setBusy(false); } }
  async function approve(automate: boolean) { const updated = await save(); if (!updated?.is_valid) return; setBusy(true); try { await api.approve(id); if (automate) { await api.automate(id); navigate(`/documents/${id}/result`); } else navigate(`/documents/${id}`); } catch (err) { setMessage(err instanceof Error ? err.message : "Approval failed"); } finally { setBusy(false); } }
  if (!document) return <div className="empty">{message || "Loading review…"}</div>;

  return <>
    <Link className="back-link" to={`/documents/${id}`}>← Back to document</Link>
    <section className="review-heading"><div><p className="eyebrow">HUMAN REVIEW</p><h1>Verify extracted shipment data</h1><p>AI output is never submitted to the ERP without this approval step.</p></div><div className={`validity ${form.is_valid ? "valid" : "needs-review"}`}>{form.is_valid ? "Validation passed" : "Review required"}</div></section>
    {message && <div className={`alert ${form.is_valid ? "success" : "error"}`}>{message}</div>}
    <section className="review-grid">
      <article className="source-pane"><div className="pane-heading"><h2>Source text</h2><a href={document.file_url} target="_blank" rel="noreferrer">View PDF ↗</a></div><pre>{document.raw_text}</pre></article>
      <form className="fields-pane" onSubmit={save}><div className="pane-heading"><h2>Structured fields</h2><span>{form.confidence ? `${Math.round(Number(form.confidence) * 100)}% confidence` : "No score"}</span></div>
        <ReviewField label="Customer" value={form.customer} error={errors.customer} onChange={(value) => change("customer", value)} />
        <ReviewField label="Container number" value={form.container_number} error={errors.container_number} onChange={(value) => change("container_number", value.toUpperCase())} />
        <div className="field-row"><ReviewField label="Origin" value={form.origin} error={errors.origin} onChange={(value) => change("origin", value)} /><ReviewField label="Destination" value={form.destination} error={errors.destination} onChange={(value) => change("destination", value)} /></div>
        <div className="field-row"><ReviewField label="Weight (kg)" type="number" value={form.weight_kg || ""} error={errors.weight_kg} onChange={(value) => change("weight_kg", value)} /><ReviewField label="Delivery date" type="date" value={form.delivery_date || ""} error={errors.delivery_date} onChange={(value) => change("delivery_date", value)} /></div>
        {errors.form && <small className="field-error">{errors.form}</small>}
        <div className="review-actions"><button className="secondary" type="submit" disabled={busy}>Save changes</button><button className="secondary approve" type="button" disabled={busy} onClick={() => void approve(false)}>Approve</button><button className="button" type="button" disabled={busy} onClick={() => void approve(true)}>Approve & automate</button></div>
      </form>
    </section>
  </>;
}

function ReviewField({ label, type = "text", value, error, onChange }: { label: string; type?: string; value: string; error?: string; onChange: (value: string) => void }) {
  return <label className={error ? "has-error" : ""}><span>{label}</span><input type={type} value={value} onChange={(event) => onChange(event.target.value)} />{error && <small className="field-error">{error}</small>}</label>;
}
