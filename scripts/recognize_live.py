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

    print("Opening camera...")

    # 🔥 FIX 1: Try multiple camera indices
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)

    if not cap.isOpened():
        print("❌ Camera not opening")
        return

    print("🎥 Camera started (60 seconds)...")

    start_time = time.time()
    FRAME_HISTORY = 10

    face_histories = {}
    marked_once = set()   # 🔥 FIX 2: avoid DB spam

    while True:
        if time.time() - start_time > 60:
            print("⏹ Session finished.")
            break

        ret, frame = cap.read()
        if not ret:
            print("❌ Frame not received")
            break

        # 🔥 FIX 3: smaller frame (performance)
        frame = cv2.resize(frame, (640, 480))

        # 🔥 FIX 4: fix brightness
        frame = cv2.convertScaleAbs(frame, alpha=0.8, beta=-30)

        # 🔥 FIX 5: RGB conversion (VERY IMPORTANT)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        faces = detect_faces(rgb_frame)
        encodings = encode_faces(rgb_frame, faces)

        for (top, right, bottom, left), face_encoding in zip(faces, encodings):

            name, distance = find_best_match(known_encodings, known_names, face_encoding)

            # 🔥 FIX 6: better threshold
            if distance > 0.65:
                name = "Unknown"

            # Face tracking
            x_center = (left + right) // 2
            bucket   = x_center // 100

            if bucket not in face_histories:
                face_histories[bucket] = []

            face_histories[bucket].append(name)

            if len(face_histories[bucket]) > FRAME_HISTORY:
                face_histories[bucket].pop(0)

            stable_name = Counter(face_histories[bucket]).most_common(1)[0][0]

            # 🔥 FIX 7: avoid multiple attendance calls
            if stable_name != "Unknown" and stable_name not in marked_once:
                mark_attendance(stable_name)
                marked_once.add(stable_name)

            # Draw
            color = (0, 255, 0) if stable_name != "Unknown" else (0, 0, 255)

            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            label = f"{stable_name} ({round(distance, 2)})"

            cv2.putText(frame, label, (left, top - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        cv2.imshow("Live Attendance", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

        # 🔥 FIX 8: prevent freeze
        time.sleep(0.01)

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_recognition_session()