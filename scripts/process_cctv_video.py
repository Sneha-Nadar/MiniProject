import cv2
import pickle
import sys
from collections import Counter

from app.ai.face_detector import detect_faces
from app.ai.face_encoder import encode_faces
from app.ai.face_matcher import find_best_match
from app.attendance.attendance_services import mark_attendance


# Accept video path from command line (passed by main.py) or fallback to default
VIDEO_PATH = sys.argv[1] if len(sys.argv) > 1 else "data/video/lab_video.mp4"


with open("data/encodings/encodings.pkl", "rb") as f:
    known_encodings, known_names = pickle.load(f)

cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():
    print(f"❌ Could not open video: {VIDEO_PATH}")
    sys.exit(1)

print(f"🎥 Processing video: {VIDEO_PATH}")

FRAME_HISTORY = 10
frame_count   = 0

# FIX: per-face history using x-position buckets (not shared list)
face_histories = {}   # bucket_key → [name, name, ...]

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1
    if frame_count % 2 != 0:      # process every 2nd frame for speed
        continue

    frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)

    faces     = detect_faces(frame)
    encodings = encode_faces(frame, faces)

    for (top, right, bottom, left), face_encoding in zip(faces, encodings):

        name, distance = find_best_match(known_encodings, known_names, face_encoding)

        if distance > 0.50:
            name = "Unknown"

        # Bucket by horizontal center → independent history per face
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
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        label = f"{stable_name} ({round(distance, 2)})"
        cv2.putText(frame, label, (left, top - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    cv2.imshow("CCTV Attendance", frame)
    if cv2.waitKey(25) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
print("✅ Video processing complete.")