import cv2
import face_recognition


def encode_faces(image, face_locations):
    """
    Generate face encodings for detected faces.
    """
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    encodings = face_recognition.face_encodings(
        rgb_image,
        face_locations
    )

    return encodings
