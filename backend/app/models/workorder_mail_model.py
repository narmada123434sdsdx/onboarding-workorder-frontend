import os
import json
import base64
import traceback
from datetime import datetime

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from sqlalchemy import text

from app.models.database import db
from app.models.workorder import WorkOrder

# ----------------------------------------------------------------------
# SMTP Credentials
# ----------------------------------------------------------------------
EMAIL_USER = os.getenv("MAIL_USER")
EMAIL_PASS = os.getenv("MAIL_PASS")


# ----------------------------------------------------------------------
# Helper Functions
# ----------------------------------------------------------------------
def parse_requested_date(req_date):
    """Parse various date formats into datetime object."""
    if not req_date:
        return None
    if isinstance(req_date, datetime):
        return req_date
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"):
        try:
            return datetime.strptime(req_date, fmt)
        except ValueError:
            continue
    return None


def detect_image_type(img_bytes):
    """Detect image type from byte signature."""
    if not img_bytes:
        return "jpeg"
    if img_bytes[:2] == b'\xff\xd8':
        return 'jpeg'
    elif img_bytes[:8] == b'\x89PNG\r\n\x1a\n':
        return 'png'
    elif img_bytes[:6] in (b'GIF87a', b'GIF89a'):
        return 'gif'
    elif img_bytes[:4] == b'RIFF' and img_bytes[8:12] == b'WEBP':
        return 'webp'
    return 'jpeg'


def parse_image_field(image_field):
    """Parse image field which can be string, dict, list, or JSON."""
    images = []
    if not image_field:
        return images

    try:
        if isinstance(image_field, str):
            try:
                parsed = json.loads(image_field)
            except json.JSONDecodeError:
                images = [image_field]
            else:
                if isinstance(parsed, list):
                    images = parsed
                elif isinstance(parsed, dict):
                    for v in parsed.values():
                        if isinstance(v, list):
                            images.extend(v)
                        elif v:
                            images.append(v)
                else:
                    images = [parsed]
        elif isinstance(image_field, dict):
            for v in image_field.values():
                if isinstance(v, list):
                    images.extend(v)
                elif v:
                    images.append(v)
        elif isinstance(image_field, (list, tuple)):
            images = list(image_field)
        elif image_field:
            images = [image_field]
    except Exception as e:
        print(f"[ERROR] parse_image_field: {e}")
        traceback.print_exc()
    return images


def decode_image(img_entry):
    """Decode image from various sources: data URL, base64, file path, or bytes."""
    img_bytes = None
    filename = "image.jpg"

    try:
        # data URL
        if isinstance(img_entry, str) and img_entry.startswith("data:image"):
            header, b64_data = img_entry.split(",", 1)
            img_bytes = base64.b64decode(b64_data)
            if "jpeg" in header or "jpg" in header:
                filename = "image.jpg"
            elif "png" in header:
                filename = "image.png"
            elif "gif" in header:
                filename = "image.gif"

        # plain base64 string (large)
        elif isinstance(img_entry, str) and len(img_entry) > 100 and not img_entry.startswith("/"):
            try:
                img_bytes = base64.b64decode(img_entry)
            except Exception:
                img_bytes = None

        # file path under /uploads/
        if img_bytes is None and isinstance(img_entry, str) and img_entry.startswith("/uploads/"):
            possible_paths = [
                img_entry,
                img_entry.lstrip("/"),
                os.path.join(os.getcwd(), img_entry.lstrip("/")),
                os.path.join(os.path.dirname(os.path.dirname(__file__)), img_entry.lstrip("/")),
            ]
            for path in possible_paths:
                try:
                    if os.path.exists(path):
                        with open(path, "rb") as f:
                            img_bytes = f.read()
                        filename = os.path.basename(img_entry)
                        break
                except Exception:
                    continue

        # absolute path
        elif img_bytes is None and isinstance(img_entry, str) and os.path.exists(img_entry):
            with open(img_entry, "rb") as f:
                img_bytes = f.read()
            filename = os.path.basename(img_entry)

        # raw bytes
        elif isinstance(img_entry, (bytes, bytearray)):
            img_bytes = bytes(img_entry)

    except Exception as e:
        print(f"[ERROR] decode_image: {e}")
        traceback.print_exc()

    return img_bytes, filename


