import cv2
import pickle
from collections import Counter

from app.ai.face_detector import detect_faces
from app.ai.face_encoder import encode_faces
from app.ai.face_matcher import find_best_match
from app.attendance.attendance_services import mark_attendance


VIDEO_PATH = "data/videos/lab_cctv.mp4"


# Load student encodings
with open("data/encodings/encodings.pkl", "rb") as f:
    known_encodings, known_names = pickle.load(f)


cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():
    print("❌ Could not open CCTV video.")
    exit()

print("🎥 Processing CCTV video...")


recent_names = []
FRAME_HISTORY = 10

frame_count = 0


while True:

    ret, frame = cap.read()

    if not ret:
        break

    frame_count += 1

    # Process every 2nd frame (for speed)
    if frame_count % 2 != 0:
        continue

    frame = cv2.resize(frame, (0,0), fx=0.5, fy=0.5)

    faces = detect_faces(frame)
    encodings = encode_faces(frame, faces)

    for (top, right, bottom, left), face_encoding in zip(faces, encodings):

        name, distance = find_best_match(
            known_encodings,
            known_names,
            face_encoding
        )

        # Reject weak matches
        if distance > 0.50:
            name = "Unknown"

        recent_names.append(name)

        if len(recent_names) > FRAME_HISTORY:
            recent_names.pop(0)

        stable_name = Counter(recent_names).most_common(1)[0][0]

        # mark attendance
        if stable_name != "Unknown":
            mark_attendance(stable_name)

        cv2.rectangle(frame,(left,top),(right,bottom),(0,255,0),2)

        label = f"{stable_name} ({round(distance,2)})"

        cv2.putText(
            frame,
            label,
            (left, top-10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0,255,0),
            2
        )

    cv2.imshow("CCTV Attendance System", frame)

    if cv2.waitKey(25) & 0xFF == 27:
        break


cap.release()
cv2.destroyAllWindows()

print("✅ CCTV video processing complete.")