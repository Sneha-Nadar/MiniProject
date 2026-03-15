from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
import subprocess
import shutil
import pandas as pd

app = FastAPI()

templates = Jinja2Templates(directory="app/frontend/templates")

app.mount("/static", StaticFiles(directory="app/frontend/static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/attendance")
def get_attendance():
    try:
        df = pd.read_excel("attendance.xlsx")
        return df.to_dict(orient="records")
    except:
        return []


@app.post("/recognize-live")
def recognize_live():

    subprocess.Popen(["python", "-m", "scripts.recognize_live"])

    return {"status": "started"}


@app.post("/upload-video")
async def upload_video(file: UploadFile = File(...)):

    path = f"data/videos/{file.filename}"

    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    subprocess.Popen(["python", "-m", "scripts.process_cctv_video"])

    return {"status": "processing"}