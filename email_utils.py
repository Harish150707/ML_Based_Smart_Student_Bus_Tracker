from flask_mail import Mail, Message

mail = Mail()

def init_mail(app):
    mail.init_app(app)

def send_attendance_email(app, parent_email, student_name):
    with app.app_context():
        msg = Message(
            subject="Student Bus Attendance",
            sender=app.config["MAIL_USERNAME"],
            recipients=[parent_email]
        )

        msg.body = f"""
Hello Parent,

Your child {student_name} has boarded the school bus successfully.

Thank you,
Smart Student Tracking System
"""

        mail.send(msg)