def attach_workorder_images(msg, msg_related, workorder, workorder_id):
    """Attach workorder images as both inline and attachment."""
    attached_count = 0
    total_size = 0
    image_field = getattr(workorder, "image", None) or getattr(workorder, "IMAGE", None)
    if not image_field:
        return attached_count, total_size

    images = parse_image_field(image_field)
    if not images:
        return attached_count, total_size

    for idx, entry in enumerate(images, start=1):
        try:
            img_bytes, base_name = decode_image(entry)
            if not img_bytes or len(img_bytes) < 50:
                continue

            img_type = detect_image_type(img_bytes)
            filename = f"workorder_{workorder_id}_image_{idx}.{img_type}"
            cid = f"image{idx}@workorder{workorder_id}"

            # Inline image for HTML <img src="cid:...">
            inline = MIMEImage(img_bytes, _subtype=img_type)
            inline.add_header('Content-Disposition', 'inline', filename=filename)
            inline.add_header('Content-ID', f'<{cid}>')
            inline.add_header('X-Attachment-Id', cid)
            msg_related.attach(inline)

            # Attachment copy
            attach = MIMEImage(img_bytes, _subtype=img_type)
            attach.add_header('Content-Disposition', 'attachment', filename=filename)
            msg.attach(attach)

            attached_count += 1
            total_size += len(img_bytes)
        except Exception as e:
            print(f"[ERROR] attach image #{idx}: {e}")
            traceback.print_exc()

    return attached_count, total_size


# ----------------------------------------------------------------------
# Database Operations
# ----------------------------------------------------------------------
def get_expiry_minutes_from_db(area):
    """Get expiry minutes for a specific area from link_expiry_t table."""
    try:
        result = db.session.execute(
            text("SELECT expiry_minutes FROM link_expiry_t WHERE area = :area LIMIT 1"),
            {"area": area},
        ).fetchone()
        return result.expiry_minutes if result else 15
    except Exception:
        return 15


def get_admin_emails_from_db():
    """
    Fetch admin emails from admins_t.
    Returns list of tuples: [(email, admin_name), ...]
    """
    try:
        rows = db.session.execute(
            text("SELECT email_id, admin_name FROM admins_t WHERE email_id IS NOT NULL")
        ).fetchall()
        admins = [(r.email_id, r.admin_name) for r in rows if r.email_id]
        print(f"[DEBUG] get_admin_emails: found {len(admins)} admins: {[a[0] for a in admins]}")
        return admins
    except Exception as e:
        print(f"[ERROR] get_admin_emails: {e}")
        traceback.print_exc()
        return []

def get_admin_email_by_id(admin_id):
    """
    Fetch admin email + name based on CREATED_BY value in workorder_t.
    Returns: (email, name) OR None if not found.
    """
    try:
        row = db.session.execute(
            text("""
                SELECT email_id, admin_name
                FROM admins_t
                WHERE "ADMIN_ID" = :aid
                LIMIT 1
            """),
            {"aid": admin_id}
        ).fetchone()

        if row:
            return (row.email_id, row.admin_name)

        return None

    except Exception as e:
        print(f"[ERROR] get_admin_email_by_id: {e}")
        traceback.print_exc()
        return None



def get_contractor_from_db(provider_id):
    """Fetch contractor details from providers_t table."""
    try:
        contractor = db.session.execute(
            text("SELECT full_name, email_id FROM providers_t WHERE provider_id = :pid"),
            {"pid": provider_id}
        ).fetchone()
        return contractor
    except Exception as e:
        print(f"[ERROR] get_contractor_from_db: {e}")
        traceback.print_exc()
        return None


def get_workorder_from_db(workorder_id):
    """Fetch workorder by ID."""
    try:
        return WorkOrder.query.get(workorder_id)
    except Exception as e:
        print(f"[ERROR] get_workorder_from_db: {e}")
        traceback.print_exc()
        return None


def insert_email_notification_log(workorder_number, sender_name, email_id, status):
    """Log email notification to email_notification_t table."""
    try:
        db.session.execute(
            text("""
            INSERT INTO email_notification_t ("WORKORDER","SENDER_NAME","EMAIL_ID","STATUS","DATE")
            VALUES (:wo,:sender,:email,:status,:date)
            """),
            {
                "wo": workorder_number,
                "sender": sender_name,
                "email": email_id,
                "status": status,
                "date": datetime.utcnow()
            }
        )
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"[WARN] insert_email_notification_log failed: {e}")


def insert_workorder_lifecycle_log(workorder, contractor_id, contractor_name, remark):
    """
    Insert a new record into workorder_life_cycle_t when contractor accepts/rejects.
    Matches table columns exactly.
    """
    try:
        requested_close = parse_requested_date(getattr(workorder, "REQUESTED_TIME_CLOSING", None))

        db.session.execute(text("""
            INSERT INTO workorder_life_cycle_t 
            (workorder, workorder_type, workorder_area, created_t, requested_time_closing, 
             remarks, status, contractor_name, contractor_id, contractor_remarks)
            VALUES 
            (:workorder, :type, :area, :created_t, :req_close, 
             :remarks, :status, :cname, :cid, :cremarks)
        """), {
            "workorder": workorder.WORKORDER,
            "type": workorder.WORKORDER_TYPE,
            "area": workorder.WORKORDER_AREA,
            "created_t": datetime.utcnow(),
            "req_close": requested_close,
            "remarks": workorder.REMARKS or None,
            "status": workorder.STATUS or None,
            "cname": contractor_name,
            "cid": contractor_id,
            "cremarks": remark or None
        })
        db.session.commit()
        print(f"[LIFECYCLE] Inserted lifecycle log for WO {workorder.WORKORDER}")

    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] insert_workorder_lifecycle_log: {e}")
        traceback.print_exc()


