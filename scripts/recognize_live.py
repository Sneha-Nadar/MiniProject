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
    """Stable + Fast Live Recognition (NO FREEZE VERSION)"""

    # 🔥 Try both cameras
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)

    if not cap.isOpened():
        print("❌ Camera not opening")
        return

    print("🎥 Camera started (60 seconds)...")

    start_time = time.time()
    frame_count = 0
    FRAME_SKIP = 5   # 🔥 higher = faster

    while True:
        if time.time() - start_time > 60:
            print("⏹ Session finished.")
            break

        ret, frame = cap.read()
        if not ret:
            print("❌ Frame not received")
            break

        # 🔥 SMALL resolution = BIG performance boost
        frame = cv2.resize(frame, (320, 240))

        frame_count += 1

        # 🔥 Skip frames (reduces CPU load)
        if frame_count % FRAME_SKIP != 0:
            cv2.imshow("Live Attendance", frame)
            if cv2.waitKey(1) == 27:
                break
            continue

        # 🔥 Convert to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # 🔥 Detect faces
        faces = detect_faces(rgb_frame)

        # 🔥 Limit faces (avoid overload)
        faces = faces[:3]

        # 🔥 Encode
        encodings = encode_faces(rgb_frame, faces)

        for (top, right, bottom, left), face_encoding in zip(faces, encodings):

            name, distance = find_best_match(
                known_encodings, known_names, face_encoding
            )

            # 🔥 Relax threshold for demo
            if distance > 0.65:
                name = "Unknown"

            # 🔥 Mark attendance
            if name != "Unknown":
                mark_attendance(name)

            color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)

            # 🔥 Draw box
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

            cv2.putText(
                frame,
                name,
                (left, top - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                1,
            )

        # 🔥 Show frame
        cv2.imshow("Live Attendance", frame)

        # 🔥 THIS prevents "Not Responding"
        if cv2.waitKey(1) == 27:
            break

        # 🔥 Small delay keeps UI smooth
        time.sleep(0.02)

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_recognition_session()