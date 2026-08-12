import os
import smtplib

from email.message import EmailMessage


class Mail:
    def __init__(self):
        self.host = os.getenv("SMTP_HOST")
        self.port = int(os.getenv("SMTP_PORT", 587))
        self.user = os.getenv("SMTP_USER")
        self.password = os.getenv("SMTP_PASSWORD")
        self.use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        self.mail_from = os.getenv("MAIL_FROM", self.user)

    def send(self, to, subject, body):
        message = EmailMessage()
        message["From"] = self.mail_from
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)

        with smtplib.SMTP(self.host, self.port) as smtp:
            smtp.ehlo()

            if self.use_tls:
                smtp.starttls()
                smtp.ehlo()

            smtp.login(self.user, self.password)
            smtp.send_message(message)