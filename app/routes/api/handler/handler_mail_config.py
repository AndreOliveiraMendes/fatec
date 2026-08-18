import smtplib

TEXT_MAIL = f"""
Olá, este é um email de teste enviado pelo sistema.
se você recebeu este email, significa que a configuração de email está funcionando corretamente.
caso você não tenha solicitado este email, por favor, ignore-o.

atenciosamente, sistema de gerenciamento de reservas de recursos.
"""

def same_config(config, data):
    # Compare the relevant fields to determine if they are the same configuration
    return (
        config.get('smtp_server') == data.get('smtp_server') and
        config.get('smtp_port') == data.get('smtp_port') and
        config.get('username') == data.get('username') and
        config.get('mail_from') == data.get('mail_from') and
        config.get('use_tls') == data.get('use_tls')
    ) or config.get('id') == data.get('id')

def get_config_by_id(configs, config_id):
    mail_configs = configs.get("configs", [])
    return next((config for config in mail_configs if config.get("id") == config_id), None)

def send_test_email(smtp_server, smtp_port, username, password, mail_from, mail_to, use_tls=True, subject="Test Email", body=TEXT_MAIL):
    try:
        # Create the email headers and body
        message = f"Subject: {subject}\n\n{body}"

        # Connect to the SMTP server
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            if use_tls:
                server.starttls()  # Upgrade the connection to a secure encrypted SSL/TLS connection
            server.login(username, password)  # Log in to the SMTP server
            server.sendmail(mail_from, mail_to, message)  # Send the email

        return True  # Email sent successfully
    except Exception as e:
        print(f"Error sending test email: {e}")
        return False  # Email sending failed