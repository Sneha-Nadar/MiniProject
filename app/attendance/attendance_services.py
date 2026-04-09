import pandas as pd
import os
from datetime import datetime

def get_today_folder():
    today = datetime.now().strftime("%Y-%m-%d")
    folder_path = os.path.join("data", "attendance", today)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

def get_current_lecture_and_slot():
    """
    Returns (lecture_label, slot, subject) based on current time.
    Slot A = first 30 min of lecture, Slot B = last 30 min.
    """
    now = datetime.now()
    day = now.strftime("%A")  # Monday, Tuesday...
    t = now.time()

    # Timetable: (lecture, start, end, {day: subject})
    lectures = [
        ("L1", "08:45", "09:45"),
        ("L2", "09:45", "10:45"),
        ("L3", "11:00", "12:00"),
        ("L4", "12:00", "13:00"),
        ("L5", "13:30", "14:30"),
        ("L6", "14:30", "15:30"),
        ("L7", "15:30", "16:30"),
    ]

    # Subject timetable from your image
    timetable = {
        "Monday":    {"L1": "NL/LL/FSDL", "L2": "FSDL",     "L3": "FSD(AP)", "L4": "FSD(AP)", "L5": "MP-1B", "L6": "MP-1B", "L7": "MP-1B"},
        "Tuesday":   {"L1": "SDL/NL/FSDL","L2": "FSDL",     "L3": "CN",      "L4": "SE",      "L5": "EM-IV", "L6": "E&S(AP)","L7": "MES"},
        "Wednesday": {"L1": "OS",         "L2": "EM-IV",     "L3": "FSDL/LL/SDL","L4":"FSDL/LL/SDL","L5":"E&S(AP)","L6":"TT","L7":"TT"},
        "Thursday":  {"L1": "EM-IV(T)",   "L2": "EM-IV",     "L3": "OS",      "L4": "SE",      "L5": "CN",    "L6": "MES",   "L7": "R"},
        "Friday":    {"L1": "MES",        "L2": "CN",        "L3": "OS",      "L4": "SE",      "L5": "LL/NL/SDL","L6":"LL/NL/SDL","L7":"R"},
        "Saturday":  {"L1": "R",          "L2": "R"},
    }

    for lecture, start, end in lectures:
        start_t = datetime.strptime(start, "%H:%M").time()
        end_t   = datetime.strptime(end,   "%H:%M").time()

        if start_t <= t <= end_t:
            # Calculate slot: A = first 30 min, B = second 30 min
            start_dt = datetime.combine(now.date(), start_t)
            elapsed  = (now - start_dt).seconds // 60
            slot     = "A" if elapsed < 30 else "B"

            subject = timetable.get(day, {}).get(lecture, "Unknown")
            return lecture, slot, subject

    return "Extra", "A", "Unknown"


def mark_attendance(full_name):
    """
    full_name is like '5024101_Rajiv Agarwal'
    Parses roll number and actual name from folder convention.
    """
    folder = get_today_folder()
    file_path = os.path.join(folder, "attendance.xlsx")

    lecture, slot, subject = get_current_lecture_and_slot()

    # Parse roll number and name from folder convention
    parts = full_name.split("_", 1)
    roll_no = parts[0] if len(parts) == 2 else "Unknown"
    name    = parts[1] if len(parts) == 2 else full_name

    now  = datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")

    if os.path.exists(file_path):
        df = pd.read_excel(file_path)
    else:
        df = pd.DataFrame(columns=["Roll No", "Name", "Date", "Time", "Lecture", "Slot", "Subject"])

    # Duplicate check: same person, same lecture, same slot
    already_marked = (
        (df["Roll No"] == roll_no) &
        (df["Lecture"] == lecture) &
        (df["Slot"]    == slot)
    ).any()

    if already_marked:
        return

    new_row = {
        "Roll No": roll_no,
        "Name":    name,
        "Date":    date,
        "Time":    time,
        "Lecture": lecture,
        "Slot":    slot,
        "Subject": subject,
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_excel(file_path, index=False)
    print(f"✅ Attendance: {name} | {lecture}-{slot} | {subject}")