def update_workorder_status_in_db(workorder, status):
    """Update workorder status."""
    try:
        workorder.STATUS = status
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] update_workorder_status_in_db: {e}")
        raise


# ----------------------------------------------------------------------
# Email Sending Functions
# ----------------------------------------------------------------------
def build_assignment_email_html(workorder, contractor_name, response_url, expiry_minutes):
    """Build HTML content for assignment email with inline images."""
    workorder_id = workorder.ID
    
    # Parse images for inline display
    image_field = getattr(workorder, "image", None) or getattr(workorder, "IMAGE", None)
    images = parse_image_field(image_field)
    inline_html = ""
    if images:
        inline_html += '<div style="display:flex;flex-wrap:wrap;gap:15px;margin:20px 0;">'
        for i in range(len(images)):
            cid = f"image{i+1}@workorder{workorder_id}"
            inline_html += f'''
            <div style="border:2px solid #ddd;padding:10px;border-radius:8px;background:#f9f9f9;text-align:center;">
                <img src="cid:{cid}" style="max-width:280px;max-height:280px;display:block;border-radius:4px;" alt="Img {i+1}"/>
                <p style="margin:8px 0 0 0;font-size:13px;color:#666;">Image {i+1}</p>
            </div>'''
        inline_html += '</div>'

    html_body = f"""
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="font-family:Arial,sans-serif;line-height:1.6;color:#333;max-width:800px;margin:0 auto;padding:20px;">
        <div style="background:linear-gradient(135deg,#667eea,#764ba2);padding:20px;border-radius:8px;margin-bottom:20px;">
            <h2 style="margin:0;color:white;">Work Order Assignment</h2>
        </div>

        <div style="background:#f0f8ff;padding:15px;border-left:4px solid #007bff;margin-bottom:20px;">
            <h3 style="margin:0;color:#007bff;">Hello {contractor_name},</h3>
            <p style="margin:5px 0 0 0;">You have been assigned a new work order for area <strong>{workorder.WORKORDER_AREA}</strong>.</p>
        </div>

        <table border="1" cellspacing="0" cellpadding="12"
               style="border-collapse:collapse;width:100%;max-width:700px;margin-bottom:25px;border:1px solid #ddd;">
            <tr style="background:#f8f9fa;"><th align="left" style="width:40%;">Work Order</th>
                <td><strong>{workorder.WORKORDER}</strong></td></tr>
            <tr><th align="left" style="background:#f8f9fa;">Type</th><td>{workorder.WORKORDER_TYPE}</td></tr>
            <tr><th align="left" style="background:#f8f9fa;">Remarks</th><td>{workorder.REMARKS or 'N/A'}</td></tr>
            <tr><th align="left" style="background:#f8f9fa;">Requested Date</th>
                <td>{workorder.REQUESTED_TIME_CLOSING or 'N/A'}</td></tr>
        </table>

        {inline_html}

        <div style="margin:30px 0;text-align:center;padding:20px;background:#f8f9fa;border-radius:8px;">
            <p style="font-size:16px;margin-bottom:15px;color:#333;"><strong>Please respond:</strong></p>
            <a href="{response_url}"
               style="background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:14px 35px;
                      text-decoration:none;border-radius:6px;display:inline-block;font-size:16px;
                      font-weight:600;box-shadow:0 4px 6px rgba(0,0,0,.2);">
                Click Here to Confirm or Reject
            </a>
            <p style="margin-top:15px;font-size:13px;color:#dc3545;">
                Important: Link expires in <strong>{expiry_minutes}</strong> minutes.
            </p>
        </div>

        <hr style="border:none;border-top:1px solid #ddd;margin:30px 0;">
        <p style="font-size:12px;color:#777;text-align:center;">
            Automated e-mail – do not reply.
        </p>
    </body>
    </html>
    """
    return html_body


