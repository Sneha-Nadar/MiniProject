from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# =========================
# 🔷 TIMETABLE CONFIG
# =========================

LECTURES = [
    ("L1","08:45","09:45"),
    ("L2","09:45","10:45"),
    ("L3","11:00","12:00"),
    ("L4","12:00","13:00"),
    ("L5","13:30","14:30"),
    ("L6","14:30","15:30"),
    ("L7","15:30","16:30"),
]

TIMETABLE = {
    "Monday":    {"L1":"NL/LL/FSDL","L2":"FSDL",     "L3":"FSD(AP)","L4":"FSD(AP)","L5":"MP-1B",    "L6":"MP-1B",    "L7":"MP-1B"},
    "Tuesday":   {"L1":"SDL/NL/FSDL","L2":"FSDL",    "L3":"CN",     "L4":"SE",     "L5":"EM-IV",    "L6":"E&S(AP)", "L7":"MES"},
    "Wednesday": {"L1":"OS",         "L2":"EM-IV",    "L3":"FSDL/LL","L4":"FSDL/LL","L5":"E&S(AP)", "L6":"TT",      "L7":"TT"},
    "Thursday":  {"L1":"EM-IV(T)",   "L2":"EM-IV",    "L3":"OS",     "L4":"SE",     "L5":"CN",       "L6":"MES",     "L7":"R"},
    "Friday":    {"L1":"MES",        "L2":"CN",       "L3":"OS",     "L4":"SE",     "L5":"LL/NL/SDL","L6":"LL/NL/SDL","L7":"R"},
    "Saturday":  {"L1":"R",          "L2":"R"},
}

# =========================
# 🔷 EMAIL CONFIG
# =========================

GMAIL_USER = "your_email@gmail.com"
GMAIL_PASS = "your_app_password"   # Use App Password

def send_defaulter_alert(student_name, roll_no, subject, percentage):
    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = f"{roll_no}@student.fcrit.ac.in"
    msg['Subject'] = f"Attendance Warning — {subject}"

    body = f"""
Dear {student_name},

This is an automated attendance alert from CognifAce — Smart Attendance System.

Your attendance in {subject} is {percentage}%.

Minimum required attendance is 75%.
Please attend regularly.

Regards,
IT Department, FCRIT
"""
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(GMAIL_USER, GMAIL_PASS)
            smtp.send_message(msg)
        print(f"⚠️ Alert sent to {student_name}")
    except Exception as e:
        print(f"[email] Error: {e}")

# =========================
# 🔷 LECTURE + SLOT LOGIC
# =========================

def get_current_lecture_and_slot():
    now = datetime.now()
    day = now.strftime("%A")
    t   = now.time()

    # Normal lectures
    for lecture, start, end in LECTURES:
        start_t = datetime.strptime(start, "%H:%M").time()
        end_t   = datetime.strptime(end, "%H:%M").time()

        if start_t <= t <= end_t:
            start_dt = datetime.combine(now.date(), start_t)
            elapsed  = (now - start_dt).seconds // 60
            slot     = "A" if elapsed < 30 else "B"
            subject  = TIMETABLE.get(day, {}).get(lecture, "Unknown")
            return lecture, slot, subject

    # Extra lecture logic
    last_end_time = datetime.strptime(LECTURES[-1][2], "%H:%M").time()
    extra_start_dt = datetime.combine(now.date(), last_end_time)

    elapsed = (now - extra_start_dt).seconds // 60
    slot = "A" if elapsed < 30 else "B"

    return "Extra", slot, "Extra Session"

# =========================
# 🔷 ATTENDANCE MARKING
# =========================

def mark_attendance(full_name: str):
    from app.database.db import SessionLocal
    from app.database.models import AttendanceRecord

    parts   = full_name.split("_", 1)
    roll_no = parts[0] if len(parts) == 2 else "Unknown"
    name    = parts[1] if len(parts) == 2 else full_name

    lecture, slot, subject = get_current_lecture_and_slot()

    now  = datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")

    db = SessionLocal()

    try:
        # Prevent duplicate entry
        exists = db.query(AttendanceRecord).filter_by(
            roll_no=roll_no,
            date=date,
            lecture=lecture,
            slot=slot
        ).first()

        if exists:
            return

        # Add attendance
        db.add(AttendanceRecord(
            roll_no=roll_no,
            name=name,
            date=date,
            time=time,
            lecture=lecture,
            slot=slot,
            subject=subject
        ))
        db.commit()

        print(f"✅ {name} | {lecture}-{slot} | {subject}")

        # =========================
        # 🔥 DEFaULTER CHECK (HOOK)
        # =========================

        percentage = 70  # 🔥 Replace with real calculation later

        if percentage < 75:
            send_defaulter_alert(name, roll_no, subject, percentage)

    except Exception as e:
        db.rollback()
        print(f"[mark_attendance] Error: {e}")

    finally:
        db.close()