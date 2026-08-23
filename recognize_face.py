import os
import time
import threading
from datetime import datetime

import cv2
from flask import Flask
from flask_mail import Mail, Message

from database import get_db_connection

# =====================================
# FLASK MAIL CONFIGURATION
# =====================================
app = Flask(__name__)

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME", "")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD", "")

mail = Mail(app)


# =====================================
# SEND EMAIL IN BACKGROUND
# =====================================
def send_attendance_email(parent_email, student_name):
    with app.app_context():
        try:
            msg = Message(
                subject="Student Bus Attendance",
                sender=app.config["MAIL_USERNAME"],
                recipients=[parent_email]
            )

            msg.body = f"""
Hello Parent,

Your child {student_name} has boarded the school bus successfully.

Attendance has been marked successfully.

Time:
{datetime.now().strftime("%d-%m-%Y %H:%M:%S")}

Thank you,
Smart Student Tracking System
"""

            mail.send(msg)
            print("Email Sent Successfully")

        except Exception as e:
            print("Email Error:", e)


def send_email_background(parent_email, student_name):
    """
    Fires the email on a separate thread so a slow SMTP connection can't
    stall the video loop. Returns the Thread object so the caller can
    join() it before the process exits — daemon threads get killed
    instantly when the main script ends, which was cutting emails off
    mid-send once the camera started auto-closing quickly.
    """
    thread = threading.Thread(
        target=send_attendance_email,
        args=(parent_email, student_name),
        daemon=True
    )
    thread.start()
    return thread


# =====================================
# LOAD TRAINED MODEL
# =====================================
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read("trainer/trainer.yml")


# =====================================
# LOAD FACE DETECTOR
# =====================================
face_detector = cv2.CascadeClassifier(
    "haarcascade_frontalface_default.xml"
)

if face_detector.empty():
    print("Cannot load haarcascade_frontalface_default.xml")
    exit()


# =====================================
# START FACE RECOGNITION FUNCTION
# =====================================
def start_recognition():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    cam = cv2.VideoCapture(0)

    recognized = set()
    email_threads = []

    # Once we get a confident, known match, we keep the window open just
    # long enough to show the confirmation text on screen, then close the
    # camera automatically instead of waiting for a manual ESC press.
    close_at = None
    CONFIRMATION_DISPLAY_SECONDS = 2.0

    try:
        while True:

            ret, frame = cam.read()

            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            faces = face_detector.detectMultiScale(
                gray,
                scaleFactor=1.3,
                minNeighbors=5
            )

            for (x, y, w, h) in faces:

                face = gray[y:y+h, x:x+w]

                student_id, confidence = recognizer.predict(face)

                print("--------------------------------")
                print("Predicted ID :", student_id)
                print("Confidence :", confidence)

                if confidence < 70:

                    cursor.execute(
                        "SELECT * FROM students WHERE student_id=%s",
                        (int(student_id),)
                    )

                    student = cursor.fetchone()

                    if student:

                        name = student["student_name"]

                        cv2.rectangle(
                            frame,
                            (x, y),
                            (x + w, y + h),
                            (0, 255, 0),
                            2
                        )

                        cv2.putText(
                            frame,
                            name,
                            (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8,
                            (0, 255, 0),
                            2
                        )

                        if student_id not in recognized:

                            today = datetime.now().date()

                            cursor.execute("""
                                SELECT attendance_id
                                FROM attendance
                                WHERE student_id=%s
                                AND attendance_date=%s
                            """, (student_id, today))

                            already_marked = cursor.fetchone()

                            if already_marked:

                                cv2.putText(
                                    frame,
                                    "Already Marked Today",
                                    (20, 40),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    1,
                                    (0, 0, 255),
                                    2
                                )

                                recognized.add(student_id)

                            else:

                                now = datetime.now()

                                cursor.execute("""
                                    INSERT INTO attendance
                                    (student_id, attendance_date, attendance_time, status)
                                    VALUES (%s, %s, %s, %s)
                                """, (
                                    student_id,
                                    now.date(),
                                    now.strftime("%H:%M:%S"),
                                    "Present"
                                ))

                                conn.commit()

                                print("Attendance Saved")

                                # FIX: previously looked up the recipient from
                                # the `parents` table, which only has a row
                                # once a parent has completed self-registration.
                                # Most students won't have that yet, so the
                                # email silently never sent. `students.parent_email`
                                # is populated immediately when the admin adds
                                # the student, so use that instead.
                                parent_email = student.get("parent_email")

                                if parent_email:
                                    email_threads.append(
                                        send_email_background(parent_email, name)
                                    )
                                else:
                                    print(f"No parent_email on file for student_id={student_id}, skipping notification.")

                                cv2.putText(
                                    frame,
                                    "Attendance Marked",
                                    (20, 40),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    1,
                                    (0, 255, 0),
                                    2
                                )

                                recognized.add(student_id)

                        # A confident, known face was matched this frame —
                        # start the countdown to auto-close the camera.
                        if close_at is None:
                            close_at = time.time() + CONFIRMATION_DISPLAY_SECONDS

                    else:

                        cv2.rectangle(
                            frame,
                            (x, y),
                            (x + w, y + h),
                            (0, 0, 255),
                            2
                        )

                        cv2.putText(
                            frame,
                            "ID Not Found",
                            (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8,
                            (0, 0, 255),
                            2
                        )

                else:

                    cv2.rectangle(
                        frame,
                        (x, y),
                        (x + w, y + h),
                        (0, 0, 255),
                        2
                    )

                    cv2.putText(
                        frame,
                        "Unknown",
                        (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 0, 255),
                        2
                    )

            cv2.imshow("Face Recognition", frame)

            key = cv2.waitKey(1) & 0xFF

            # Press ESC to exit manually at any time
            if key == 27:
                break

            # Auto-close once the confirmation message has had time to display
            if close_at is not None and time.time() >= close_at:
                break

    finally:
        # Close the camera window right away — this is what the person
        # demoing the system actually sees, so it should feel instant.
        cam.release()
        cv2.destroyAllWindows()

        # But give any in-flight emails a chance to actually finish sending.
        # These run on daemon threads, which get killed immediately when the
        # process exits — without this, an email that hasn't completed its
        # SMTP handshake yet (often 1-3+ seconds) would be silently dropped
        # the moment this script ends, with no error printed anywhere.
        for thread in email_threads:
            thread.join(timeout=10)

        cursor.close()
        conn.close()


if __name__ == "__main__":
    start_recognition()
