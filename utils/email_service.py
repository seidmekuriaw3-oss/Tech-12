"""
Email Service for Semira Fashion.
Sends transactional emails via SMTP.

Required env vars (set in Replit Secrets):
  SMTP_HOST   — SMTP server (e.g. smtp.gmail.com)
  SMTP_PORT   — SMTP port  (e.g. 587)
  SMTP_USER   — SMTP login / from address
  SMTP_PASS   — SMTP password (Gmail: use an App Password)
  STORE_NAME  — Display name in From header (default: Semira Fashion)
"""

import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


def _get_smtp_config():
    """Return SMTP config dict, or None if not fully configured."""
    host = os.environ.get('SMTP_HOST', '').strip()
    user = os.environ.get('SMTP_USER', '').strip()
    passwd = os.environ.get('SMTP_PASS', '').strip()
    if not (host and user and passwd):
        return None
    return {
        'host': host,
        'port': int(os.environ.get('SMTP_PORT', '587')),
        'user': user,
        'password': passwd,
        'from_name': os.environ.get('STORE_NAME', 'Semira Fashion'),
    }


def send_email(to_email: str, subject: str, html_body: str, text_body: str = '') -> bool:
    """
    Send an email.  Returns True on success, False if SMTP not configured or on error.
    """
    cfg = _get_smtp_config()
    if not cfg:
        logger.warning("[email_service] SMTP not configured — email not sent to %s", to_email)
        return False

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{cfg['from_name']} <{cfg['user']}>"
        msg['To'] = to_email

        if text_body:
            msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        with smtplib.SMTP(cfg['host'], cfg['port'], timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.login(cfg['user'], cfg['password'])
            server.sendmail(cfg['user'], [to_email], msg.as_string())

        logger.info("[email_service] Email sent to %s — %s", to_email, subject)
        return True

    except Exception as e:
        logger.error("[email_service] Failed to send to %s: %s", to_email, e)
        return False


def send_password_reset_email(to_email: str, user_name: str, reset_url: str) -> bool:
    """Send a password-reset email.  Returns True on success."""
    store_name = os.environ.get('STORE_NAME', 'Semira Fashion')

    subject = f"Password Reset — {store_name}"

    html_body = f"""
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f5f5;padding:40px 20px;">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.08);">

        <!-- Header -->
        <tr><td style="background:linear-gradient(135deg,#1a7a4a,#0f5232);padding:32px 40px;text-align:center;">
          <p style="margin:0;font-size:40px;">👗</p>
          <h1 style="margin:8px 0 0;color:#fff;font-size:22px;font-weight:700;">{store_name}</h1>
        </td></tr>

        <!-- Body -->
        <tr><td style="padding:40px;">
          <h2 style="margin:0 0 16px;color:#1a7a4a;font-size:20px;">Reset Your Password</h2>
          <p style="margin:0 0 12px;color:#555;font-size:15px;line-height:1.6;">
            Hello <strong>{user_name}</strong>,
          </p>
          <p style="margin:0 0 24px;color:#555;font-size:15px;line-height:1.6;">
            We received a request to reset the password for your account.
            Click the button below to choose a new password.
            This link is valid for <strong>1 hour</strong>.
          </p>

          <!-- CTA Button -->
          <table cellpadding="0" cellspacing="0" width="100%"><tr><td align="center" style="padding:8px 0 32px;">
            <a href="{reset_url}"
               style="display:inline-block;background:linear-gradient(135deg,#1a7a4a,#0f5232);
                      color:#fff;text-decoration:none;padding:14px 36px;border-radius:10px;
                      font-size:16px;font-weight:600;letter-spacing:0.3px;">
              Reset Password
            </a>
          </td></tr></table>

          <p style="margin:0 0 8px;color:#888;font-size:13px;">If the button doesn't work, copy and paste this link:</p>
          <p style="margin:0 0 24px;word-break:break-all;">
            <a href="{reset_url}" style="color:#1a7a4a;font-size:13px;">{reset_url}</a>
          </p>

          <hr style="border:none;border-top:1px solid #eee;margin:0 0 20px;">
          <p style="margin:0;color:#aaa;font-size:12px;line-height:1.5;">
            If you didn't request a password reset, you can safely ignore this email —
            your password will not be changed.<br>
            For security, this link expires in 1 hour.
          </p>
        </td></tr>

        <!-- Footer -->
        <tr><td style="background:#f9f9f9;padding:20px 40px;text-align:center;">
          <p style="margin:0;color:#bbb;font-size:12px;">&copy; {store_name}. All rights reserved.</p>
        </td></tr>

      </table>
    </td></tr>
  </table>
</body>
</html>
"""

    text_body = (
        f"Reset Your Password — {store_name}\n\n"
        f"Hello {user_name},\n\n"
        f"Click the link below to reset your password (valid 1 hour):\n"
        f"{reset_url}\n\n"
        f"If you didn't request this, ignore this email.\n\n"
        f"— {store_name}"
    )

    return send_email(to_email, subject, html_body, text_body)
