from fastapi import FastAPI, UploadFile, File, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import sys
import shutil
import os

# Absolute base path — works from any directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(title="Smart Attendance System")

templates = Jinja2Templates(
    directory=os.path.join(BASE_DIR, "app", "frontend", "templates")
)
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "app", "frontend", "static")),
    name="static"
)


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
    file_path = os.path.join(BASE_DIR, "data", "attendance", today, "attendance.xlsx")

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
    dataset_path = os.path.join(BASE_DIR, "data", "datasets")

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
# Current lecture / slot info  (for dashboard banner)
# ──────────────────────────────────────────────
@app.get("/current-lecture")
def current_lecture():
    from app.attendance.attendance_services import get_current_lecture_and_slot
    lecture, slot, subject = get_current_lecture_and_slot()
    return {"lecture": lecture, "slot": slot, "subject": subject}


# ──────────────────────────────────────────────
# Live recognition  (runs in background)
# ──────────────────────────────────────────────
def _run_live():
    import subprocess
    subprocess.Popen(
        [sys.executable, "-m", "scripts.recognize_live"],
        cwd=BASE_DIR
    )

@app.post("/recognize-live")
def recognize_live(background_tasks: BackgroundTasks):
    background_tasks.add_task(_run_live)
    return {"status": "Live recognition started for 60 seconds"}


# ──────────────────────────────────────────────
# Upload CCTV video  (saves file, then processes it)
# ──────────────────────────────────────────────
def _process_video(video_path: str):
    import subprocess
    subprocess.Popen(
        [sys.executable, "-m", "scripts.process_cctv_video", video_path],
        cwd=BASE_DIR
    )

@app.post("/upload-video")
async def upload_video(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    video_dir  = os.path.join(BASE_DIR, "data", "video")
    os.makedirs(video_dir, exist_ok=True)
    video_path = os.path.join(video_dir, file.filename)

    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    background_tasks.add_task(_process_video, video_path)
    return JSONResponse({"status": f"Video '{file.filename}' uploaded. Processing started."})