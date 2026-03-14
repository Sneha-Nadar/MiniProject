import numpy as np
import face_recognition

def find_best_match(known_encodings, known_names, face_encoding, threshold=0.45):

    if len(known_encodings) == 0:
        return "Unknown", 1.0

    distances = face_recognition.face_distance(
        known_encodings,
        face_encoding
    )

    best_match_index = np.argmin(distances)
    best_distance = distances[best_match_index]

    if best_distance < threshold:
        return known_names[best_match_index], best_distance

    return "Unknown", best_distance