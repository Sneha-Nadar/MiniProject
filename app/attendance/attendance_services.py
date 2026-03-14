import pandas as pd
import os
from datetime import datetime

FILE_NAME = "attendance.xlsx"

def mark_attendance(name):

    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")

    if os.path.exists(FILE_NAME):
        df = pd.read_excel(FILE_NAME)
    else:
        df = pd.DataFrame(columns=["Name", "Date", "Time"])

    if ((df["Name"] == name) & (df["Date"] == date)).any():
        return

    df.loc[len(df)] = [name, date, time]

    df.to_excel(FILE_NAME, index=False)

    print(f"✅ Attendance marked for {name}")
from datetime import datetime

FILE_NAME = "attendance.xlsx"

def mark_attendance(name):

    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")

    if os.path.exists(FILE_NAME):
        df = pd.read_excel(FILE_NAME)
    else:
        df = pd.DataFrame(columns=["Name", "Date", "Time"])

    # prevent duplicate attendance
    if ((df["Name"] == name) & (df["Date"] == date)).any():
        return

    new_row = {
        "Name": name,
        "Date": date,
        "Time": time
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    df.to_excel(FILE_NAME, index=False)

    print(f"✅ Attendance marked for {name}")