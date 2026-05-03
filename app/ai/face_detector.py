import cv2
import face_recognition

def detect_faces(image, model="cnn"):
    """
    Detect faces using CNN model (more accurate than HOG).
    Use model="hog" for CPU-only if CNN is too slow on your machine.
    CNN is ~3x slower but handles side angles, low light, small faces much better.
    """
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    face_locations = face_recognition.face_locations(
        rgb_image,
        model=model,          # "cnn" for accuracy, "hog" for speed
        number_of_times_to_upsample=1
    )
    return face_locations