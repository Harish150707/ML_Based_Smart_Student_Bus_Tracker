import cv2
import os

# -----------------------------
# Enter Student ID
# -----------------------------
student_id = input("Enter Student ID: ")

# -----------------------------
# Create dataset folder
# -----------------------------
dataset_path = os.path.join("dataset", student_id)
os.makedirs(dataset_path, exist_ok=True)

# -----------------------------
# Load Haar Cascade
# -----------------------------
face_detector = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")

if face_detector.empty():
    print("ERROR: Could not load haarcascade_frontalface_default.xml")
    print("Make sure the XML file is in the same folder as face_capture.py")
    exit()

# -----------------------------
# Open Laptop Camera
# -----------------------------
camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("ERROR: Could not open webcam.")
    exit()

count = 0

print("\nCamera started...")
print("Look at the camera.")
print("50 face images will be captured automatically.\n")

while True:

    ret, frame = camera.read()

    if not ret:
        print("Failed to capture frame.")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_detector.detectMultiScale(
        gray,
        scaleFactor=1.3,
        minNeighbors=5
    )

    for (x, y, w, h) in faces:

        count += 1

        face = gray[y:y+h, x:x+w]

        filename = os.path.join(dataset_path, f"{count}.jpg")

        cv2.imwrite(filename, face)

        cv2.rectangle(frame,
                      (x, y),
                      (x+w, y+h),
                      (0, 255, 0),
                      2)

        cv2.putText(
            frame,
            f"Images: {count}/50",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

    cv2.imshow("Face Capture", frame)

    key = cv2.waitKey(1)

    if key == 27:
        break

    if count >= 50:
        break

camera.release()
cv2.destroyAllWindows()

print("\nFace images captured successfully!")
print("Saved in:", dataset_path)