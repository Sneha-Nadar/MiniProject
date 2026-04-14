import face_recognition

def detect_faces(image):
    # 🔥 USE HOG (FAST, REAL-TIME)
    return face_recognition.face_locations(image, model="hog")