def send_email_with_attachments(workorder, contractor_email, contractor_name, html_body):
    """
    Send email with workorder images as attachments.
    Returns: (status_string, attached_count, attached_size)
    """
    workorder_id = workorder.ID
    
    msg = MIMEMultipart("mixed")
    msg["Subject"] = f"Work Order Assigned – {workorder.WORKORDER}"
    msg["From"] = EMAIL_USER or "no-reply@example.com"
    msg["To"] = contractor_email

    related = MIMEMultipart("related")
    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(html_body, "html"))
    related.attach(alt)

    attached_cnt, attached_sz = attach_workorder_images(msg, related, workorder, workorder_id)
    msg.attach(related)

    status = "UNSENT"
    try:
        if not EMAIL_USER or not EMAIL_PASS:
            raise RuntimeError("SMTP credentials missing")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as srv:
            srv.login(EMAIL_USER, EMAIL_PASS)
            srv.send_message(msg)
        status = "SENT"
    except Exception as e:
        status = f"FAILED: {str(e)[:80]}"
        print(f"[ERROR] send_email_with_attachments: {e}")
        traceback.print_exc()

    return status, attached_cnt, attached_sz


def build_admin_notification_html(workorder, contractor_name, contractor_id, action, remark):
    """Build HTML content for admin notification email."""
    status_text = "ACCEPTED" if action == "accept" else "REJECTED"
    status_color = "#28a745" if action == "accept" else "#dc3545"
    status_icon = "✓ Checkmark" if action == "accept" else "✗ Cross"

    html = f"""
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="font-family:Arial,sans-serif;line-height:1.6;color:#333;max-width:800px;margin:0 auto;padding:20px;">
        <div style="background:{status_color};padding:20px;border-radius:8px;margin-bottom:20px;">
            <h2 style="margin:0;color:white;">{status_icon} Work Order {status_text}</h2>
        </div>

        <div style="background:#f8f9fa;padding:15px;border-left:4px solid {status_color};margin-bottom:20px;">
            <p style="margin:5px 0 0 0;font-size:16px;">
                Contractor <strong>{contractor_name}</strong> has <strong>{status_text.lower()}</strong> the work order.
            </p>
        </div>

        <table border="1" cellspacing="0" cellpadding="12"
               style="border-collapse:collapse;width:100%;max-width:700px;margin-bottom:25px;border:1px solid #ddd;">
            <tr style="background:#f8f9fa;"><th align="left" style="width:40%;">Work Order</th>
                <td><strong>{workorder.WORKORDER}</strong></td></tr>
            <tr><th align="left" style="background:#f8f9fa;">Type</th><td>{workorder.WORKORDER_TYPE}</td></tr>
            <tr><th align="left" style="background:#f8f9fa;">Area</th><td>{workorder.WORKORDER_AREA}</td></tr>
            <tr><th align="left" style="background:#f8f9fa;">Contractor</th>
                <td>{contractor_name} (ID: {contractor_id})</td></tr>
            <tr><th align="left" style="background:#f8f9fa;">Status</th>
                <td style="color:{status_color};font-weight:bold;">{status_text}</td></tr>
            <tr><th align="left" style="background:#f8f9fa;">Response Date</th>
                <td>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
            {f'<tr><th align="left" style="background:#f8f9fa;">Remark</th><td>{remark}</td></tr>' if remark else ''}
        </table>

        <hr style="border:none;border-top:1px solid #ddd;margin:30px 0;">
        <p style="font-size:12px;color:#777;text-align:center;">
            Automated notification – do not reply.
        </p>
    </body>
    </html>
    """
    return html, status_text


def send_admin_notification_email(workorder, html_content, status_text, admins):
    """
    Send notification email to all admins (BCC).
    Returns: (success_count, failed_list)
    """
    admin_emails = [e for e, _ in admins]
    success = 0
    failed = []

    try:
        if not EMAIL_USER or not EMAIL_PASS:
            raise RuntimeError("MAIL_USER/MAIL_PASS not set")

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Work Order {status_text} – {workorder.WORKORDER}"
        msg["From"] = EMAIL_USER or "no-reply@example.com"
        msg["To"] = EMAIL_USER or "no-reply@example.com"
        if admin_emails:
            msg["Bcc"] = ", ".join(admin_emails)
        msg.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)

        print(f"[ADMIN] Notification sent (BCC) to: {admin_emails}")
        success = len(admin_emails)

        # Log each admin notification
        for email, name in admins:
            try:
                insert_email_notification_log(
                    workorder.WORKORDER,
                    f"Admin: {name}",
                    email,
                    f"ADMIN_NOTIFIED_{status_text}"
                )
            except Exception as log_e:
                print(f"[WARN] Failed to log notification for {email}: {log_e}")

    except Exception as e:
        print(f"[ADMIN] FAILED to send notifications: {e}")
        traceback.print_exc()
        failed = [(name, email, str(e)) for email, name in admins]

    return success, failed


def get_first_workorder_image(workorder):
    """Get first image data from workorder for serving."""
    field = getattr(workorder, "image", None) or getattr(workorder, "IMAGE", None)
    if not field:
        return None, None

    imgs = parse_image_field(field)
    if not imgs:
        return None, None

    img_bytes, _ = decode_image(imgs[0])
    if not img_bytes:
        return None, None

    img_type = detect_image_type(img_bytes)
    return img_bytes, img_type