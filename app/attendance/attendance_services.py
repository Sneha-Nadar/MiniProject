import pandas as pd
import os
from datetime import datetime

FILE_NAME = "attendance.xlsx"


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

    return None


def mark_attendance(name):

    lecture = get_current_lecture()

    if lecture is None:
        print("Outside lecture time")
        return

    now = datetime.now()

    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")

    if os.path.exists(FILE_NAME):
        df = pd.read_excel(FILE_NAME)
    else:
        df = pd.DataFrame(columns=["Name","Date","Time","Lecture"])


    if ((df["Name"] == name) &
        (df["Date"] == date) &
        (df["Lecture"] == lecture)).any():

        return


    new_row = {
        "Name": name,
        "Date": date,
        "Time": time,
        "Lecture": lecture
    }

    df = pd.concat([df,pd.DataFrame([new_row])],ignore_index=True)

    df.to_excel(FILE_NAME,index=False)

    print(f"Attendance marked for {name} ({lecture})")