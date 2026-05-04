import face_recognition

def encode_faces(image, face_locations):
    """
    Generate face encodings for detected faces.
    Assumes image is already in RGB format.
    """
    return face_recognition.face_encodings(image, face_locations)