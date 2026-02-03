import { useState, useEffect } from "react";
import "./styles.css";

export default function App() {
  const [files, setFiles] = useState([]);
  const [jobId, setJobId] = useState(null);
  const [jobStatus, setJobStatus] = useState(null);
  const [busy, setBusy] = useState(false);
  const [previewUrls, setPreviewUrls] = useState({});

  // Polling pour récupérer le statut du job
  useEffect(() => {
    if (!jobId || !busy) return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/job/${jobId}`);
        const data = await res.json();

        if (data.ok) {
          setJobStatus(data);

          // Si le job est terminé, arrêter le polling
          if (data.status === "completed") {
            setBusy(false);
            clearInterval(interval);
          }
        }
      } catch (e) {
        console.error("Polling error:", e);
      }
    }, 2000); // Poll toutes les 2 secondes

    return () => clearInterval(interval);
  }, [jobId, busy]);

  // Générer les aperçus des images sélectionnées
  useEffect(() => {
    const newPreviewUrls = {};
    
    files.forEach((file) => {
      const key = `${file.name}-${file.size}`;
      if (!previewUrls[key]) {
        const url = URL.createObjectURL(file);
        newPreviewUrls[key] = url;
      }
    });

    if (Object.keys(newPreviewUrls).length > 0) {
      setPreviewUrls((prev) => ({ ...prev, ...newPreviewUrls }));
    }

    // Cleanup des URLs qui ne sont plus utilisées
    return () => {
      Object.values(newPreviewUrls).forEach((url) => URL.revokeObjectURL(url));
    };
  }, [files]);

  const handleFileSelect = (e) => {
    const selectedFiles = Array.from(e.target.files || []);

    setFiles((prev) => {
      // Merge + éviter doublons (même nom + taille)
      const merged = [...prev, ...selectedFiles];
      const unique = Array.from(
        new Map(merged.map((f) => [`${f.name}-${f.size}`, f])).values()
      );
      return unique;
    });

    setJobId(null);
    setJobStatus(null);

    // Important: reset input pour permettre re-sélection du même fichier
    e.target.value = "";
  };

  const removeFile = (key) => {
    setFiles((prev) => prev.filter((f) => `${f.name}-${f.size}` !== key));
    
    // Cleanup de l'URL de prévisualisation
    if (previewUrls[key]) {
      URL.revokeObjectURL(previewUrls[key]);
      setPreviewUrls((prev) => {
        const newUrls = { ...prev };
        delete newUrls[key];
        return newUrls;
      });
    }
  };

  const clear = () => {
    // Cleanup de toutes les URLs de prévisualisation
    Object.values(previewUrls).forEach((url) => URL.revokeObjectURL(url));
    
    setFiles([]);
    setPreviewUrls({});
    setJobId(null);
    setJobStatus(null);
    setBusy(false);
  };

  const run = async () => {
    if (files.length === 0) {
      alert("Choisis au moins une image d'abord.");
      return;
    }

    setBusy(true);
    setJobStatus(null);

    try {
      // 1️⃣ Upload toutes les images
      const formData = new FormData();
      files.forEach((file) => {
        formData.append("files", file);
      });

      const uploadRes = await fetch("/upload-batch", {
        method: "POST",
        body: formData,
      });

      const uploadData = await uploadRes.json();

      if (!uploadData.ok) {
        throw new Error(uploadData.error || "Upload failed");
      }

      const newJobId = uploadData.job_id;
      setJobId(newJobId);

      // 2️⃣ Lancer le traitement
      const runRes = await fetch(`/run-batch/${newJobId}`, {
        method: "POST",
      });

      const runData = await runRes.json();

      if (!runData.ok) {
        throw new Error(runData.error || "Failed to start processing");
      }

      // Le polling va maintenant gérer la suite
    } catch (e) {
      alert(`Erreur: ${e.message}`);
      setBusy(false);
    }
  };

  const successCount = jobStatus?.success || 0;
  const failedCount = jobStatus?.failed || 0;
  const totalCount = jobStatus?.total || files.length;

  return (
    <div className="wrap">
      <header className="top">
        <div className="brand">
          <div className="logo">G</div>
          <div>
            <h1>Gemini Product Studio</h1>
            <p>Batch Processing Mode</p>
          </div>
        </div>
      </header>

      <section className="card">
        <div className="grid">
          <div className="left">
            <h2>1) Sélectionner les images</h2>

            <label className="drop">
              <input
                type="file"
                accept="image/*"
                multiple
                onChange={handleFileSelect}
                disabled={busy}
              />
              <div className="dropInner">
                <div className="icon">⬆️</div>
                <div className="txt">
                  <strong>Choisir des images</strong>
                  <div className="hint">
                    PNG / JPG / WEBP (1 ou plusieurs)
                  </div>
                </div>
              </div>
            </label>

            {files.length > 0 && (
              <div className="fileList">
                <h3>📁 {files.length} image(s) sélectionnée(s)</h3>
                <ul>
                  {files.map((file, idx) => {
                    const key = `${file.name}-${file.size}`;
                    return (
                      <li 
                        key={key}
                        style={{
                          backgroundImage: previewUrls[key] 
                            ? `url(${previewUrls[key]})` 
                            : 'none',
                          backgroundSize: 'cover',
                          backgroundPosition: 'center'
                        }}
                        title={`${file.name} (${(file.size / 1024).toFixed(0)} KB)`}
                      >
                        <button onClick={() => removeFile(key)}>✖</button>
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}

            <div className="actions">
              <button className="btn" onClick={run} disabled={busy}>
                {busy ? "⏳ Processing..." : "🚀 Run Batch"}
              </button>
              <button
                className="btn secondary"
                onClick={clear}
                disabled={busy}
              >
                🧹 Clear
              </button>
            </div>

            {jobStatus && (
              <div className="progress">
                <div className="progressHeader">
                  <span className="pill">
                    {jobStatus.status === "completed"
                      ? "Done ✅"
                      : "Processing..."}
                  </span>
                  <span className="small">
                    {jobStatus.completed}/{jobStatus.total}
                  </span>
                </div>

                <div className="progressBar">
                  <div
                    className="progressFill"
                    style={{ width: `${jobStatus.progress_percent}%` }}
                  />
                </div>

                <div className="stats">
                  <div className="stat success">✅ {successCount} réussis</div>
                  {failedCount > 0 && (
                    <div className="stat failed">❌ {failedCount} échoués</div>
                  )}
                </div>
              </div>
            )}
          </div>

          <div className="right">
            <h2>2) Résultats</h2>

            <div className="results">
              {!jobStatus || jobStatus.results.length === 0 ? (
                <div className="muted">
                  Les résultats apparaîtront ici au fur et à mesure...
                </div>
              ) : (
                <div className="resultsList">
                  {jobStatus.results.map((result, idx) => (
                    <div
                      key={idx}
                      className={`resultItem ${
                        result.success ? "success" : "failed"
                      }`}
                    >
                      <div className="resultHeader">
                        <span className="resultNum">#{idx + 1}</span>
                        <span className="resultName">
                          {result.original_name}
                        </span>
                        <span className="resultStatus">
                          {result.success ? "✅" : "❌"}
                        </span>
                      </div>

                      {result.success ? (
                        <div className="resultContent">
                          <img
                            src={`${result.result_url}?t=${Date.now()}`}
                            alt={`Result ${idx + 1}`}
                            className="resultImg"
                            loading="lazy"
                          />
                          <div className="resultActions">
                            <a
                              className="btnSmall"
                              href={result.result_url}
                              download={result.filename}
                            >
                              ⬇️ Download
                            </a>
                            <a
                              className="btnSmall secondary"
                              href={result.result_url}
                              target="_blank"
                              rel="noreferrer"
                            >
                              🔍 Open
                            </a>
                          </div>
                        </div>
                      ) : (
                        <div className="resultError">
                          <div className="errorMsg">
                            {result.error || "Processing failed"}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      <footer className="foot">
        {jobStatus?.status === "completed" && (
          <div>
            🎉 Processing terminé ! {successCount}/{totalCount} images traitées
            avec succès
          </div>
        )}
      </footer>
    </div>
  );
}