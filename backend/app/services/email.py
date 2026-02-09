"""
Email service for sending password reset emails.
"""

import logging
from typing import Optional

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


def send_password_reset_email(email: str, reset_token: str) -> bool:
    """
    Send a password reset email.
    
    In development mode (email_console_mode=True), logs the reset link instead.
    In production mode, sends via SMTP.
    
    Args:
        email: Recipient email address
        reset_token: Password reset token
        
    Returns:
        True if email was sent/logged successfully
    """
    reset_url = f"{settings.frontend_url}?reset_token={reset_token}"
    
    if settings.email_console_mode:
        # Development mode - log to console
        logger.info("=" * 60)
        logger.info("PASSWORD RESET EMAIL (Console Mode)")
        logger.info(f"To: {email}")
        logger.info(f"Reset URL: {reset_url}")
        logger.info("=" * 60)
        print(f"\n[EMAIL] Password reset for {email}")
        print(f"[EMAIL] Reset URL: {reset_url}\n")
        return True
    
    # Production mode - send via SMTP
    if not settings.smtp_host:
        logger.error("SMTP not configured but email_console_mode is disabled")
        return False
    
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Password Reset Request"
        msg["From"] = settings.smtp_from_email
        msg["To"] = email
        
        # Plain text version
        text_content = f"""
Hello,

You have requested to reset your password. Click the link below to proceed:

{reset_url}

This link will expire in {settings.password_reset_expire_hours} hour(s).

If you did not request this reset, please ignore this email.
"""
        
        # HTML version
        html_content = f"""
<html>
  <body>
    <p>Hello,</p>
    <p>You have requested to reset your password. Click the link below to proceed:</p>
    <p><a href="{reset_url}">Reset Password</a></p>
    <p>This link will expire in {settings.password_reset_expire_hours} hour(s).</p>
    <p>If you did not request this reset, please ignore this email.</p>
  </body>
</html>
"""
        
        msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))
        
        # Send email
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            if settings.smtp_user and settings.smtp_password:
                server.starttls()
                server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_from_email, email, msg.as_string())
        
        logger.info(f"Password reset email sent to {email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send password reset email: {e}")
        return False
