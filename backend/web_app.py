import os
import time
import asyncio
import threading
import uuid
import json
import shutil
from datetime import datetime
from typing import List

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# ── Import de notre session persistante ──────────────────────────────────────
from gemini_process import GeminiSession

# ══════════════════════════════════════════════════════════════════════════════
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Répertoires ───────────────────────────────────────────────────────────────
UPLOADS_DIR   = "/data/uploads"
DOWNLOADS_DIR = "/data/downloads"
JOBS_DIR      = "/data/jobs"

os.makedirs(UPLOADS_DIR,   exist_ok=True)
os.makedirs(DOWNLOADS_DIR, exist_ok=True)
os.makedirs(JOBS_DIR,      exist_ok=True)

# ── Jobs en mémoire ──────────────────────────────────────────────────────────
jobs: dict = {}


# ══════════════════════════════════════════════════════════════════════════════
# PERSISTANCE JOB SUR DISQUE
# ══════════════════════════════════════════════════════════════════════════════
def save_job_to_disk(job_id: str):
    job_file = os.path.join(JOBS_DIR, f"{job_id}.json")
    with open(job_file, "w") as f:
        json.dump(jobs[job_id], f, indent=2)


# ══════════════════════════════════════════════════════════════════════════════
# BOUCLE BATCH — UN SEUL NAVIGATEUR POUR TOUTES LES IMAGES
# ══════════════════════════════════════════════════════════════════════════════
async def run_batch_async(job_id: str):
    """
    Fonction principale du batch.
    1) Crée une GeminiSession (lance Chrome UNE fois).
    2) Loop sur chaque image → session.process_image().
    3) Ferme Chrome à la fin.
    """
    job = jobs[job_id]
    job["status"]     = "processing"
    job["started_at"] = datetime.now().isoformat()
    save_job_to_disk(job_id)

    session = GeminiSession()

    try:
        # ── Lance le navigateur (une seule fois) ──────────────────────────
        await session.start()

        # ── Traite chaque image dans la MÊME session ─────────────────────
        for idx, img_info in enumerate(job["images"]):
            image_path   = img_info["path"]
            original_name = img_info["original_name"]
            total        = job["total"]

            # Update statut
            job["current"] = idx + 1
            job["status"]  = f"Processing image {idx + 1}/{total}..."
            save_job_to_disk(job_id)

            print(f"\n{'=' * 60}")
            print(f"🎯 Processing image {idx + 1}/{total}")
            print(f"📁 File: {original_name}")
            print(f"{'=' * 60}\n")

            # ── Appel à la session (Chrome reste ouvert) ───────────────
            result = await session.process_image(image_path)

            # ── Construire l'info de résultat ─────────────────────────
            result_info = {
                "index":         idx,
                "original_name": original_name,
                "success":       result["success"],
                "result_url":    None,
                "filename":      None,
                "error":         result.get("error"),
            }

            if result["success"] and result["result_path"]:
                filename = os.path.basename(result["result_path"])
                result_info["result_url"] = f"/downloads/{filename}"
                result_info["filename"]   = filename
                print(f"✅ Image {idx + 1}/{total} processed successfully!")
            else:
                print(f"❌ Image {idx + 1}/{total} failed: {result.get('error')}")

            job["results"].append(result_info)
            save_job_to_disk(job_id)

        # ── Fin du batch ──────────────────────────────────────────────────
        job["status"]       = "completed"
        job["completed_at"] = datetime.now().isoformat()
        save_job_to_disk(job_id)

        success = sum(1 for r in job["results"] if r["success"])
        print(f"\n🎉 Job {job_id} completed! ✅ {success}/{job['total']} succeeded")

    except Exception as e:
        print(f"\n💥 Job {job_id} crashed: {e}")
        job["status"]       = "failed"
        job["completed_at"] = datetime.now().isoformat()
        job["error"]        = str(e)
        save_job_to_disk(job_id)

    finally:
        # ── Ferme Chrome (UNE seule fois, à la fin) ─────────────────────
        await session.close()


