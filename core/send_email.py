import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

def send_email(subject, body, to_emails, email_user, email_pass, smtp_server, smtp_port):
    if not all([email_user, email_pass, to_emails]):
        raise ValueError("Missing email credentials or recipient list.")

    msg = EmailMessage()
    msg["From"] = email_user
    msg["To"] = ", ".join(to_emails)
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(email_user, email_pass)
            server.send_message(msg)
            print("✅ Email sent successfully!")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
