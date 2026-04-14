import face_recognition

def detect_faces(image):
    try:
        # 🔥 Best for group images (more accurate)
        return face_recognition.face_locations(image, model="cnn")
    except:
        # 🔥 Safe fallback (CPU friendly)
        return face_recognition.face_locations(image, model="hog")