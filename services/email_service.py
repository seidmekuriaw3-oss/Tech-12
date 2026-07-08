"""
Email Service — SEMIRA FASHION
Sends daily admin digest via SMTP (Gmail / any SMTP provider).

Required env vars:
  SMTP_USER   — sender Gmail address (e.g. yourstore@gmail.com)
  SMTP_PASS   — Gmail App Password (16 chars, no spaces)

Optional env vars (have sane defaults):
  SMTP_HOST   — default: smtp.gmail.com
  SMTP_PORT   — default: 587  (STARTTLS)
"""

import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def _smtp_cfg():
    return {
        'host': os.environ.get('SMTP_HOST', 'smtp.gmail.com'),
        'port': int(os.environ.get('SMTP_PORT', 587)),
        'user': os.environ.get('SMTP_USER', '').strip(),
        'password': os.environ.get('SMTP_PASS', '').strip(),
    }


def is_email_configured():
    cfg = _smtp_cfg()
    return bool(cfg['user'] and cfg['password'])


def send_email(to_addr: str, subject: str, html_body: str, text_body: str = '') -> bool:
    """
    Send one HTML email. Returns True on success, False on failure.
    Silently logs errors — never raises to callers.
    """
    cfg = _smtp_cfg()
    if not cfg['user'] or not cfg['password']:
        logger.warning(
            "Email not sent — SMTP_USER and SMTP_PASS are not configured. "
            "Set them in the Replit Secrets panel."
        )
        return False

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"SEMIRA FASHION <{cfg['user']}>"
        msg['To'] = to_addr

        if text_body:
            msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        with smtplib.SMTP(cfg['host'], cfg['port'], timeout=20) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(cfg['user'], cfg['password'])
            server.sendmail(cfg['user'], [to_addr], msg.as_string())

        logger.info(f"Email sent → {to_addr}: {subject}")
        return True

    except Exception as e:
        logger.error(f"Email send failed → {to_addr}: {e}")
        return False


