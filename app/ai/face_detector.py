import cv2
import face_recognition


def detect_faces(image):
    """
    Detect faces in an image.
    Returns list of face locations.
    """
    # Convert BGR (OpenCV) to RGB (face_recognition)
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Detect faces
    face_locations = face_recognition.face_locations(
        rgb_image,
        model="hog"  # fast & reliable for real-time
    )

    return face_locations
