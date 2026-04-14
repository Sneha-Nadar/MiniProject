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
    cap = cv2.VideoCapture(0)
    print("🎥 Camera started (60 seconds)...")

    start_time = time.time()
    FRAME_HISTORY = 10

    # FIX: per-face history dict keyed by position bucket
    face_histories = {}  # key: x-bucket → list of names

    while True:
        if time.time() - start_time > 60:
            print("⏹ Session finished.")
            break

        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.resize(frame, (960, 720))
        faces = detect_faces(frame)
        encodings = encode_faces(frame, faces)

        for (top, right, bottom, left), face_encoding in zip(faces, encodings):
            name, distance = find_best_match(known_encodings, known_names, face_encoding)

            if distance > 0.50:
                name = "Unknown"

            # Use horizontal center bucket as face identity key
            x_center = (left + right) // 2
            bucket   = x_center // 100  # 100px wide buckets

            if bucket not in face_histories:
                face_histories[bucket] = []

            face_histories[bucket].append(name)

            if len(face_histories[bucket]) > FRAME_HISTORY:
                face_histories[bucket].pop(0)

            stable_name = Counter(face_histories[bucket]).most_common(1)[0][0]

            if stable_name != "Unknown":
                mark_attendance(stable_name)

            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            label = f"{stable_name} ({round(distance, 2)})"
            cv2.putText(frame, label, (left, top - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imshow("Live Attendance", frame)
        if cv2.waitKey(1) == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_recognition_session()