def build_digest_html(data: dict) -> str:
    """
    Build the daily HTML digest email.
    data keys: date, new_orders, total_revenue, pending_orders,
               low_stock_products, ai_conversations, top_products
    """
    date_str     = data.get('date', datetime.now().strftime('%B %d, %Y'))
    new_orders   = data.get('new_orders', 0)
    revenue      = data.get('total_revenue', 0)
    pending      = data.get('pending_orders', 0)
    low_stock    = data.get('low_stock_products', [])
    ai_count     = data.get('ai_conversations', 0)
    top_products = data.get('top_products', [])

    # Low stock rows
    low_stock_rows = ''
    if low_stock:
        for p in low_stock[:8]:
            name = p.get('name') or p.get('name_am') or 'Unknown'
            qty  = p.get('stock_quantity', 0)
            thr  = p.get('low_stock_threshold', 5)
            color = '#dc2626' if qty <= 2 else '#d97706'
            low_stock_rows += f"""
            <tr>
              <td style="padding:8px 12px;border-bottom:1px solid #f3f4f6;">{name}</td>
              <td style="padding:8px 12px;border-bottom:1px solid #f3f4f6;text-align:center;
                         color:{color};font-weight:700;">{qty}</td>
              <td style="padding:8px 12px;border-bottom:1px solid #f3f4f6;text-align:center;
                         color:#6b7280;">{thr}</td>
            </tr>"""
    else:
        low_stock_rows = '<tr><td colspan="3" style="padding:12px;text-align:center;color:#6b7280;">✅ ሁሉም ምርቶች ጥሩ stock አላቸው</td></tr>'

    # Top products rows
    top_rows = ''
    for i, p in enumerate(top_products[:5], 1):
        name  = p.get('name') or p.get('name_am') or 'Unknown'
        count = p.get('order_count', 0)
        top_rows += f"""
        <tr>
          <td style="padding:8px 12px;border-bottom:1px solid #f3f4f6;">{i}.</td>
          <td style="padding:8px 12px;border-bottom:1px solid #f3f4f6;">{name}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #f3f4f6;text-align:center;
                     font-weight:700;color:#1D6F42;">{count}</td>
        </tr>"""
    if not top_rows:
        top_rows = '<tr><td colspan="3" style="padding:12px;text-align:center;color:#6b7280;">ትናንት ምንም ትዕዛዝ አልነበረም</td></tr>'

    return f"""<!DOCTYPE html>
<html lang="am">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SEMIRA Daily Digest</title></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:Arial,Helvetica,sans-serif;">

<table width="100%" cellpadding="0" cellspacing="0" style="background:#f3f4f6;padding:24px 0;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;">

  <!-- Header -->
  <tr><td style="background:#1D6F42;border-radius:12px 12px 0 0;padding:28px 32px;text-align:center;">
    <h1 style="margin:0;color:#fff;font-size:22px;letter-spacing:1px;">👗 SEMIRA FASHION</h1>
    <p style="margin:6px 0 0;color:#a7f3d0;font-size:14px;">Daily Admin Digest — {date_str}</p>
  </td></tr>

  <!-- Stats row -->
  <tr><td style="background:#fff;padding:24px 32px;">
    <table width="100%" cellpadding="0" cellspacing="0">
    <tr>
      <td width="25%" style="text-align:center;padding:0 8px;">
        <div style="background:#f0fdf4;border-radius:10px;padding:16px 8px;">
          <div style="font-size:28px;font-weight:700;color:#1D6F42;">{new_orders}</div>
          <div style="font-size:12px;color:#6b7280;margin-top:4px;">አዲስ ትዕዛዞች</div>
        </div>
      </td>
      <td width="25%" style="text-align:center;padding:0 8px;">
        <div style="background:#fffbeb;border-radius:10px;padding:16px 8px;">
          <div style="font-size:28px;font-weight:700;color:#d97706;">{pending}</div>
          <div style="font-size:12px;color:#6b7280;margin-top:4px;">Pending ትዕዛዞች</div>
        </div>
      </td>
      <td width="25%" style="text-align:center;padding:0 8px;">
        <div style="background:#eff6ff;border-radius:10px;padding:16px 8px;">
          <div style="font-size:20px;font-weight:700;color:#1d4ed8;">{revenue:,.0f}</div>
          <div style="font-size:12px;color:#6b7280;margin-top:4px;">ዕለታዊ ገቢ (ETB)</div>
        </div>
      </td>
      <td width="25%" style="text-align:center;padding:0 8px;">
        <div style="background:#fdf4ff;border-radius:10px;padding:16px 8px;">
          <div style="font-size:28px;font-weight:700;color:#7c3aed;">{ai_count}</div>
          <div style="font-size:12px;color:#6b7280;margin-top:4px;">AI ንግግሮች</div>
        </div>
      </td>
    </tr>
    </table>
  </td></tr>

  <!-- Low stock -->
  <tr><td style="background:#fff;padding:0 32px 24px;">
    <h2 style="font-size:15px;font-weight:700;color:#333;margin:0 0 12px;
               border-top:1px solid #f3f4f6;padding-top:20px;">
      ⚠️ ዝቅተኛ Stock ምርቶች
    </h2>
    <table width="100%" cellpadding="0" cellspacing="0"
           style="border:1px solid #f3f4f6;border-radius:8px;overflow:hidden;">
      <thead>
        <tr style="background:#f9fafb;">
          <th style="padding:9px 12px;text-align:left;font-size:12px;color:#6b7280;font-weight:600;">ምርት</th>
          <th style="padding:9px 12px;text-align:center;font-size:12px;color:#6b7280;font-weight:600;">Stock</th>
          <th style="padding:9px 12px;text-align:center;font-size:12px;color:#6b7280;font-weight:600;">Min</th>
        </tr>
      </thead>
      <tbody>{low_stock_rows}</tbody>
    </table>
  </td></tr>

  <!-- Top products -->
  <tr><td style="background:#fff;padding:0 32px 24px;">
    <h2 style="font-size:15px;font-weight:700;color:#333;margin:0 0 12px;
               border-top:1px solid #f3f4f6;padding-top:20px;">
      🔥 ትናንት ብዙ የተሸጡ ምርቶች
    </h2>
    <table width="100%" cellpadding="0" cellspacing="0"
           style="border:1px solid #f3f4f6;border-radius:8px;overflow:hidden;">
      <thead>
        <tr style="background:#f9fafb;">
          <th style="padding:9px 12px;text-align:left;font-size:12px;color:#6b7280;font-weight:600;">#</th>
          <th style="padding:9px 12px;text-align:left;font-size:12px;color:#6b7280;font-weight:600;">ምርት</th>
          <th style="padding:9px 12px;text-align:center;font-size:12px;color:#6b7280;font-weight:600;">ትዕዛዞች</th>
        </tr>
      </thead>
      <tbody>{top_rows}</tbody>
    </table>
  </td></tr>

  <!-- CTA -->
  <tr><td style="background:#fff;padding:0 32px 28px;text-align:center;">
    <a href="https://{os.environ.get('REPLIT_DEV_DOMAIN','semirafashion.com')}/admin"
       style="display:inline-block;background:#1D6F42;color:#fff;padding:13px 32px;
              border-radius:8px;text-decoration:none;font-weight:700;font-size:14px;">
      🚀 Admin Panel ክፈት
    </a>
  </td></tr>

  <!-- Footer -->
  <tr><td style="background:#f9fafb;border-radius:0 0 12px 12px;
                 padding:16px 32px;text-align:center;border-top:1px solid #f3f4f6;">
    <p style="margin:0;font-size:12px;color:#9ca3af;">
      SEMIRA FASHION — Daily Digest &bull; ሰሚራ ፋሽን &bull;
      <a href="https://{os.environ.get('REPLIT_DEV_DOMAIN','semirafashion.com')}/admin/ai-logs"
         style="color:#1D6F42;text-decoration:none;">AI Logs</a>
    </p>
  </td></tr>

</table>
</td></tr>
</table>
</body></html>"""


def build_digest_text(data: dict) -> str:
    date_str   = data.get('date', datetime.now().strftime('%B %d, %Y'))
    new_orders = data.get('new_orders', 0)
    revenue    = data.get('total_revenue', 0)
    pending    = data.get('pending_orders', 0)
    ai_count   = data.get('ai_conversations', 0)
    low_stock  = data.get('low_stock_products', [])

    lines = [
        f"SEMIRA FASHION — Daily Digest ({date_str})",
        "=" * 44,
        f"አዲስ ትዕዛዞች: {new_orders}",
        f"Pending ትዕዛዞች: {pending}",
        f"ዕለታዊ ገቢ: {revenue:,.0f} ETB",
        f"AI ንግግሮች: {ai_count}",
        "",
        "ዝቅተኛ Stock ምርቶች:",
    ]
    if low_stock:
        for p in low_stock[:8]:
            lines.append(f"  • {p.get('name','?')} — {p.get('stock_quantity',0)} ቀርቷል")
    else:
        lines.append("  ✅ ሁሉም ምርቶች ጥሩ stock አላቸው")
    return "\n".join(lines)
