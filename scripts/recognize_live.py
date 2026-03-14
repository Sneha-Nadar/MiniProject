import cv2
import pickle
from collections import Counter

from app.ai.face_detector import detect_faces
from app.ai.face_encoder import encode_faces
from app.ai.face_matcher import find_best_match
from app.attendance.attendance_service import mark_attendance


# Load encodings
with open("data/encodings/encodings.pkl", "rb") as f:
    known_encodings, known_names = pickle.load(f)


cap = cv2.VideoCapture(0)

print("🎥 Camera started. Press ESC to exit.")


recent_names = []
FRAME_HISTORY = 10


while True:

    ret, frame = cap.read()

    if not ret:
        break

    # Resize frame for stability
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

        # Stabilize prediction
        recent_names.append(name)

        if len(recent_names) > FRAME_HISTORY:
            recent_names.pop(0)

        stable_name = Counter(recent_names).most_common(1)[0][0]

        # Mark attendance
        if stable_name != "Unknown":
            mark_attendance(stable_name)

        # Draw bounding box
        cv2.rectangle(frame, (left, top), (right, bottom), (0,255,0), 2)

        label = f"{stable_name} ({round(distance,2)})"

        cv2.putText(
            frame,
            label,
            (left, top - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0,255,0),
            2
        )

    cv2.imshow("Live Face Recognition", frame)

    if cv2.waitKey(1) == 27:
        break


cap.release()
cv2.destroyAllWindows()