import cv2
import pickle
from collections import Counter
import time

from app.ai.face_detector import detect_faces
from app.ai.face_encoder import encode_faces
from app.ai.face_matcher import find_best_match
from app.attendance.attendance_services import mark_attendance

with open("data/encodings/encodings.pkl", "rb") as f:
    known_encodings, known_names = pickle.load(f)

def run_recognition_session():
    """Run a 60-second face recognition session."""

    # 🔥 FIX 1: Use CAP_DSHOW (Windows fix)
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    # 🔥 FIX 2: Check camera
    if not cap.isOpened():
        print("❌ Camera not opening")
        return

    print("🎥 Camera started (60 seconds)...")

    start_time = time.time()
    FRAME_HISTORY = 10
    face_histories = {}

    while True:
        if time.time() - start_time > 60:
            print("⏹ Session finished.")
            break

        ret, frame = cap.read()
        if not ret:
            print("❌ Frame not received")
            break

        # 🔥 FIX 3: Resize properly (not too small)
        frame = cv2.resize(frame, (960, 720))

        # 🔥 FIX 4: Convert to RGB (VERY IMPORTANT)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        faces = detect_faces(rgb_frame)
        encodings = encode_faces(rgb_frame, faces)

        for (top, right, bottom, left), face_encoding in zip(faces, encodings):

            name, distance = find_best_match(known_encodings, known_names, face_encoding)

            # 🔥 FIX 5: Better threshold for live
            if distance > 0.60:
                name = "Unknown"

            # Face tracking bucket
            x_center = (left + right) // 2
            bucket   = x_center // 100

            if bucket not in face_histories:
                face_histories[bucket] = []

            face_histories[bucket].append(name)

            if len(face_histories[bucket]) > FRAME_HISTORY:
                face_histories[bucket].pop(0)

            stable_name = Counter(face_histories[bucket]).most_common(1)[0][0]

            if stable_name != "Unknown":
                mark_attendance(stable_name)

            # Draw
            color = (0, 255, 0) if stable_name != "Unknown" else (0, 0, 255)

            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            label = f"{stable_name} ({round(distance, 2)})"

            cv2.putText(frame, label, (left, top - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        cv2.imshow("Live Attendance", frame)

        # ESC to exit
        if cv2.waitKey(1) == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_recognition_session()