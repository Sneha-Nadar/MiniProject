import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pickle
import cv2
import face_recognition   # 🔥 direct use (faster)

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

    max_images_per_person = 10
    count = 0

    for image_name in os.listdir(person_path):

        if count >= max_images_per_person:
            break

        image_path = os.path.join(person_path, image_name)

        image = cv2.imread(image_path)

        if image is None:
            continue

        # 🔥 Resize smaller (faster)
        image = cv2.resize(image, (320, 240))

        # 🔥 Convert to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # 🔥 FAST detection (HOG)
        faces = face_recognition.face_locations(rgb_image, model="hog")

        if len(faces) != 1:
            print(f"⚠️ Skipping {image_name} (faces detected: {len(faces)})")
            continue

        encodings = face_recognition.face_encodings(rgb_image, faces)

        if len(encodings) == 0:
            continue

        known_encodings.append(encodings[0])
        known_names.append(person_name)

        count += 1

print("💾 Saving encodings...")

with open(ENCODINGS_FILE, "wb") as f:
    pickle.dump((known_encodings, known_names), f)

print(f"✅ Encoding complete. Total encodings: {len(known_encodings)}")