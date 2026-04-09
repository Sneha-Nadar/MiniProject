from fastapi import FastAPI, UploadFile, File, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import sys
import shutil
import os

app = FastAPI(title="Smart Attendance System")

templates = Jinja2Templates(directory="app/frontend/templates")
app.mount("/static", StaticFiles(directory="app/frontend/static"), name="static")


# ──────────────────────────────────────────────
# Dashboard
# ──────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


# ──────────────────────────────────────────────
# Attendance  (today's file, all columns)
# ──────────────────────────────────────────────
@app.get("/attendance")
def get_attendance():
    from datetime import datetime
    import pandas as pd

    today     = datetime.now().strftime("%Y-%m-%d")
    file_path = f"data/attendance/{today}/attendance.xlsx"

    try:
        if not os.path.exists(file_path):
            return []
        df = pd.read_excel(file_path)
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"[attendance] Error: {e}")
        return []


# ──────────────────────────────────────────────
# Student count
# ──────────────────────────────────────────────
@app.get("/students")
def get_students():
    dataset_path = "data/datasets"
    try:
        students = [
            name for name in os.listdir(dataset_path)
            if os.path.isdir(os.path.join(dataset_path, name))
        ]
        return {"total_students": len(students), "students": students}
    except Exception as e:
        print(f"[students] Error: {e}")
        return {"total_students": 0, "students": []}


# ──────────────────────────────────────────────
# Current lecture / slot info  (for dashboard)
# ──────────────────────────────────────────────
@app.get("/current-lecture")
def current_lecture():
    from app.attendance.attendance_services import get_current_lecture_and_slot
    lecture, slot, subject = get_current_lecture_and_slot()
    return {"lecture": lecture, "slot": slot, "subject": subject}


# ──────────────────────────────────────────────
# Live recognition  (runs in background thread)
# ──────────────────────────────────────────────
def _run_live():
    """Background task — runs recognize_live session."""
    import subprocess
    subprocess.Popen([sys.executable, "-m", "scripts.recognize_live"])

@app.post("/recognize-live")
def recognize_live(background_tasks: BackgroundTasks):
    background_tasks.add_task(_run_live)
    return {"status": "Live recognition started for 60 seconds"}


# ──────────────────────────────────────────────
# Upload CCTV video  (saves file, then processes)
# ──────────────────────────────────────────────
def _process_video(video_path: str):
    """Background task — processes a specific video file."""
    import subprocess
    subprocess.Popen([sys.executable, "-m", "scripts.process_cctv_video", video_path])

@app.post("/upload-video")
async def upload_video(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    os.makedirs("data/video", exist_ok=True)
    video_path = f"data/video/{file.filename}"

    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    background_tasks.add_task(_process_video, video_path)
    return JSONResponse({"status": f"Video '{file.filename}' uploaded. Processing started."})