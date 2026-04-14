import os
import pickle
import cv2

from app.ai.face_detector import detect_faces
from app.ai.face_encoder import encode_faces

DATASET_DIR = "data/datasets"
ENCODINGS_FILE = "data/encodings/encodings.pkl"

known_encodings = []
known_names = []

print("🔄 Encoding dataset...")

for person_name in os.listdir(DATASET_DIR):

    person_path = os.path.join(DATASET_DIR, person_name)

    if not os.path.isdir(person_path):
        continue

    print(f"Encoding {person_name}...")

    for image_name in os.listdir(person_path):

        image_path = os.path.join(person_path, image_name)

        image = cv2.imread(image_path)

        if image is None:
            continue

        # 🔥 FIX 1: Resize (standardize input)
        image = cv2.resize(image, (640, 480))

        # 🔥 FIX 2: Convert to RGB (VERY IMPORTANT)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        faces = detect_faces(rgb_image)

        # 🔥 FIX 3: Skip bad images
        if len(faces) != 1:
            print(f"⚠️ Skipping {image_name} (faces detected: {len(faces)})")
            continue

        encodings = encode_faces(rgb_image, faces)

        if len(encodings) == 0:
            continue

        known_encodings.append(encodings[0])
        known_names.append(person_name)

print("💾 Saving encodings...")

with open(ENCODINGS_FILE, "wb") as f:
    pickle.dump((known_encodings, known_names), f)

print(f"✅ Encoding complete. Total encodings: {len(known_encodings)}")