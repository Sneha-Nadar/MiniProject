import cv2
import pickle
import time

from app.ai.face_matcher import find_best_match
from app.attendance.attendance_services import mark_attendance

# 🔥 USE face_recognition DIRECTLY (faster + stable)
import face_recognition

# Load encodings
with open("data/encodings/encodings.pkl", "rb") as f:
    known_encodings, known_names = pickle.load(f)


def run_recognition_session():

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)

    if not cap.isOpened():
        print("❌ Camera not opening")
        return

    print("🎥 Camera started (60 seconds)...")

    start_time = time.time()

    while True:
        if time.time() - start_time > 60:
            print("⏹ Session finished.")
            break

        ret, frame = cap.read()
        if not ret:
            print("❌ Frame not received")
            continue   # 🔥 don't break

        # 🔥 SMALL SIZE = FAST
        small = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)

        rgb_small = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

        # 🔥 FAST DETECTION (HOG)
        face_locations = face_recognition.face_locations(rgb_small, model="hog")

        # 🔥 ENCODINGS
        face_encodings = face_recognition.face_encodings(rgb_small, face_locations)

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):

            name, distance = find_best_match(
                known_encodings, known_names, face_encoding
            )

            if distance > 0.65:
                name = "Unknown"

            # 🔥 Scale back
            top *= 2
            right *= 2
            bottom *= 2
            left *= 2

            color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)

            if name != "Unknown":
                mark_attendance(name)

            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

            cv2.putText(
                frame,
                f"{name}",
                (left, top - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                color,
                2,
            )

        cv2.imshow("Live Attendance", frame)

        if cv2.waitKey(1) == 27:
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_recognition_session()