from fastapi import APIRouter
import pandas as pd
import os
from app.attendance.attendance_services import get_today_folder

router = APIRouter()

@router.get("/attendance")
def get_attendance():
    try:
        folder    = get_today_folder()
        file_path = os.path.join(folder, "attendance.xlsx")
        if not os.path.exists(file_path):
            return []
        df = pd.read_excel(file_path)
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"Error reading attendance: {e}")
        return []