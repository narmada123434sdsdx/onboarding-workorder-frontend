import traceback
from time import time
from urllib.parse import quote, unquote
from datetime import datetime
import os

from app.models.database import db
from app.models.workorder_mail_model import (
    get_contractor_from_db,
    get_workorder_from_db,
    get_expiry_minutes_from_db,
    get_admin_emails_from_db,
    build_assignment_email_html,
    send_email_with_attachments,
    build_admin_notification_html,
    send_admin_notification_email,
    insert_email_notification_log,
    insert_workorder_lifecycle_log,
    update_workorder_status_in_db,
    get_first_workorder_image
)


# ----------------------------------------------------------------------
# CONTROLLER FUNCTIONS
# ----------------------------------------------------------------------

def handle_send_acceptance_mail(workorder_id, request_data, base_url):
    """
    Controller for sending assignment email to contractor.
    Returns: dict with response data and status code
    """
    try:
        print(f"\n{'='*60}")
        print(f"[START] handle_send_acceptance_mail – WO {workorder_id}")
        print(f"{'='*60}")

        # Validate request data
        if not request_data:
            return {"error": "Invalid JSON"}, 400

        provider_id = request_data.get("CONTRACTOR_ID")
        sender_name = request_data.get("SENDER_NAME", "System")
        if not provider_id:
            return {"error": "CONTRACTOR_ID missing"}, 400

        # Get contractor details
        contractor = get_contractor_from_db(provider_id)
        if not contractor:
            return {"error": "Contractor not found"}, 404
        contractor_name, contractor_email = contractor.full_name, contractor.email_id

        # Get workorder
        workorder = get_workorder_from_db(workorder_id)
        if not workorder:
            return {"error": "Work order not found"}, 404

        # Generate response URL with expiry
        expiry_minutes = get_expiry_minutes_from_db(workorder.WORKORDER_AREA)
        ts = int(time())
        
        # *** FIX: Use PUBLIC_BASE_URL from environment ***
        public_base_url = os.getenv("PUBLIC_BASE_URL", base_url)
        print(f"[INFO] Using public URL: {public_base_url}")
        
        response_url = (
            f"{public_base_url}/api/workorders/respond-workorder/{workorder_id}"
            f"?contractor_id={provider_id}&contractor_name={quote(contractor_name)}&timestamp={ts}"
        )
        print(f"[INFO] Generated URL: {response_url}")

        # Rest of the code stays the same...

        # Build email HTML
        html_body = build_assignment_email_html(
            workorder=workorder,
            contractor_name=contractor_name,
            response_url=response_url,
            expiry_minutes=expiry_minutes
        )

        # Send email with attachments
        status, attached_cnt, attached_sz = send_email_with_attachments(
            workorder=workorder,
            contractor_email=contractor_email,
            contractor_name=contractor_name,
            html_body=html_body
        )

        # Log notification
        insert_email_notification_log(
            workorder.WORKORDER,
            contractor_name,
            contractor_email,
            status
        )

        return {
            "message": f"Email sent to {contractor_email}",
            "attachments_count": attached_cnt,
            "attachments_size_bytes": attached_sz,
            "status": status,
            "workorder": workorder.WORKORDER
        }, 200

    except Exception as e:
        db.session.rollback()
        print(f"[FATAL] handle_send_acceptance_mail: {e}")
        traceback.print_exc()
        return {"error": str(e)}, 500


def handle_get_workorder_image(workorder_id):
    """
    Controller for serving workorder image.
    Returns: tuple (image_bytes, image_type) or (error_html, status_code)
    """
    workorder = get_workorder_from_db(workorder_id)
    if not workorder:
        return "<h3>Workorder not found</h3>", 404

    img_bytes, img_type = get_first_workorder_image(workorder)
    
    if not img_bytes:
        return "<h3>No image available</h3>", 404

    return img_bytes, img_type


