import cv2
import pickle
import sys
import os

from app.ai.face_detector import detect_faces
from app.ai.face_encoder import encode_faces
from app.ai.face_matcher import find_best_match
from app.attendance.attendance_services import mark_attendance

IMAGE_PATH = sys.argv[1] if len(sys.argv) > 1 else None

if not IMAGE_PATH or not os.path.exists(IMAGE_PATH):
    print(f"❌ Image not found: {IMAGE_PATH}")
    sys.exit(1)

# Load encodings
with open("data/encodings/encodings.pkl", "rb") as f:
    known_encodings, known_names = pickle.load(f)

print(f"🖼️ Processing image: {IMAGE_PATH}")
image = cv2.imread(IMAGE_PATH)

if image is None:
    print("❌ Could not read image.")
    sys.exit(1)

# 🔥 STEP 1: UPSCALE (important for group photos)
image = cv2.resize(image, None, fx=1.8, fy=1.8)

# 🔥 STEP 2: Convert to RGB
rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

# 🔥 STEP 3: Detect + Encode
faces = detect_faces(rgb_image)
encodings = encode_faces(rgb_image, faces)

print(f"👥 Detected {len(faces)} face(s)")

marked = []

for (top, right, bottom, left), face_encoding in zip(faces, encodings):
    name, distance = find_best_match(known_encodings, known_names, face_encoding)

    # 🔥 Real-world tolerant threshold
    if distance > 0.55:
        name = "Unknown"

    if name != "Unknown":
        mark_attendance(name)
        marked.append(name)

    # Draw bounding boxes
    color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)

    cv2.rectangle(image, (left, top), (right, bottom), color, 2)
    cv2.putText(
        image,
        f"{name} ({round(distance, 2)})",
        (left, top - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        color,
        2
    )

# Save annotated image
output_dir = os.path.join(os.path.dirname(IMAGE_PATH), "annotated")
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, os.path.basename(IMAGE_PATH))

cv2.imwrite(output_path, image)

print(f"✅ Marked: {marked}")
print(f"💾 Saved annotated image: {output_path}")