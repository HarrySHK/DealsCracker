import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings


async def send_email(to_email: str, subject: str, content: str):
    try:
        # Create the email content
        msg = MIMEMultipart()
        msg["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.SMTP_USERNAME}>"
        msg["To"] = to_email
        msg["Subject"] = subject

        # Attach the email body
        msg.attach(MIMEText(content, "plain"))

        # Connect to the SMTP server
        with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(msg)

        print(f"Email sent successfully to {to_email}")
    except Exception as e:
        print(f"Error sending email: {e}")
        raise
