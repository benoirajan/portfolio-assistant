import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from src.core.config import settings

logger = logging.getLogger("folioguard.services.email")


class EmailService:
    @staticmethod
    def send_verification_otp(email: str, otp: str) -> bool:
        """
        Dispatches a 6-digit email verification OTP.
        If SMTP credentials are provided, transmits via SMTP.
        Otherwise falls back to high-visibility console/dev logging.
        """
        smtp_configured = bool(
            settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD
        )

        if smtp_configured:
            try:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = f"Your FolioGuard Verification Code: {otp}"
                msg["From"] = settings.EMAILS_FROM
                msg["To"] = email

                text_content = (
                    f"Welcome to FolioGuard!\n\n"
                    f"Your 6-digit verification code is: {otp}\n\n"
                    f"This code will expire in 10 minutes. If you did not request this code, please ignore this email.\n"
                )
                html_content = f"""
                <html>
                  <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #f8fafc; padding: 32px;">
                    <div style="max-width: 480px; margin: 0 auto; background: #1e293b; border-radius: 16px; padding: 28px; border: 1px solid #334155;">
                      <h2 style="margin-top: 0; color: #38bdf8; font-size: 20px;">FolioGuard — Verify Your Email Address</h2>
                      <p style="color: #94a3b8; font-size: 14px; line-height: 1.5;">
                        Welcome to <strong>FolioGuard</strong>. Please enter the following 6-digit code to complete your verification and access your tenant-isolated portfolio:
                      </p>
                      <div style="background: #0f172a; border-radius: 12px; padding: 18px; text-align: center; margin: 24px 0; border: 1px solid #38bdf8;">
                        <span style="font-size: 32px; font-weight: 700; letter-spacing: 6px; color: #38bdf8; font-family: monospace;">{otp}</span>
                      </div>
                      <p style="color: #64748b; font-size: 12px; line-height: 1.4;">
                        This code expires in 10 minutes. If you did not sign up for FolioGuard, you can safely disregard this email.
                      </p>
                    </div>
                  </body>
                </html>
                """

                msg.attach(MIMEText(text_content, "plain"))
                msg.attach(MIMEText(html_content, "html"))

                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                    server.starttls()
                    clean_password = settings.SMTP_PASSWORD.replace(" ", "").strip('"\'')
                    server.login(settings.SMTP_USER, clean_password)
                    server.sendmail(settings.EMAILS_FROM, [email], msg.as_string())

                logger.info("Verification OTP email successfully dispatched via SMTP to %s", email)
                return True
            except Exception as e:
                logger.error("Failed to send SMTP verification email to %s: %s", email, e, exc_info=True)
                # Fall back to console logger
        
        # Dev fallback / console print
        print("\n" + "=" * 60)
        print("  [FOLIOGUARD — EMAIL VERIFICATION OTP]")
        print(f"  To:      {email}")
        print(f"  Code:    {otp}")
        print("  Expires: 10 minutes")
        print("=" * 60 + "\n")
        logger.info("[DEV MODE] Verification OTP for %s: %s (logged to console)", email, otp)
        return True


email_service = EmailService()
