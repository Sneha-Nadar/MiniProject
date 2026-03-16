import pandas as pd
import os
from datetime import datetime


def get_today_folder():
    
    today = datetime.now().strftime("%Y-%m-%d")

    folder_path = os.path.join("data", "attendance", today)

    os.makedirs(folder_path, exist_ok=True)

    return folder_path


def get_current_lecture():

    now = datetime.now().time()

    lectures = [
        ("L1","08:30","09:30"),
        ("L2","09:30","10:30"),
        ("L3","10:30","11:30"),
        ("L4","11:30","12:30"),
        ("L5","01:30","02:30"),
        ("L6","02:30","03:30"),
        ("L7","03:30","04:30")
    ]

    for lecture,start,end in lectures:

        start = datetime.strptime(start,"%H:%M").time()
        end = datetime.strptime(end,"%H:%M").time()

        if start <= now <= end:
            return lecture

    return "Extra"


def mark_attendance(name):

    folder = get_today_folder()

    file_path = os.path.join(folder,"attendance.xlsx")

    lecture = get_current_lecture()

    now = datetime.now()

    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")

    if os.path.exists(file_path):
        df = pd.read_excel(file_path)
    else:
        df = pd.DataFrame(columns=["Name","Date","Time","Lecture"])


    if ((df["Name"] == name) &
        (df["Lecture"] == lecture)).any():
        return


    new_row = {
        "Name": name,
        "Date": date,
        "Time": time,
        "Lecture": lecture
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    df.to_excel(file_path, index=False)

    print(f"Attendance marked for {name} ({lecture})")