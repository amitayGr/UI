"""
email_utils.py
-------------
Description:
    Email utility module for the Geometric Learning System. Handles all email-related
    functionality, particularly for password reset operations. Uses Mailtrap for email
    delivery in development environment.

Main Components:
    - Token Generation: Secure token creation for password resets
    - Email Formatting: HTML email template creation
    - Email Sending: SMTP connection and email delivery

Author: Karin Hershko and Afik Dadon
Date: February 2025
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import secrets

class EmailUtils:
    """ Utility class for handling email operations in the application.
    All methods are static as this class serves as a namespace for email-related functions."""

    # SMTP Configuration
    SMTP_SERVER = "sandbox.smtp.mailtrap.io"
    SMTP_PORT = 2525
    SMTP_USERNAME = "a2769d763a80f3"
    SMTP_PASSWORD = "a79000ef963db9"
    SENDER_EMAIL = "noreply@geometricakinator.com"

    @staticmethod
    def generate_reset_token() -> str:
        """Generate a secure random token for password reset."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def get_token_expiry() -> datetime:
        """Get expiry time for reset token (1 hour from now)."""
        return datetime.now() + timedelta(hours=1)

    @staticmethod
    def send_reset_email(email: str, reset_token: str) -> bool:
        """Send password reset email using configured SMTP server."""
        # Prepare email message
        msg = MIMEMultipart()
        msg['From'] = EmailUtils.SENDER_EMAIL
        msg['To'] = email
        msg['Subject'] = "איפוס סיסמה - Geometric Akinator"

        # Generate reset link
        reset_link = f"http://127.0.0.1:10000/login/reset-password/{reset_token}"

        # Create HTML email template
        body = EmailUtils._create_email_template(reset_link)
        msg.attach(MIMEText(body, 'html', 'utf-8'))

        # Send email
        try:
            server = smtplib.SMTP(EmailUtils.SMTP_SERVER, EmailUtils.SMTP_PORT)
            server.login(EmailUtils.SMTP_USERNAME, EmailUtils.SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
            return True
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False

    @staticmethod
    def _create_email_template(reset_link: str) -> str:
        """Create HTML template for reset password email."""
        return f"""
            <html>
                <body style="margin: 0; padding: 0; background-color: #f5f5f5; font-family: Arial, sans-serif;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; margin: 20px auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <tr>
                            <td style="padding: 40px 30px;" dir="rtl">
                                <table border="0" cellpadding="0" cellspacing="0" width="100%">
                                    <tr>
                                        <td style="text-align: center; padding-bottom: 30px;">
                                            <h1 style="color: #3F4D57; margin: 0; font-size: 24px;">איפוס סיסמה</h1>
                                        </td>
                                    </tr>
                                </table>

                                <table border="0" cellpadding="0" cellspacing="0" width="100%">
                                    <tr>
                                        <td style="padding: 20px 0 5px 0; text-align: right;">
                                            <p style="color: #666666; font-size: 16px; line-height: 1.5; margin: 0 0 20px;">שלום,</p>
                                            <p style="color: #666666; font-size: 16px; line-height: 1.5; margin: 0;">קיבלנו בקשה לאיפוס הסיסמה שלך בGeometric Akinator.</p>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 5px 0 20px 0; text-align: center;">
                                            <a href="{reset_link}">
                                                <img src="http://127.0.0.1:10000/static/media/reset password.png" 
                                                     alt="איפוס סיסמה" 
                                                     style="max-width: 200px; height: auto; cursor: pointer;">
                                            </a>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 20px 0; text-align: right;">
                                            <p style="color: #666666; font-size: 14px; line-height: 1.5; margin: 0 0 10px;">הקישור תקף למשך שעה אחת.</p>
                                            <p style="color: #666666; font-size: 14px; line-height: 1.5; margin: 0;">אם לא ביקשת לאפס את הסיסמה, אנא התעלם מהודעה זו.</p>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    </table>
                </body>
            </html>
            """