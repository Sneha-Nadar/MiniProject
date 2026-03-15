from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import subprocess
import shutil
import pandas as pd
import os


app = FastAPI(title="Smart Attendance System")


# -----------------------------
# Frontend Templates
# -----------------------------
templates = Jinja2Templates(directory="app/frontend/templates")


# -----------------------------
# Static Files (CSS / JS)
# -----------------------------
app.mount("/static", StaticFiles(directory="app/frontend/static"), name="static")


# -----------------------------
# Dashboard Route
# -----------------------------
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):

    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request}
    )


# -----------------------------
# Attendance API
# -----------------------------
@app.get("/attendance")
def get_attendance():

    try:

        df = pd.read_excel("attendance.xlsx")

        return df.to_dict(orient="records")

    except:

        return []


# -----------------------------
# Student Stats API
# -----------------------------
@app.get("/students")
def get_students():

    dataset_path = "data/datasets"

    students = [
        name for name in os.listdir(dataset_path)
        if os.path.isdir(os.path.join(dataset_path, name))
    ]

    return {
        "total_students": len(students),
        "students": students
    }


# -----------------------------
# Start Live Recognition
# -----------------------------
import sys

@app.post("/recognize-live")
def recognize_live():

    subprocess.Popen(
        [sys.executable, "-m", "scripts.recognize_live"]
    )

    return {"status": "Live recognition started"}


# -----------------------------
# Upload CCTV Video
# -----------------------------
@app.post("/upload-video")
async def upload_video(file: UploadFile = File(...)):

    os.makedirs("data/videos", exist_ok=True)

    video_path = f"data/videos/{file.filename}"

    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    subprocess.Popen(
        ["python", "-m", "scripts.process_cctv_video"]
    )

    return JSONResponse(
        {"status": "Video uploaded and processing started"}
    )