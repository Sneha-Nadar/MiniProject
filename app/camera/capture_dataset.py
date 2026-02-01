import cv2
import os

# Base dataset directory
DATASET_DIR = "data/datasets"

def capture_images(student_id, student_name, num_images=20):
    """
    Captures face images for a student using webcam.
    Press SPACE to capture image.
    Press ESC to exit early.
    """

    # Create student folder
    student_folder = f"{student_id}_{student_name}"
    save_path = os.path.join(DATASET_DIR, student_folder)
    os.makedirs(save_path, exist_ok=True)

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("❌ Cannot access camera")
        return

    print(f"📸 Capturing images for {student_name}")
    print("➡️ Press SPACE to capture | ESC to quit")

    img_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        window_name = "Dataset Capture - Press SPACE"

        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.imshow(window_name, frame)
        cv2.setWindowProperty(

            window_name,
            cv2.WND_PROP_TOPMOST,
            1
        )


        key = cv2.waitKey(1)

        if key == 27:  # ESC
            break

        if key == 32:  # SPACE
            img_name = f"img_{img_count+1}.jpg"
            img_path = os.path.join(save_path, img_name)
            cv2.imwrite(img_path, frame)
            img_count += 1
            print(f"✅ Image {img_count} saved")

        if img_count >= num_images:
            break

    cap.release()
    cv2.destroyAllWindows()
    print("🎉 Dataset capture completed")


if __name__ == "__main__":
    student_id = input("Enter Student ID: ")
    student_name = input("Enter Student Name: ")
    capture_images(student_id, student_name)
