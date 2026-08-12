import os
from datetime import datetime

from app.notifications.mail import Mail, OAuth2Auth, PasswordAuth


def _test_email_body(to_email):
    return (
        f"Olá!\n\n"
        f"Este é um e-mail de teste enviado para {to_email}.\n\n"
        f"Se você recebeu esta mensagem, significa que a configuração do "
        f"servidor de e-mail está funcionando corretamente e que o sistema "
        f"conseguiu realizar o envio com sucesso.\n\n"
        f"Esta mensagem foi gerada automaticamente para verificar a "
        f"funcionalidade de envio de e-mails. Por favor, não responda a este "
        f"e-mail.\n\n"
        f"Se você não solicitou este teste, pode simplesmente ignorar esta mensagem.\n\n"
        f"---\n"
        f"Teste de envio de e-mail\n"
        f"Gerado automaticamente pelo sistema em "
        f"{datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}."
    )


def _send_test_email(to_email, auth):
    try:
        mail = Mail(auth)

        mail.send(
            to_email,
            "Test Email",
            _test_email_body(to_email)
        )

        return True, f"Test email sent successfully to {to_email}."

    except Exception as e:
        return False, f"Failed to send test email: {str(e)}"


def send_test_email_apppassword(to_email):
    auth = PasswordAuth(
        user=os.getenv("SMTP_USER"),
        password=os.getenv("SMTP_PASSWORD")
    )

    return _send_test_email(to_email, auth)


def send_test_email_oauth(to_email):
    auth = OAuth2Auth(
        user=os.getenv("SMTP_USER"),
        token=os.getenv("SMTP_OAUTH_TOKEN")
    )

    return _send_test_email(to_email, auth)