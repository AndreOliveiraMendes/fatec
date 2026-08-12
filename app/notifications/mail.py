import os
import smtplib
from email.message import EmailMessage


class Mail:
    def __init__(self, auth):
        self.host = os.getenv("SMTP_HOST")
        self.port = int(os.getenv("SMTP_PORT", 587))
        self.use_tls = os.getenv(
            "SMTP_USE_TLS", "true"
        ).lower() == "true"

        self.mail_from = os.getenv("MAIL_FROM")
        self.auth = auth

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

            self.auth.authenticate(smtp)

            smtp.send_message(message)

class SMTPAuth:
    def authenticate(self, smtp):
        raise NotImplementedError

class PasswordAuth(SMTPAuth):
    def __init__(self, user, password):
        self.user = user
        self.password = password

    def authenticate(self, smtp):
        smtp.login(self.user, self.password)

class OAuth2Auth(SMTPAuth):
    def __init__(self, user, token):
        self.user = user
        self.token = token

    def authenticate(self, smtp):
        # XOAUTH2
        print("OAuth2 authentication is not implemented yet.")