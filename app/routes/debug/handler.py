from app.notifications.mail import Mail


def send_test_email(to_email):
    """
    Sends a test email to the specified email address.
    """
    try:
        mail = Mail()
        subject = "Test Email"
        body = "This is a test email sent from the application."
        mail.send(to_email, subject, body)
        return True, f"Test email sent successfully to {to_email}."
    except Exception as e:
        return False, f"Failed to send test email: {str(e)}"