import os
import glob
import time
import subprocess
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import shutil

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOADS_DIR = "/data/uploads"
DOWNLOADS_DIR = "/data/downloads"
IMAGE_PATH = "/data/current_input.jpg"

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

@app.get("/")
def health():
    return {"ok": True, "service": "Gemini Product Studio Backend"}

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
        ext = ".jpg"

    filename = f"{int(time.time())}_{uuid.uuid4().hex}{ext}"
    save_path = os.path.join(UPLOADS_DIR, filename)

    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    # Copier vers IMAGE_PATH
    shutil.copyfile(save_path, IMAGE_PATH)

    with open("/data/last_upload.txt", "w") as m:
        m.write(save_path)

    print(f"✅ Image uploaded: {filename} ({len(content)} bytes)")
    
    return {
        "ok": True,
        "saved_to": save_path,
        "filename": filename,
        "size": len(content)
    }

@app.post("/run")
def run_script():
    # 🔪 Tuer tous les processus Chrome/Chromium
    print("🔪 Killing existing Chrome processes...")
    try:
        subprocess.run(["pkill", "-9", "chrome"], check=False, 
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["pkill", "-9", "chromium"], check=False,
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
    except:
        pass

    # 🧹 Nettoyer les locks
    lock_files = [
        "/data/user_data/SingletonLock",
        "/data/user_data/SingletonSocket",
        "/data/user_data/SingletonCookie",
    ]
    for lock_file in lock_files:
        try:
            if os.path.exists(lock_file):
                os.remove(lock_file)
                print(f"🧹 Removed: {lock_file}")
        except:
            pass
    
    if not os.path.exists(IMAGE_PATH):
        return JSONResponse({
            "ok": False,
            "logs": "❌ Aucune image trouvée. Uploadez d'abord une image."
        })

    print("🚀 Starting Gemini process...")
    
    before = set(glob.glob(os.path.join(DOWNLOADS_DIR, "result_*.*")))
    start_ts = time.time()

    p = subprocess.Popen(
        ["python3", "gemini_process.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        cwd="/app"
    )

    logs = []
    timeout_sec = 15 * 60

    while True:
        line = p.stdout.readline() if p.stdout else ""
        if line:
            log_line = line.rstrip()
            logs.append(log_line)
            print(log_line)

        if p.poll() is not None:
            break

        if time.time() - start_ts > timeout_sec:
            p.kill()
            logs.append("⏱️ ERROR: Timeout atteint, processus arrêté.")
            break

    out = "\n".join(logs)

    after = set(glob.glob(os.path.join(DOWNLOADS_DIR, "result_*.*")))
    new_files = list(after - before)
    new_files = [f for f in new_files if os.path.getmtime(f) >= start_ts - 1]

    if new_files:
        new_files.sort(key=os.path.getmtime, reverse=True)
        result = new_files[0]
        name = os.path.basename(result)
        
        print(f"✅ Résultat trouvé: {name}")
        
        return JSONResponse({
            "ok": True,
            "download_url": f"/downloads/{name}",
            "filename": name,
            "logs": out
        })

    print("❌ Aucun fichier résultat trouvé")
    return JSONResponse({
        "ok": False,
        "logs": out or "❌ Le script n'a produit aucun résultat."
    })

@app.get("/downloads/{filename}")
def get_download(filename: str):
    path = os.path.join(DOWNLOADS_DIR, filename)
    
    if not os.path.exists(path):
        return JSONResponse(
            {"detail": f"Fichier non trouvé: {filename}"},
            status_code=404
        )
    
    return FileResponse(
        path,
        media_type="image/jpeg",
        headers={"Cache-Control": "no-cache"}
    )