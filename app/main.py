from fastapi import FastAPI, UploadFile, File, Request, BackgroundTasks, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from scripts.process_image import process_image_function

import sys, shutil, os, io
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(title="Smart Attendance System")
app.add_middleware(SessionMiddleware, secret_key="fcrit_smartattendance_2026")

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "app", "frontend", "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "app", "frontend", "static")), name="static")

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "attendance2026"

@app.on_event("startup")
def startup():
    from app.database.db import init_db
    init_db()

def is_logged_in(request: Request) -> bool:
    return request.session.get("authenticated") is True

# ── Login ──────────────────────────────────────────────────────────────────────
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if is_logged_in(request):
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login", response_class=HTMLResponse)
async def login_submit(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        request.session["authenticated"] = True
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid username or password"})

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)

# ── Dashboard ──────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    if not is_logged_in(request):
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse("dashboard.html", {"request": request})

# ── Attendance API ─────────────────────────────────────────────────────────────
@app.get("/attendance")
def get_attendance(request: Request, date: str = None):
    if not is_logged_in(request):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    from app.database.db import SessionLocal
    from app.database.models import AttendanceRecord
    target_date = date or datetime.now().strftime("%Y-%m-%d")
    db = SessionLocal()
    try:
        records = db.query(AttendanceRecord).filter_by(date=target_date).all()
        return [{"Roll No":r.roll_no,"Name":r.name,"Date":r.date,"Time":r.time,
                 "Lecture":r.lecture,"Slot":r.slot,"Subject":r.subject} for r in records]
    except Exception as e:
        print(f"[attendance] {e}"); return []
    finally:
        db.close()

# ── Export Excel ───────────────────────────────────────────────────────────────
@app.get("/export")
def export_attendance(request: Request, date: str = None):
    if not is_logged_in(request):
        return RedirectResponse("/login", status_code=302)
    import pandas as pd
    from app.database.db import SessionLocal
    from app.database.models import AttendanceRecord
    target_date = date or datetime.now().strftime("%Y-%m-%d")
    db = SessionLocal()
    try:
        records = db.query(AttendanceRecord).filter_by(date=target_date).all()
        data = [{"Roll No":r.roll_no,"Name":r.name,"Date":r.date,"Time":r.time,
                 "Lecture":r.lecture,"Slot":r.slot,"Subject":r.subject} for r in records]
    finally:
        db.close()
    df = pd.DataFrame(data) if data else pd.DataFrame(
        columns=["Roll No","Name","Date","Time","Lecture","Slot","Subject"])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Attendance")
        ws = writer.sheets["Attendance"]
        for col in ws.columns:
            max_len = max((len(str(c.value or "")) for c in col), default=10)
            ws.column_dimensions[col[0].column_letter].width = max_len + 4
    output.seek(0)
    return StreamingResponse(output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=attendance_{target_date}.xlsx"})

# ── Students ───────────────────────────────────────────────────────────────────
@app.get("/students")
def get_students():
    dataset_path = os.path.join(BASE_DIR, "data", "datasets")
    try:
        students = [n for n in os.listdir(dataset_path) if os.path.isdir(os.path.join(dataset_path, n))]
        return {"total_students": len(students), "students": students}
    except Exception as e:
        print(f"[students] {e}"); return {"total_students": 0, "students": []}

# ── Current lecture ────────────────────────────────────────────────────────────
@app.get("/current-lecture")
def current_lecture():
    from app.attendance.attendance_services import get_current_lecture_and_slot
    lecture, slot, subject = get_current_lecture_and_slot()
    return {"lecture": lecture, "slot": slot, "subject": subject}

# ── Live recognition ───────────────────────────────────────────────────────────
def _run_live():
    import subprocess
    subprocess.Popen([sys.executable, "-m", "scripts.recognize_live"], cwd=BASE_DIR)

@app.post("/recognize-live")
def recognize_live(request: Request, background_tasks: BackgroundTasks):
    if not is_logged_in(request):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    background_tasks.add_task(_run_live)
    return {"status": "Live recognition started for 60 seconds"}

# ── Upload CCTV video ──────────────────────────────────────────────────────────
def _process_video(video_path: str):
    import subprocess
    subprocess.Popen([sys.executable, "-m", "scripts.process_cctv_video", video_path], cwd=BASE_DIR)

@app.post("/upload-video")
async def upload_video(request: Request, background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not is_logged_in(request):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    video_dir = os.path.join(BASE_DIR, "data", "video")
    os.makedirs(video_dir, exist_ok=True)
    video_path = os.path.join(video_dir, file.filename)
    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    background_tasks.add_task(_process_video, video_path)
    return JSONResponse({"status": f"Video '{file.filename}' uploaded. Processing started."})

# ── Upload classroom image ─────────────────────────────────────────────────────

@app.post("/upload-image")
async def upload_image(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):

    if not is_logged_in(request):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}:
        return JSONResponse({"status": "❌ Invalid file type"}, status_code=400)

    image_dir = os.path.join(BASE_DIR, "data", "images")
    os.makedirs(image_dir, exist_ok=True)

    image_path = os.path.join(image_dir, file.filename)

    with open(image_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    print(f"🖼️ Queued image: {image_path}")

    # 🔥 RUN IN BACKGROUND (FIX)
    background_tasks.add_task(process_image_function, image_path)

    return JSONResponse({"status": f"⏳ Processing started for '{file.filename}'"})