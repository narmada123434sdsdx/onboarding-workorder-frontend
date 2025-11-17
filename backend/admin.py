# admin.py (Updated for .env)
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import psycopg2
import psycopg2.extras
import bcrypt
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import uuid
import json
from fpdf import FPDF
from datetime import datetime
import os
import pandas as pd
from dotenv import load_dotenv   # ✅ new import

# ---------------------- Load Environment ----------------------
load_dotenv()

# ---------------------- Config from .env ----------------------
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}

EMAIL_CONFIG = {
    'sender_email': os.getenv('SMTP_USER'),
    'sender_password': os.getenv('SMTP_PASSWORD'),
    'smtp_server': os.getenv('SMTP_HOST'),
    'smtp_port': int(os.getenv('SMTP_PORT', 587))
}

ADMIN_EMAIL = os.getenv('FROM_EMAIL', 'admin@ontract.com')

# ---------------------- Flask App ----------------------
app = Flask(__name__)
CORS(app,
     resources={r"/api/*": {"origins": os.getenv('ALLOWED_ORIGINS', 'http://localhost:5173')}},
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

# ---------------------- Upload Configuration ----------------------
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ---------------------- DB CONNECTION ----------------------
def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

# ---------------------- EMAIL UTILITY ----------------------
def send_email(to_email, subject, body, attachment=None):
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = EMAIL_CONFIG['sender_email']
    msg['To'] = to_email
    msg.attach(MIMEText(body))

    if attachment:
        with open(attachment, 'rb') as f:
            part = MIMEApplication(f.read(), Name=os.path.basename(attachment))
        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment)}"'
        msg.attach(part)

    try:
        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False


def send_admin_otp_email(email, otp):
    subject = "Your Ontract Admin OTP Code"
    body = f"""
    Dear Admin,

    Your One-Time Password (OTP) for logging in to your Ontract admin account is {otp}.

    Please enter this code to complete your login process.
    This OTP is valid for 5 minutes. For your security, do not share this code with anyone.

    Thank you,
    Ontract
    """
    return send_email(email, subject, body.strip())

# ---------------------- PDF GENERATION (Updated for new schema) ----------------------
def generate_pdf(details, email):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=False, margin=15)
    pdf.add_page()

    def draw_template():
        pdf.set_line_width(1)
        pdf.set_draw_color(41, 128, 185)
        pdf.rect(10, 10, 277, 190)
        pdf.set_draw_color(52, 152, 219)
        pdf.rect(15, 15, 267, 180)
        pdf.set_fill_color(41, 128, 185)
        pdf.rect(15, 15, 267, 35, 'F')

        pdf.set_font("Arial", 'B', 28)
        pdf.set_text_color(255, 255, 255)
        pdf.set_xy(15, 25)
        pdf.cell(267, 15, "Jlink Provider Certificate", 0, 1, 'C')

        cert_id = f"POV{random.randint(1000, 9999)}"
        pdf.set_font("Arial", 'I', 12)
        pdf.set_xy(15, 42)
        pdf.cell(267, 6, f"Certificate ID: {cert_id}", 0, 1, 'C')

        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", 'I', 14)
        pdf.set_xy(15, 60)
        pdf.cell(267, 8, "This certifies that the following provider has been registered", 0, 1, 'C')

    draw_template()

    pdf.set_font("Arial", '', 12)
    y_position = 78
    left_margin = 50

    for key, value in details.items():
        if key == "Provider ID":
            continue

        if y_position > 175:
            pdf.add_page()
            draw_template()
            y_position = 78

        pdf.set_xy(left_margin, y_position)
        pdf.set_font("Arial", 'B', 12)
        pdf.set_text_color(41, 128, 185)
        pdf.cell(60, 8, f"{key}:", 0, 0, 'L')

        pdf.set_font("Arial", '', 12)
        pdf.set_text_color(0, 0, 0)

        if key == "Services" and isinstance(value, list):
            for svc in value:
                if y_position > 175:
                    pdf.add_page()
                    draw_template()
                    y_position = 78
                # Updated: Use city (or full location) instead of service_location
                location = svc.get('Service Location')
  # Fallback to city; could be f"{svc.get('region')}, {svc.get('state')}, {svc.get('city')}"
                svc_text = f"- {svc['Service Name']} - Rs.{svc['Service Rate']} ({location})"
                pdf.set_xy(left_margin + 60, y_position)
                pdf.cell(0, 8, svc_text.encode('latin-1', 'replace').decode('latin-1'), 0, 1, 'L')
                y_position += 8
        else:
            pdf.cell(0, 8, str(value)[:100], 0, 1, 'L')
            y_position += 12

    pdf.set_font("Arial", 'I', 10)
    pdf.set_text_color(100, 100, 100)
    pdf.set_xy(15, 170)
    issue_date = datetime.now().strftime("%B %d, %Y")
    pdf.cell(133, 6, f"Issued on: {issue_date}", 0, 0, 'L')

    pdf.set_xy(180, 165)
    pdf.line(180, 170, 250, 170)
    pdf.set_xy(180, 171)
    pdf.cell(70, 6, "Authorized Signature", 0, 1, 'C')

    safe_email = email.replace('@', '_').replace('.', '_')
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{safe_email}_certificate.pdf")
    pdf.output(pdf_path)
    return pdf_path

