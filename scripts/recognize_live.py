import cv2
import pickle
from collections import Counter
import time

from app.ai.face_detector import detect_faces
from app.ai.face_encoder import encode_faces
from app.ai.face_matcher import find_best_match
from app.attendance.attendance_services import mark_attendance

# 🔥 Load encodings
with open("data/encodings/encodings.pkl", "rb") as f:
    known_encodings, known_names = pickle.load(f)


def run_recognition_session():
    """Run a 60-second face recognition session (FAST + STABLE)"""

    # 🔥 Try both cameras (internal + external)
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)

    if not cap.isOpened():
        print("❌ Camera not opening")
        return

    print("🎥 Camera started (60 seconds)...")

    start_time = time.time()
    FRAME_SKIP = 3
    frame_count = 0

    while True:
        # ⏱ Stop after 60 sec
        if time.time() - start_time > 60:
            print("⏹ Session finished.")
            break

        ret, frame = cap.read()
        if not ret:
            print("❌ Frame not received")
            break

        # 🔥 Resize for speed
        frame = cv2.resize(frame, (640, 480))

        frame_count += 1

        # 🔥 Skip frames (VERY IMPORTANT)
        if frame_count % FRAME_SKIP != 0:
            cv2.imshow("Live Attendance", frame)
            if cv2.waitKey(1) == 27:
                break
            continue

        # 🔥 Convert to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        faces = detect_faces(rgb_frame)

        # 🔥 Prevent overload (many faces = lag)
        if len(faces) > 10:
            cv2.imshow("Live Attendance", frame)
            cv2.waitKey(1)
            continue

        encodings = encode_faces(rgb_frame, faces)

        for (top, right, bottom, left), face_encoding in zip(faces, encodings):

            name, distance = find_best_match(
                known_encodings, known_names, face_encoding
            )

            # 🔥 Threshold tuning
            if distance > 0.60:
                name = "Unknown"

            color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)

            # 🔥 Mark attendance only for known
            if name != "Unknown":
                mark_attendance(name)

            # 🔥 Draw box
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

            label = f"{name} ({round(distance, 2)})"
            cv2.putText(
                frame,
                label,
                (left, top - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2,
            )

        # 🔥 Show frame
        cv2.imshow("Live Attendance", frame)

        # 🔥 MUST for UI (prevents freeze)
        if cv2.waitKey(1) == 27:
            break

        # 🔥 Small delay → smooth UI
        time.sleep(0.01)

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_recognition_session()