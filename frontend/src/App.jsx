import { useMemo, useState } from "react";
import "./styles.css";

export default function App() {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState({ pill: "Ready", text: "Sélectionne une image pour commencer." });
  const [resultUrl, setResultUrl] = useState(null);
  const [busy, setBusy] = useState(false);

  const previewUrl = useMemo(() => (file ? URL.createObjectURL(file) : null), [file]);

  const clear = () => {
    setFile(null);
    setResultUrl(null);
    setStatus({ pill: "Ready", text: "Sélectionne une image pour commencer." });
  };

  const run = async () => {
    if (!file) {
      alert("Choisis une image d'abord.");
      return;
    }

    setBusy(true);
    setResultUrl(null);

    try {
      setStatus({ pill: "Uploading", text: "Upload de l'image…" });

      // ✅ IMPORTANT
      const formData = new FormData();
      formData.append("file", file);

      const up = await fetch("/upload", { method: "POST", body: formData });
      const upJson = await up.json().catch(() => ({}));
      if (!up.ok) throw new Error(upJson?.detail || "Upload failed");

      setStatus({ pill: "Running", text: "Exécution du script… (ça peut prendre du temps)" });

      const r = await fetch("/run", { method: "POST" });
      const j = await r.json().catch(() => ({}));
      
    if (j?.ok && j?.download_url) {
    const bust = `${j.download_url}?t=${Date.now()}`;
    setResultUrl(bust);
    setStatus({ pill: "Done ✅", text: "Terminé ✅" });
    } else {
    // ✅ Afficher les logs pour déboguer
    console.log("Backend response:", j);
    console.log("Logs from script:", j?.logs);
    throw new Error(j?.logs || "Pas de résultat trouvé dans /downloads");
    }
    } catch (e) {
      setStatus({ pill: "Failed ❌", text: `Erreur: ${e.message}` });
    } finally {
      setBusy(false);
    }
  };

  const downloadName = resultUrl ? resultUrl.split("/downloads/")[1]?.split("?")[0] : "result.jpg";

  return (
    <div className="wrap">
      <header className="top">
        <div className="brand">
          <div className="logo">G</div>
          <div>
            <h1>Gemini Product Studio</h1>
            <p>Upload → Run → Download</p>
          </div>
        </div>
      </header>

      <section className="card">
        <div className="grid">
          <div className="left">
            <h2>1) Choisir une image</h2>

            <label className="drop">
              <input
                type="file"
                accept="image/*"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />
              <div className="dropInner">
                <div className="icon">⬆️</div>
                <div className="txt">
                  <strong>Choisir une image</strong>
                  <div className="hint">PNG / JPG / WEBP</div>
                </div>
              </div>
            </label>

            {previewUrl && (
              <div className="preview">
                <img src={previewUrl} alt="preview" />
                <button className="ghost" onClick={clear} type="button">
                  Effacer
                </button>
              </div>
            )}

            <div className="actions">
              <button className="btn" onClick={run} disabled={busy}>
                🚀 Run
              </button>
              <button className="btn secondary" onClick={clear} disabled={busy}>
                🧹 Clear
              </button>
            </div>

            <div className="status">
              <div className="pill">{status.pill}</div>
              <div className="small">{status.text}</div>
            </div>
          </div>

          <div className="right">
            <h2>2) Résultat</h2>

            <div className="result">
              {!resultUrl ? (
                <div className="muted">Aucun résultat pour le moment.</div>
              ) : (
                <div className="resultInner">
                  <img src={resultUrl} alt="result" />
                  <div className="actions">
                    <a className="btn" href={resultUrl} download={downloadName}>
                      ⬇️ Télécharger l'image
                    </a>
                    <a className="btn secondary" href={resultUrl} target="_blank" rel="noreferrer">
                      🔍 Ouvrir
                    </a>
                  </div>
                  <div className="small">Fichier : {downloadName}</div>
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      <footer className="foot">Tip: إذا الصورة ما ظهرتش، جرّب refresh.</footer>
    </div>
  );
}