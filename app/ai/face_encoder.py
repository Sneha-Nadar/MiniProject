import cv2
import face_recognition

def detect_faces(image):
    """
    Detect faces using HOG model.
    Fast, CPU-friendly, works well for frontal faces in classroom settings.
    """
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    face_locations = face_recognition.face_locations(
        rgb_image,
        model="hog",
        number_of_times_to_upsample=1
    )
    return face_locations