# ---------------------- ADMIN LOGIN ----------------------
@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cursor.execute("SELECT password_hash FROM admins WHERE email = %s", (email,))
        admin = cursor.fetchone()
        if admin and bcrypt.checkpw(password.encode(), admin['password_hash'].encode()):
            otp = ''.join(random.choices(string.digits, k=6))
            cursor.execute("INSERT INTO otp_codes ( email_id, otp_code, created_at) VALUES (%s, %s, NOW())",
                           (email, otp))
            conn.commit()
            if send_admin_otp_email(email, otp):
                return jsonify({"message": "OTP sent to email"}), 200
            else:
                cursor.execute("DELETE FROM otp_codes WHERE email_id = %s", (email,))
                conn.commit()
                return jsonify({"error": "Failed to send OTP"}), 500
        return jsonify({"error": "Invalid credentials"}), 401
    except psycopg2.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

# ---------------------- VERIFY OTP ----------------------
@app.route('/api/admin/verify_otp', methods=['POST'])
def verify_admin_otp():
    data = request.get_json()
    email = data.get('email')
    otp = data.get('otp')

    if not email or not otp:
        return jsonify({"error": "Email and OTP required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cursor.execute("""
            SELECT otp_code FROM otp_codes 
            WHERE email_id = %s AND created_at > NOW() - INTERVAL '5 minutes'
            ORDER BY created_at DESC LIMIT 1
        """, (email,))
        record = cursor.fetchone()

        if record and record['otp_code'] == otp:
            cursor.execute("DELETE FROM otp_codes WHERE email_id = %s", (email,))
            conn.commit()
            return jsonify({"message": "OTP verified successfully", "admin_email": email}), 200
        else:
            return jsonify({"error": "Invalid or expired OTP"}), 401
    except psycopg2.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

# ---------------------- GET PROVIDERS (Updated for new schema) ----------------------
@app.route('/api/admin/providers', methods=['GET'])
def get_providers():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cursor.execute("""
            SELECT provider_id, full_name, email_id, contact_number, status, id_type, id_number, 
                   mailing_address, billing_address, alternate_contact_number, tin_number
            FROM providers
            ORDER BY created_at DESC
        """)
        providers = cursor.fetchall()

        # Convert each DictRow → normal dict
        providers = [dict(row) for row in providers]

        provider_ids = [p['provider_id'] for p in providers]

        if provider_ids:
            # Updated: Fetch from new columns (region, state, city)
            cursor.execute("""
                SELECT provider_id, service_name, service_rate, region, state, city
                FROM provider_services
                WHERE provider_id = ANY(%s)
                ORDER BY provider_id, service_name
            """, (provider_ids,))
            services_rows = cursor.fetchall()

            # Group services by provider_id as array of objects (matches new format)
            services_map = {}
            for row in services_rows:
                pid = row['provider_id']
                if pid not in services_map:
                    services_map[pid] = []
                # Create location string for legacy compatibility (e.g., "Kuala Lumpur")
                location = f"{row['city']}, {row['state']}, {row['region']}".strip(", ").replace(", N/A", "").replace("N/A", "")
                services_map[pid].append({
                    "service_name": row['service_name'],
                    "service_rate": float(row['service_rate']),
                    "region": row['region'] or '',
                    "state": row['state'] or '',
                    "city": row['city'] or '',
                    "service_location": location or 'N/A'  # Legacy field for PDF/UI
                })

        # Enrich providers with services array
        for provider in providers:
            pid = provider['provider_id']
            provider['services'] = services_map.get(pid, [])  # Now an array
            # For quick summary (legacy string)
            all_locs = [s.get('service_location', 'N/A') for s in provider['services']]
            provider['service_locations'] = ", ".join(sorted(set(all_locs))) if all_locs and all_locs != ['N/A'] else "N/A"

        return jsonify(providers), 200

    except psycopg2.Error as err:
        print(f"Database error in get_providers: {err}")  # Debug log
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

# ---------------------- APPROVE PROVIDER (Updated query) ----------------------
@app.route('/api/admin/approve_provider', methods=['POST'])
def approve_provider():
    data = request.get_json()
    email = data.get('email')
    if not email:
        return jsonify({"error": "Email required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cursor.execute("UPDATE providers SET status='approved' WHERE email_id=%s AND status='pending'", (email,))
        conn.commit()

        if cursor.rowcount > 0:
            cursor.execute("""
                SELECT provider_id, full_name, contact_number
                FROM providers
                WHERE email_id=%s
            """, (email,))
            provider = cursor.fetchone()
            provider_id = provider['provider_id']

            # Updated: Use new columns for services
            cursor.execute("""
                SELECT service_name, service_rate, state -- Use city as location; add state/region if needed
                FROM provider_services WHERE provider_id=%s
            """, (provider_id,))
            services = cursor.fetchall()

            details = {
                "Provider ID": provider_id,
                "Full Name": provider['full_name'],
                "Email": email,
                "Phone Number": provider['contact_number'],
                "Services": [{"Service Name": s['service_name'], "Service Rate": s['service_rate'], "Service Location": s['state'] or 'N/A'} for s in services]
            }

            pdf_path = generate_pdf(details, email)

            # Insert notification
            approval_message = "Your provider profile has been approved. You can now submit your bank details."
            cursor.execute("""
                INSERT INTO admin_messages ( email_id, message, sent_at, is_read, notification_type)
                VALUES ( %s, %s, NOW(), %s, %s)
            """, ( email, approval_message, False, 'approval'))
            conn.commit()

            email_body = approval_message
            if send_email(email, "Profile Approved", email_body, pdf_path):
                os.remove(pdf_path)
                return jsonify({"message": "Provider approved"}), 200
            else:
                os.remove(pdf_path)
                return jsonify({"error": "Provider approved but failed to send email and certificate"}), 500
        else:
            return jsonify({"error": "Provider not found or not pending"}), 404
    except psycopg2.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

# ---------------------- REJECT PROVIDER ----------------------
@app.route('/api/admin/reject_provider', methods=['POST'])
def reject_provider():
    data = request.get_json()
    email = data.get('email')
    if not email:
        return jsonify({"error": "Email required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE providers SET status='rejected' WHERE email_id=%s AND status='pending'", (email,))
        conn.commit()
        if cursor.rowcount > 0:
            # Insert notification
            reject_message = "Your provider profile has been rejected. Please contact admin for more details."
            cursor.execute("""
                INSERT INTO admin_messages ( email_id, message, sent_at, is_read, notification_type)
                VALUES ( %s, %s, NOW(), %s, %s)
            """, (email, reject_message, False, 'rejection'))
            conn.commit()

            send_email(email, "Profile Rejected", reject_message)
            return jsonify({"message": "Provider rejected"}), 200
        else:
            return jsonify({"error": "Provider not found or not pending"}), 404
    except psycopg2.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

# ---------------------- SEND MESSAGE ----------------------
@app.route('/api/admin/send_message', methods=['POST'])
def send_message():
    data = request.get_json()
    email = data.get('email')
    message = data.get('message')
    if not email or not message:
        return jsonify({"error": "Email and message required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if send_email(email, "Message from Ontract Admin", message):
            cursor.execute("""
                INSERT INTO admin_messages (email_id, message, sent_at, is_read, notification_type) 
                VALUES ( %s, %s, NOW(), %s, %s)
            """, ( email, message, False, 'message'))
            conn.commit()
            return jsonify({"message": "Message sent and saved"}), 200
        else:
            return jsonify({"error": "Failed to send email"}), 500
    except psycopg2.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

# ---------------------- GET CONTRACTORS ----------------------
@app.route('/api/admin/contractors', methods=['GET'])
def get_contractors():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cursor.execute("""
            SELECT company_id, company_name, head_email, contact_number, status
            FROM company_details
            ORDER BY created_at DESC
        """)
        contractors = [dict(row) for row in cursor.fetchall()]

        company_ids = [c['company_id'] for c in contractors]
        services_map = {}

        if company_ids:
            cursor.execute("""
                SELECT company_id, service_name, service_rate, service_location
                FROM company_services
                WHERE company_id = ANY(%s)
            """, (company_ids,))

            for row in cursor.fetchall():
                cid = row['company_id']
                services_map.setdefault(cid, []).append({
                    "service_name": row['service_name'],
                    "service_location": row['service_location'],
                    "service_rate": float(row['service_rate'])
                })

        for c in contractors:
            cid = c['company_id']
            c['services'] = services_map.get(cid, [])

        return jsonify(contractors), 200

    except psycopg2.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()


# ---------------------- APPROVE CONTRACTOR ----------------------
@app.route('/api/admin/approve_contractor', methods=['POST'])
def approve_contractor():
    data = request.get_json()
    email = data.get('email')
    if not email:
        return jsonify({"error": "Email required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        # Update status to approved
        cursor.execute("""
            UPDATE company_details 
            SET status='approved' 
            WHERE head_email=%s AND status='pending'
        """, (email,))
        conn.commit()

        if cursor.rowcount > 0:
            # Fetch company details
            cursor.execute("""
                SELECT company_id, company_name, head_email, contact_number, status,brn_number,head_name
                FROM company_details
                WHERE head_email=%s
            """, (email,))
            company = cursor.fetchone()
            company_id = company['company_id']

            # Fetch related services
            cursor.execute("""
                SELECT service_name, service_rate, service_location
                FROM company_services
                WHERE company_id=%s
            """, (company_id,))
            services = cursor.fetchall()

            # Prepare details for PDF
            details = {
                "Company ID": company['brn_number'],
                "Company Name": company['company_name'],
                "Name":company['head_name'],
                "Email": company['head_email'],
                "Contact Number": company['contact_number'],
                "Services": [
                    {
                        "Service Name": s['service_name'],
                        "Service Rate": s['service_rate'],
                        "Service Location": s['service_location']
                    } for s in services
                ]
            }

            # Generate PDF
            pdf_path = generate_pdf(details, email)

            # Insert admin message (notification)
            approval_message = (
                "Your company has been approved. You can now proceed to submit bank details."
            )
            cursor.execute("""
                INSERT INTO admin_messages (email_id, message, sent_at, is_read, notification_type)
                VALUES ( %s, %s, NOW(), %s, %s)
            """, ( email, approval_message, False, 'approval'))
            conn.commit()

            # Send email with PDF
            email_body = approval_message
            if send_email(email, "Company Approved", email_body, pdf_path):
                os.remove(pdf_path)
                return jsonify({"message": "Contractor approved"}), 200
            else:
                os.remove(pdf_path)
                return jsonify({"error": "Company approved but failed to send email and certificate"}), 500
        else:
            return jsonify({"error": "Company not found or not pending"}), 404

    except psycopg2.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()



# ---------------------- REJECT CONTRACTOR ----------------------
@app.route('/api/admin/reject_contractor', methods=['POST'])
def reject_contractor():
    data = request.get_json()
    email = data.get('email')
    if not email:
        return jsonify({"error": "Email required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE company_details SET status='rejected' WHERE head_email=%s AND status='pending'", (email,))
        conn.commit()
        if cursor.rowcount > 0:
            cursor.execute("""
                INSERT INTO admin_messages (email_id, message, sent_at, is_read, notification_type)
                VALUES (%s, %s, %s, NOW(), %s, %s)
            """, (email, "Your bank details have been submitted successfully. Await admin approval if required.", False, 'bank_submitted'))
            send_email(email, "Company Rejected",
                       "Your company registration has been rejected. Contact admin for details.")
            return jsonify({"message": "Contractor rejected"}), 200
        else:
            return jsonify({"error": "Not found or already processed"}), 404
    except psycopg2.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()


# ---------------------- SEND MESSAGE TO CONTRACTOR ----------------------
@app.route('/api/admin/send_message_contractor', methods=['POST'])
def send_message_contractor():
    data = request.get_json()
    email = data.get('email')
    message = data.get('message')
    if not email or not message:
        return jsonify({"error": "Email and message required"}), 400


    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if send_email(email, "Message from Admin", message):
            cursor.execute("""
                INSERT INTO admin_messages ( email_id, message, sent_at, is_read, notification_type)
                VALUES ( %s, %s, NOW(), %s, %s)
            """, (email, message, False, 'message'))
            conn.commit()
            return jsonify({"message": "Message sent"}), 200
        else:
            return jsonify({"error": "Failed to send email"}), 500
    except psycopg2.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()


#-----------------------STANDARD RATE----------------------

@app.route('/api/admin/upload_excel', methods=['POST'])
def upload_excel():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    if not file.filename.endswith(('.xlsx', '.xls')):
        return jsonify({"error": "Only Excel files are allowed"}), 400

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    df = pd.read_excel(filepath)

    required_columns = {'service_name', 'service_location', 'service_rate','client'}
    if not required_columns.issubset(df.columns):
        return jsonify({"error": "Missing required columns"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        for _, row in df.iterrows():
            cursor.execute("""
                INSERT INTO standard_rates (service_name, service_location, service_rate,client)
                VALUES (%s, %s, %s,%s)
                ON CONFLICT (service_name, service_location)
                DO UPDATE SET service_rate = EXCLUDED.service_rate
            """, (row['service_name'], row['service_location'], row['service_rate'],row['client']))
        conn.commit()
        return jsonify({"message": "File uploaded and data saved"}), 200
    except psycopg2.Error as err:
        conn.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/admin/standard_rates', methods=['GET'])
def get_standard_rates():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM standard_rates ORDER BY service_name, service_location")
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(data)


@app.route('/api/admin/standard_rates', methods=['POST'])
def add_standard_rate():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO standard_rates (service_name, service_location, service_rate,client)
            VALUES (%s, %s, %s,%s)
            ON CONFLICT (service_name, service_location)
            DO UPDATE SET service_rate = EXCLUDED.service_rate
            RETURNING id
        """, (data['service_name'], data['service_location'], data['service_rate'],data['client']))
        conn.commit()
        return jsonify({"message": "Rate added"}), 201
    except psycopg2.Error as err:
        conn.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/admin/standard_rates/<int:id>', methods=['PUT'])
def update_standard_rate(id):
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE standard_rates
            SET service_name = %s, service_location = %s, service_rate = %s, client=%s
            WHERE id = %s
        """, (data['service_name'], data['service_location'], data['service_rate'],data['client'], id))
        conn.commit()
        return jsonify({"message": "Rate updated"}), 200
    except psycopg2.Error as err:
        conn.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/admin/standard_rates/<int:id>', methods=['DELETE'])
def delete_standard_rate(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM standard_rates WHERE id = %s", (id,))
        conn.commit()
        return jsonify({"message": "Rate deleted"}), 200
    except psycopg2.Error as err:
        conn.rollback()
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/admin/rates', methods=['GET'])
def get_admin_rates():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cursor.execute("""
            SELECT id, service_name, service_location, service_rate,client
            FROM standard_rates
            ORDER BY service_name, service_location
        """)
        rows = cursor.fetchall()
        rates = [dict(row) for row in rows]
        return jsonify(rates), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    app.run(debug=True, port=5001)