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
# ── STUDENT PORTAL ─────────────────────────────────────────────────────────────

# Default student password (change this or make per-student later)
STUDENT_PASSWORD = "fcrit2026"

@app.get("/student/login", response_class=HTMLResponse)
async def student_login_page(request: Request):
    if request.session.get("student_roll"):
        return RedirectResponse("/student", status_code=302)
    return templates.TemplateResponse("student_login.html",
                                      {"request": request, "error": None})

@app.post("/student/login", response_class=HTMLResponse)
async def student_login_submit(request: Request,
                                roll_no: str = Form(...),
                                password: str = Form(...)):
    # Validate roll number exists in dataset
    dataset_path = os.path.join(BASE_DIR, "data", "datasets")
    students = [n for n in os.listdir(dataset_path)
                if os.path.isdir(os.path.join(dataset_path, n))]
    matched = [s for s in students if s.startswith(roll_no + "_")]

    if not matched or password != STUDENT_PASSWORD:
        return templates.TemplateResponse("student_login.html",
            {"request": request, "error": "Invalid Roll Number or Password"})

    folder_name = matched[0]
    name = folder_name.split("_", 1)[1]
    request.session["student_roll"] = roll_no
    request.session["student_name"] = name
    return RedirectResponse("/student", status_code=302)

@app.get("/student", response_class=HTMLResponse)
async def student_portal(request: Request):
    if not request.session.get("student_roll"):
        return RedirectResponse("/student/login", status_code=302)
    return templates.TemplateResponse("student.html", {"request": request})

@app.get("/student/logout")
async def student_logout(request: Request):
    request.session.pop("student_roll", None)
    request.session.pop("student_name", None)
    return RedirectResponse("/student/login", status_code=302)

@app.get("/student/dashboard")
def student_dashboard(request: Request):
    if not request.session.get("student_roll"):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    from app.database.db import SessionLocal
    from app.database.models import AttendanceRecord
    from collections import defaultdict

    roll_no = request.session["student_roll"]
    name    = request.session["student_name"]

    db = SessionLocal()
    try:
        records = db.query(AttendanceRecord).filter_by(roll_no=roll_no).all()

        # Count per subject
        subject_counts = defaultdict(lambda: {"attended": 0, "total": 0})

        # Total slots per subject (estimate from timetable — 2 slots per lecture)
        # You can hardcode total expected lectures per subject here
        all_subjects = set(r.subject for r in records)
        for subj in all_subjects:
            subj_records = [r for r in records if r.subject == subj]
            subject_counts[subj]["attended"] = len(subj_records)
            # Total = unique (date, lecture) pairs × 2 slots
            unique_lectures = len(set((r.date, r.lecture) for r in subj_records))
            # Approximate total conducted = attended (since we only have marked data)
            # For real total, you'd track total conducted separately
            subject_counts[subj]["total"] = max(len(subj_records), unique_lectures * 2)

        subject_wise = {}
        for subj, counts in subject_counts.items():
            pct = round((counts["attended"] / counts["total"] * 100)
                        if counts["total"] > 0 else 0, 1)
            subject_wise[subj] = {
                "attended":   counts["attended"],
                "total":      counts["total"],
                "percentage": pct
            }

        total_attended = len(records)
        total_slots    = sum(v["total"] for v in subject_wise.values())
        overall_pct    = round((total_attended / total_slots * 100)
                               if total_slots > 0 else 0, 1)

        return {
            "roll_no":            roll_no,
            "name":               name,
            "total_attended":     total_attended,
            "overall_percentage": overall_pct,
            "subject_wise":       subject_wise
        }
    finally:
        db.close()

@app.get("/student/records")
def student_records(request: Request, month: str = None):
    if not request.session.get("student_roll"):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    from app.database.db import SessionLocal
    from app.database.models import AttendanceRecord

    roll_no = request.session["student_roll"]
    db = SessionLocal()
    try:
        query = db.query(AttendanceRecord).filter_by(roll_no=roll_no)
        if month:  # format: "2026-03"
            query = query.filter(AttendanceRecord.date.like(f"{month}%"))
        records = query.order_by(AttendanceRecord.date.desc()).all()
        return [{"date": r.date, "time": r.time, "lecture": r.lecture,
                 "slot": r.slot, "subject": r.subject} for r in records]
    finally:
        db.close()
@app.get("/admin/defaulters")
def get_defaulters(request: Request):
    if not is_logged_in(request):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    from app.database.db import SessionLocal
    from app.database.models import AttendanceRecord
    from collections import defaultdict

    db = SessionLocal()
    try:
        all_records = db.query(AttendanceRecord).all()

        # Group by roll_no + subject
        data = defaultdict(lambda: defaultdict(int))
        names = {}
        for r in all_records:
            data[r.roll_no][r.subject] += 1
            names[r.roll_no] = r.name

        defaulters = []
        for roll_no, subjects in data.items():
            for subject, attended in subjects.items():
                # Approximate total = attended * (1/expected_rate)
                # For now flag anyone below 75% of their own max
                total = max(attended, 20)  # assume min 20 slots per subject
                pct = round(attended / total * 100, 1)
                if pct < 75:
                    defaulters.append({
                        "roll_no":    roll_no,
                        "name":       names[roll_no],
                        "subject":    subject,
                        "attended":   attended,
                        "percentage": pct
                    })

        return sorted(defaulters, key=lambda x: x["percentage"])
    finally:
        db.close()