def run_batch_in_thread(job_id: str):
    """Wrapper pour exécuter la coroutine async dans un thread séparé."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_batch_async(job_id))
    finally:
        loop.close()


# ══════════════════════════════════════════════════════════════════════════════
# ROUTES FASTAPI
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/")
def health():
    return {"ok": True, "service": "Gemini Product Studio Backend (Persistent Session)"}


# ── Upload batch ──────────────────────────────────────────────────────────────
@app.post("/upload-batch")
async def upload_batch(files: List[UploadFile] = File(...)):
    if not files:
        return JSONResponse({"ok": False, "error": "No files provided"}, status_code=400)

    job_id = f"job_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    uploaded_files = []

    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in (".jpg", ".jpeg", ".png", ".webp"):
            ext = ".jpg"

        filename  = f"{int(time.time())}_{uuid.uuid4().hex[:8]}{ext}"
        save_path = os.path.join(UPLOADS_DIR, filename)

        content = await file.read()
        with open(save_path, "wb") as f:
            f.write(content)

        uploaded_files.append({
            "path":          save_path,
            "original_name": file.filename,
            "size":          len(content),
        })
        print(f"✅ Uploaded: {file.filename} ({len(content)} bytes)")

    jobs[job_id] = {
        "id":           job_id,
        "status":       "pending",
        "total":        len(uploaded_files),
        "current":      0,
        "images":       uploaded_files,
        "results":      [],
        "created_at":   datetime.now().isoformat(),
        "started_at":   None,
        "completed_at": None,
    }
    save_job_to_disk(job_id)

    return {
        "ok":           True,
        "job_id":       job_id,
        "total_images": len(uploaded_files),
        "message":      f"Uploaded {len(uploaded_files)} image(s)",
    }


# ── Start batch ───────────────────────────────────────────────────────────────
@app.post("/run-batch/{job_id}")
def run_batch(job_id: str):
    if job_id not in jobs:
        return JSONResponse({"ok": False, "error": "Job not found"}, status_code=404)

    job = jobs[job_id]
    if job["status"] == "processing":
        return JSONResponse({"ok": False, "error": "Job already running"}, status_code=400)

    # Lance le batch dans un thread (pour ne pas bloquer FastAPI)
    thread = threading.Thread(target=run_batch_in_thread, args=(job_id,), daemon=True)
    thread.start()

    return {"ok": True, "job_id": job_id, "message": "Processing started"}


# ── Polling du statut ─────────────────────────────────────────────────────────
@app.get("/job/{job_id}")
def get_job_status(job_id: str):
    if job_id not in jobs:
        # Essai depuis le disque (ex : après redémarrage du serveur)
        job_file = os.path.join(JOBS_DIR, f"{job_id}.json")
        if os.path.exists(job_file):
            with open(job_file) as f:
                jobs[job_id] = json.load(f)
        else:
            return JSONResponse({"ok": False, "error": "Job not found"}, status_code=404)

    job = jobs[job_id]
    total     = job["total"]
    completed = len(job["results"])
    success   = sum(1 for r in job["results"] if r["success"])

    return {
        "ok":              True,
        "job_id":          job_id,
        "status":          job["status"],
        "total":           total,
        "current":         job["current"],
        "completed":       completed,
        "success":         success,
        "failed":          completed - success,
        "progress_percent": int((completed / total * 100) if total > 0 else 0),
        "results":         job["results"],
        "created_at":      job.get("created_at"),
        "started_at":      job.get("started_at"),
        "completed_at":    job.get("completed_at"),
    }


# ── Download résultat ─────────────────────────────────────────────────────────
@app.get("/downloads/{filename}")
def get_download(filename: str):
    path = os.path.join(DOWNLOADS_DIR, filename)
    if not os.path.exists(path):
        return JSONResponse({"detail": f"File not found: {filename}"}, status_code=404)
    return FileResponse(path, media_type="image/jpeg", headers={"Cache-Control": "no-cache"})


# ── Liste des jobs ────────────────────────────────────────────────────────────
@app.get("/jobs")
def list_jobs():
    return {"ok": True, "jobs": list(jobs.values())}