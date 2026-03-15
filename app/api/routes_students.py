from fastapi import APIRouter
import os

router = APIRouter()


@router.get("/students")
def get_students():

    dataset_path = "data/datasets"

    students = [
        name for name in os.listdir(dataset_path)
        if os.path.isdir(os.path.join(dataset_path, name))
    ]

    return {
        "total_students": len(students),
        "students": students
    }