def handle_respond_workorder_get(workorder_id, contractor_id, contractor_name, timestamp):
    """
    Controller for GET request - display response form.
    Returns: tuple (html_content, status_code) or error tuple
    """
    workorder = get_workorder_from_db(workorder_id)
    if not workorder:
        return "<h3>Work order not found</h3>", 404

    # Validate timestamp
    if not timestamp or not timestamp.isdigit():
        return "<h3>Invalid timestamp</h3>", 400

    # Check link expiry
    ts = int(timestamp)
    now = int(time())
    expiry = get_expiry_minutes_from_db(workorder.WORKORDER_AREA)
    if now - ts > expiry * 60:
        return f"""
        <html><body style="font-family:Arial;text-align:center;padding:50px;">
        <h3 style="color:#dc3545;">Link Expired</h3>
        <p>Valid for {expiry} minutes only.</p>
        </body></html>
        """, 403

    # Generate response form
    html = f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width,initial-scale=1">
        <style>
            body{{font-family:Arial;background:linear-gradient(135deg,#667eea,#764ba2);display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0;padding:20px;}}
            .box{{background:#fff;padding:40px;border-radius:10px;box-shadow:0 10px 25px rgba(0,0,0,.2);max-width:600px;width:100%;}}
            h3{{color:#333;margin-top:0;}}
            .wo{{background:#f8f9fa;padding:15px;border-radius:5px;margin:20px 0;border-left:4px solid #667eea;}}
            textarea{{width:100%;padding:12px;border:2px solid #ddd;border-radius:6px;font-family:Arial;font-size:14px;resize:vertical;box-sizing:border-box;}}
            textarea:focus{{outline:none;border-color:#667eea;}}
            .btns{{display:flex;gap:15px;margin-top:20px;}}
            button{{flex:1;padding:14px 30px;border:none;border-radius:6px;cursor:pointer;font-size:16px;font-weight:600;transition:.3s;}}
            .accept{{background:#28a745;color:#fff;}}
            .accept:hover{{background:#218838;transform:translateY(-2px);box-shadow:0 4px 8px rgba(40,167,69,.3);}}
            .reject{{background:#dc3545;color:#fff;}}
            .reject:hover{{background:#c82333;transform:translateY(-2px);box-shadow:0 4px 8px rgba(220,53,69,.3);}}
            label{{display:block;margin-bottom:8px;font-weight:600;color:#555;}}
        </style>
    </head>
    <body>
        <div class="box">
            <h3>Respond to Work Order</h3>
            <div class="wo"><strong>WO ID:</strong> {workorder.WORKORDER}</div>
            <form method="POST">
                <label>Remark (optional):</label>
                <textarea name="remark" rows="4" placeholder="Any comments…"></textarea>
                <div class="btns">
                    <button type="submit" name="action" value="accept" class="accept">Accept</button>
                    <button type="submit" name="action" value="reject" class="reject">Reject</button>
                </div>
            </form>
        </div>
    </body>
    </html>
    """
    return html, 200


def handle_respond_workorder_post(workorder_id, contractor_id, contractor_name, timestamp, action, remark):
    """
    Controller for POST request - process accept/reject action.
    Returns: tuple (html_content, status_code)
    """
    workorder = get_workorder_from_db(workorder_id)
    if not workorder:
        return "<h3>Work order not found</h3>", 404

    # Validate timestamp
    if not timestamp or not timestamp.isdigit():
        return "<h3>Invalid timestamp</h3>", 400

    # Check link expiry
    ts = int(timestamp)
    now = int(time())
    expiry = get_expiry_minutes_from_db(workorder.WORKORDER_AREA)
    if now - ts > expiry * 60:
        return f"""
        <html><body style="font-family:Arial;text-align:center;padding:50px;">
        <h3 style="color:#dc3545;">Link Expired</h3>
        <p>Valid for {expiry} minutes only.</p>
        </body></html>
        """, 403

    # Update workorder status
    status = "Accepted" if action == "accept" else "Rejected"
    update_workorder_status_in_db(workorder, status)

    # Log lifecycle
    insert_workorder_lifecycle_log(
        workorder=workorder,
        contractor_id=contractor_id,
        contractor_name=contractor_name,
        remark=remark
    )

    # Send admin notification
    # Send admin notification
    try:
        # Get admin who created this workorder
        creator_id = workorder.created_by
  # <--- workorder IS available here
        from app.models.workorder_mail_model import get_admin_email_by_id

        creator_admin = get_admin_email_by_id(creator_id)

        if creator_admin:
            admin_email, admin_name = creator_admin

            print(f"\n{'='*60}")
            print(f"[ADMIN NOTIFY] ONLY CREATOR NOTIFIED – WO {workorder.WORKORDER}")
            print(f"{'='*60}")

            # Build email HTML for admin
            html_content, status_text = build_admin_notification_html(
                workorder=workorder,
                contractor_name=contractor_name,
                contractor_id=contractor_id,
                action=action,
                remark=remark
            )

            # Send mail to only the creator admin
            msg_status, _, _ = send_email_with_attachments(
                workorder=workorder,
                contractor_email=admin_email,
                contractor_name=admin_name,
                html_body=html_content   # <--- FIXED
            )

            print(f"[ADMIN EMAIL] Sent to creator admin: {admin_email}")

        else:
            print("[WARN] No matching admin found for CREATED_BY")

    except Exception as e:
        print(f"[ERROR] Admin notify failed: {e}")
        traceback.print_exc()

    # Generate success page
    color = "#28a745" if action == "accept" else "#dc3545"
    icon = "✓" if action == "accept" else "✗"
    status_text = "Accepted" if action == "accept" else "Rejected"
    
    html = f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width,initial-scale=1">
        <style>
            body{{font-family:Arial;background:linear-gradient(135deg,#667eea,#764ba2);display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0;padding:20px;}}
            .box{{background:#fff;padding:40px;border-radius:10px;box-shadow:0 10px 25px rgba(0,0,0,.2);max-width:600px;width:100%;text-align:center;}}
            .icon{{font-size:64px;margin-bottom:20px;}}
            h3{{color:{color};margin:10px 0;}}
            .info{{background:#f8f9fa;padding:15px;border-radius:5px;margin:20px 0;border-left:4px solid {color};}}
        </style>
    </head>
    <body>
        <div class="box">
            <div class="icon">{icon}</div>
            <h3>Work Order {status_text}</h3>
            <div class="info"><strong>WO:</strong> {workorder.WORKORDER}</div>
            <p>Your response has been recorded.</p>
            <p>Administrators have been notified.</p>
            {f'<p><strong>Remark:</strong> {remark}</p>' if remark else ''}
            <p style="font-size:14px;color:#777;margin-top:30px;">Thank you!</p>
        </div>
    </body>
    </html>
    """
    return html, 200