import smtplib
from email.message import EmailMessage
from authlib.integrations.requests_client import OAuth2Session
import base64

TEXT_MAIL = """
Olá, este é um email de teste enviado pelo sistema.
Se você recebeu este email, significa que a configuração de email está funcionando corretamente.
Caso você não tenha solicitado este email, por favor, ignore-o.

Atenciosamente,
Sistema de Gerenciamento de Reservas de Recursos.
"""

def same_config(config, data, check_id=True):
    if check_id:
        return config.get('id') == data.get('id')
    return (
        config.get('smtp_server') == data.get('smtp_server') and
        config.get('smtp_port') == data.get('smtp_port') and
        config.get('username') == data.get('username') and
        config.get('mail_from') == data.get('mail_from') and
        config.get('use_tls') == data.get('use_tls')
    )


def get_config_by_id(configs, config_id):
    mail_configs = configs.get("configs", [])
    return next(
        (config for config in mail_configs if config.get("id") == config_id),
        None
    )

def get_google_access_token(client_id, client_secret, refresh_token):
    client = OAuth2Session(
        client_id=client_id,
        client_secret=client_secret,
        scope="https://mail.google.com/",
    )

    token = client.refresh_token(
        "https://oauth2.googleapis.com/token",
        refresh_token=refresh_token,
    )

    return token["access_token"]

def smtp_oauth2_auth(server, username, access_token):
    auth_string = f"user={username}\x01auth=Bearer {access_token}\x01\x01"

    encoded = base64.b64encode(
        auth_string.encode("utf-8")
    ).decode("ascii")

    code, response = server.docmd(
        "AUTH",
        "XOAUTH2 " + encoded
    )

    if code != 235:
        raise RuntimeError(
            f"Falha na autenticação OAuth: {code} {response!r}"
        )

def send_email(
    smtp_server,
    smtp_port,
    username,
    password,
    mail_from,
    mail_to,
    use_tls=True,
    subject="Test Email",
    body=TEXT_MAIL
):
    try:
        message = EmailMessage()

        message["Subject"] = subject
        message["From"] = mail_from
        message["To"] = mail_to

        message.set_content(body, charset="utf-8")

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            if use_tls:
                server.starttls()

            server.login(username, password)
            server.send_message(message)

        return True

    except Exception as e:
        print(f"Error sending test email: {e}")
        return False

def send_email_oauth2(
    smtp_server,
    smtp_port,
    username,
    mail_from,
    mail_to,
    client_id,
    client_secret,
    refresh_token,
    use_tls=True,
    subject="Test Email",
    body=TEXT_MAIL
):
    try:
        message = EmailMessage()

        message["Subject"] = subject
        message["From"] = mail_from
        message["To"] = mail_to

        message.set_content(body, charset="utf-8")
        access_token = get_google_access_token(
            client_id,
            client_secret,
            refresh_token,
        )

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            if use_tls:
                server.starttls()

            smtp_oauth2_auth(
                server,
                username,
                access_token,
            )

            server.send_message(message)

        return True

    except Exception as e:
        print(f"Error sending test email: {e}")
        return False  