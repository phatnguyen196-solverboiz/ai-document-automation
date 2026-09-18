import { ChangeEvent, DragEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../services/api";

export function UploadPage() {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [progress, setProgress] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  function choose(candidate?: File) {
    if (!candidate) return;
    if (candidate.type !== "application/pdf" || !candidate.name.toLowerCase().endsWith(".pdf")) return setError("Choose a PDF file.");
    if (candidate.size > 10 * 1024 * 1024) return setError("PDF must be 10 MB or smaller.");
    setError(""); setFile(candidate);
  }
  function onDrop(event: DragEvent) { event.preventDefault(); choose(event.dataTransfer.files[0]); }
  function onInput(event: ChangeEvent<HTMLInputElement>) { choose(event.target.files?.[0]); }
  async function upload() {
    if (!file) return;
    setBusy(true); setError("");
    try {
      const document = await api.uploadDocument(file, setProgress);
      await api.extract(document.id);
      navigate(`/documents/${document.id}/review`);
    } catch (err) { setError(err instanceof Error ? err.message : "Upload failed"); }
    finally { setBusy(false); }
  }

  return <section className="narrow-page">
    <Link className="back-link" to="/">← Back to overview</Link>
    <div className="upload-card"><p className="eyebrow">NEW DOCUMENT</p><h1>Upload a shipping PDF</h1><p>The file is extracted locally, then passed through the configured structured-output service.</p>
      {error && <div className="alert error">{error}</div>}
      <label className="dropzone" onDragOver={(event) => event.preventDefault()} onDrop={onDrop}>
        <input type="file" accept="application/pdf,.pdf" onChange={onInput} />
        <span className="upload-icon">PDF</span><strong>{file ? file.name : "Drop your PDF here"}</strong><small>{file ? `${(file.size / 1024).toFixed(1)} KB` : "or click to browse • maximum 10 MB"}</small>
      </label>
      {busy && <div className="progress"><span style={{ width: `${progress}%` }} /></div>}
      <button className="button full" disabled={!file || busy} onClick={() => void upload()}>{busy ? `Processing ${progress}%` : "Upload and extract"}</button>
    </div>
  </section>;
}
