import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ApiError, api } from "../services/api";
import type { DocumentRecord, Extraction } from "../types";

const empty: Extraction = { id: 0, document: 0, customer: "", container_number: "", origin: "", destination: "", weight_kg: null, delivery_date: null, confidence: null, is_valid: false };
type MessageTone = "success" | "error" | "info";

export function ReviewPage() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const [document, setDocument] = useState<DocumentRecord | null>(null);
  const [form, setForm] = useState<Extraction>(empty);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [message, setMessage] = useState("");
  const [messageTone, setMessageTone] = useState<MessageTone>("info");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setMessage("");
    Promise.all([api.getDocument(id), api.getExtraction(id)])
      .then(([doc, data]) => { if (!cancelled) { setDocument(doc); setForm(data); } })
      .catch((err: Error) => { if (!cancelled) { setMessageTone("error"); setMessage(err.message); } });
    return () => { cancelled = true; };
  }, [id]);

  const canEdit = document?.status === "REVIEW_REQUIRED" || document?.status === "FAILED";
  const change = (field: keyof Extraction, value: string) => setForm((current) => ({ ...current, [field]: value }));

  function showError(err: unknown, fallback: string) {
    if (err instanceof ApiError) setErrors(err.fieldErrors);
    setMessageTone("error");
    setMessage(err instanceof Error ? err.message : fallback);
  }

  async function save(event?: FormEvent) {
    event?.preventDefault();
    if (!canEdit) return null;
    setBusy(true); setMessage("");
    try {
      const updated = await api.updateExtraction(id, form);
      setForm(updated);
      setErrors(updated.validation_errors || {});
      setDocument((current) => current ? { ...current, status: "REVIEW_REQUIRED" } : current);
      setMessageTone(updated.is_valid ? "success" : "error");
      setMessage(updated.is_valid ? "Changes saved. Data is valid." : "Changes saved. Review the highlighted fields.");
      return updated;
    } catch (err) {
      showError(err, "Save failed");
      return null;
    } finally { setBusy(false); }
  }

  async function approve(automate: boolean) {
    const updated = await save();
    if (!updated?.is_valid) return;
    setBusy(true); setMessage("");
    try {
      const approved = await api.approve(id);
      setDocument(approved);
      if (automate) {
        await api.automate(id);
        navigate(`/documents/${id}/result`);
      } else navigate(`/documents/${id}`);
    } catch (err) {
      showError(err, "Approval failed");
    } finally { setBusy(false); }
  }

  async function runAutomation() {
    setBusy(true); setMessage("");
    try {
      await api.automate(id);
      navigate(`/documents/${id}/result`);
    } catch (err) {
      showError(err, "Automation failed");
      api.getDocument(id).then(setDocument).catch(() => undefined);
    } finally { setBusy(false); }
  }

  if (!document) return <div className="empty">{message || "Loading review…"}</div>;

  const stateLabel = document.status === "AUTOMATED" ? "Automation complete"
    : document.status === "APPROVED" ? "Approved"
      : form.is_valid ? "Validation passed" : "Review required";
  const validityClass = document.status === "AUTOMATED" || document.status === "APPROVED" || form.is_valid ? "valid" : "needs-review";

  return <>
    <Link className="back-link" to={`/documents/${id}`}>← Back to document</Link>
    <section className="review-heading"><div><p className="eyebrow">HUMAN REVIEW</p><h1>Verify extracted shipment data</h1><p>AI output is never submitted to the ERP without this approval step.</p></div><div className={`validity ${validityClass}`}>{stateLabel}</div></section>
    {message && <div className={`alert ${messageTone}`}>{message}</div>}
    <section className="review-grid">
      <article className="source-pane"><div className="pane-heading"><h2>Source text</h2><a href={document.file_url} target="_blank" rel="noreferrer">View PDF ↗</a></div><pre>{document.raw_text}</pre></article>
      <form className="fields-pane" onSubmit={save}><div className="pane-heading"><h2>Structured fields</h2><span>{form.confidence ? `${Math.round(Number(form.confidence) * 100)}% confidence` : "No score"}</span></div>
        <ReviewField disabled={!canEdit} label="Customer" value={form.customer} error={errors.customer} onChange={(value) => change("customer", value)} />
        <ReviewField disabled={!canEdit} label="Container number" value={form.container_number} error={errors.container_number} onChange={(value) => change("container_number", value.toUpperCase())} />
        <div className="field-row"><ReviewField disabled={!canEdit} label="Origin" value={form.origin} error={errors.origin} onChange={(value) => change("origin", value)} /><ReviewField disabled={!canEdit} label="Destination" value={form.destination} error={errors.destination} onChange={(value) => change("destination", value)} /></div>
        <div className="field-row"><ReviewField disabled={!canEdit} label="Weight (kg)" type="number" value={form.weight_kg ?? ""} error={errors.weight_kg} onChange={(value) => change("weight_kg", value)} /><ReviewField disabled={!canEdit} label="Delivery date" type="date" value={form.delivery_date ?? ""} error={errors.delivery_date} onChange={(value) => change("delivery_date", value)} /></div>
        {errors.form && <small className="field-error">{errors.form}</small>}
        <div className="review-actions">
          {canEdit ? <><button className="secondary" type="submit" disabled={busy}>Save changes</button><button className="secondary approve" type="button" disabled={busy} onClick={() => void approve(false)}>Approve</button><button className="button" type="button" disabled={busy} onClick={() => void approve(true)}>Approve & automate</button></>
            : document.status === "APPROVED" ? <button className="button" type="button" disabled={busy} onClick={() => void runAutomation()}>{busy ? "Automating…" : "Run automation"}</button>
              : document.status === "AUTOMATED" ? <Link className="button" to={`/documents/${id}/result`}>View result</Link>
                : <Link className="secondary" to={`/documents/${id}`}>View document</Link>}
        </div>
      </form>
    </section>
  </>;
}

function ReviewField({ label, type = "text", value, error, disabled = false, onChange }: { label: string; type?: string; value: string; error?: string; disabled?: boolean; onChange: (value: string) => void }) {
  return <label className={error ? "has-error" : ""}><span>{label}</span><input disabled={disabled} type={type} value={value} onChange={(event) => onChange(event.target.value)} />{error && <small className="field-error">{error}</small>}</label>;
}
