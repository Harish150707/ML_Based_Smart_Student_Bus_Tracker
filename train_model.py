import cv2
import os
import numpy as np

# Create trainer folder if it doesn't exist
os.makedirs("trainer", exist_ok=True)

recognizer = cv2.face.LBPHFaceRecognizer_create()

faces = []
ids = []

dataset_path = "dataset"

for student_id in os.listdir(dataset_path):

    student_folder = os.path.join(dataset_path, student_id)

    if not os.path.isdir(student_folder):
        continue

    for image_name in os.listdir(student_folder):

        image_path = os.path.join(student_folder, image_name)

        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

        if img is None:
            continue

        faces.append(img)
        ids.append(int(student_id))

if len(faces) == 0:
    print("No face images found.")
    exit()

recognizer.train(faces, np.array(ids))

recognizer.write("trainer/trainer.yml")

print("===================================")
print("Face model trained successfully!")
print(f"Total face images : {len(faces)}")
print(f"Total students    : {len(set(ids))}")
print("Model saved as trainer/trainer.yml")
print("===================================")