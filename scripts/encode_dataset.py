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

        faces = detect_faces(image)

        encodings = encode_faces(image, faces)

        for encoding in encodings:
            known_encodings.append(encoding)
            known_names.append(person_name)

print("💾 Saving encodings...")

with open(ENCODINGS_FILE, "wb") as f:
    pickle.dump((known_encodings, known_names), f)

print("✅ Encoding complete.")