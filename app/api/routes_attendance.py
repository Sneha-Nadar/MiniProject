from fastapi import APIRouter
import pandas as pd

router = APIRouter()


@router.get("/attendance")
def get_attendance():

    try:
        df = pd.read_excel("attendance.xlsx")

        return df.to_dict(orient="records")

    except:
        return []