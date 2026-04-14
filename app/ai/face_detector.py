import face_recognition

def detect_faces(image):
    try:
        # 🔥 Best for group + real-world detection
        return face_recognition.face_locations(image, model="cnn")
    except:
        # 🔥 Safe fallback
        return face_recognition.face_locations(image, model="hog")