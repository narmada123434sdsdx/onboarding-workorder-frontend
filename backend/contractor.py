# contractor.py
from flask import Flask, Blueprint, request, jsonify, send_file
from flask_cors import CORS, cross_origin
import psycopg2
import psycopg2.extras
import bcrypt
import uuid
import smtplib
import random
import os
import re
import string
import json
from werkzeug.utils import secure_filename
from cryptography.fernet import Fernet
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from fpdf import FPDF  # pip install fpdf2
from dotenv import load_dotenv   # ✅ New import

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

# ---------------------- Flask App Setup ----------------------
app = Flask(__name__)
CORS(app,
     origins=[os.getenv('ALLOWED_ORIGINS', 'http://localhost:5173')],
     methods=["GET", "POST", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"],
     supports_credentials=True)

# ---------------------- Uploads ----------------------
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ---------------------- Encryption ----------------------
ENCRYPTION_KEY = b'cvI_hj-yDtPL1Z2lFlRBTBzTE72Hw1U0DTKw2U5uh3s='
cipher = Fernet(ENCRYPTION_KEY)


# ---------------------- Blueprint ----------------------
contractor_bp = Blueprint('contractor_bp', __name__)

# ---------------------- Database Connection ----------------------
def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

# ---------------------- Email Sender ----------------------
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

# ---------------------- Activation Email ----------------------
def send_activation_email(email, token):
    """Send activation link email."""
    link = f"http://localhost:5173/contractor/activate?token={token}"
    subject = "Activate Your Company Account"
    body = f"""
    Please click the link below to activate your account:
    {link}
    """
    send_email(email, subject, body)


#--------------send otp---------------
def send_otp_email(email, otp):
    subject = "Your Ontract OTP Code"
    body = f"""
    Dear Company User,

    Your One-Time Password (OTP) for logging in to your Ontract account is {otp}.

    Please enter this code to complete your login process.
    This OTP is valid for 5 minutes. For your security, do not share this code with anyone.

    Thank you,
    Ontract
    """
    return send_email(email, subject, body.strip())


# ---------------------- Company Signup ----------------------
@contractor_bp.route('/api/contractor/contractor_signup', methods=['POST'])
def contractor_signup():
    try:
        data = request.get_json()
        print("hello")
        brn_number = data.get('business_registration_number')
        companyName=data.get('company_name')
        email = data.get('email_id')
        phone = data.get('phone_number')
        password = data.get('password')

        if not all([brn_number, email, phone, password]):
            return jsonify({"error": "All fields are required"}), 400

        # Hash password
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        activation_token = str(uuid.uuid4())


        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO company_details (
                 company_name, BRN_Number,password_hash,mailing_address,billing_address,contact_number, 
                head_name, head_email, tin_number, active_status, status, activation_token, created_at
            ) VALUES (
                 %s, %s, %s, %s,%s,%s,
                %s, %s, %s, %s, %s, %s,%s
            )
        """, (
             companyName, brn_number,hashed_password, '-','-', phone,
            '-', email, '-', False, 'registered', activation_token, datetime.now()
        ))

        conn.commit()
        send_activation_email(email, activation_token)

        return jsonify({
            "message": "Signup successful. Activation link sent to your email."
        }), 200

    except psycopg2.Error as err:
        print("DB Error:", err)
        return jsonify({"error": str(err)}), 500
    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# ---------------------- Company Activation ----------------------
@contractor_bp.route('/api/contractor/contractor_activate', methods=['POST'])
def contractor_activate():
    data = request.get_json()
    token = data.get('token')

    if not token:
        return jsonify({"error": "Token is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        cursor.execute("SELECT head_email FROM company_details WHERE activation_token = %s", (token,))
        company = cursor.fetchone()

        if not company:
            return jsonify({"error": "Invalid activation token"}), 400

        cursor.execute("""
            UPDATE company_details
            SET active_status = TRUE, status = 'pending'
            WHERE activation_token = %s
        """, (token,))
        conn.commit()

        return jsonify({
            "message": "Company account activated successfully.",
            "email_id": company['head_email']
        }), 200

    except psycopg2.Error as err:
        print("DB Error:", err)
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

# -------------------------------------------------------------
# ✅ Contractor Login Route
# -------------------------------------------------------------
@contractor_bp.route('/api/contractor/login', methods=['POST'])
def contractor_login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cursor.execute("SELECT password_hash, active_status FROM company_details WHERE head_email = %s", (email,))
        contractor = cursor.fetchone()

        if contractor and bcrypt.checkpw(password.encode(), contractor['password_hash'].encode()):
            if contractor['active_status']:
                otp = ''.join(random.choices(string.digits, k=6))


                cursor.execute(
                    "INSERT INTO otp_codes (email_id, otp_code) VALUES ( %s, %s)",
                    ( email, otp)
                )
                conn.commit()

                send_otp_email(email, otp)
                return jsonify({"message": "OTP sent to contractor email"}), 200
            else:
                return jsonify({"error": "Account not activated"}), 401
        else:
            return jsonify({"error": "Invalid credentials"}), 401
    finally:
        cursor.close()
        conn.close()


# ------------------ CONTRACTOR VERIFY OTP ------------------

@contractor_bp.route('/api/contractor/verify_otp', methods=['POST'])
def contractor_verify_otp():
    data = request.get_json()
    email = data.get('email')
    otp = data.get('otp')

    if not email or not otp:
        return jsonify({"error": "Email and OTP required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cursor.execute("""
            SELECT otp_code FROM otp_codes 
            WHERE email_id = %s AND created_at > (NOW() - INTERVAL '5 minutes')
        """, (email,))
        record = cursor.fetchone()

        if record and record['otp_code'] == otp:
            cursor.execute("DELETE FROM otp_codes WHERE email_id = %s", (email,))
            conn.commit()
             # ✅ Fetch contractor basic info for frontend
            cursor.execute("SELECT company_id, head_email, contact_number FROM company_details WHERE head_email = %s", (email,))
            contractor = cursor.fetchone()
            return jsonify({"message": "OTP verified successfully", "contractor": contractor}), 200
        else:
            return jsonify({"error": "Invalid or expired OTP"}), 401
    finally:
        cursor.close()
        conn.close()


# ------------------ CONTRACTOR RESEND OTP ------------------

@contractor_bp.route('/api/contractor/resend_otp', methods=['POST'])
def contractor_resend_otp():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({"error": "Email required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        # Clear old OTPs
        cursor.execute("DELETE FROM otp_codes WHERE email_id = %s", (email,))

        otp = ''.join(random.choices(string.digits, k=6))


        cursor.execute(
            "INSERT INTO otp_codes (email_id, otp_code) VALUES ( %s, %s)",
            ( email, otp)
        )
        conn.commit()

        send_otp_email(email, otp)
        return jsonify({"message": "OTP resent to contractor email"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ---------------------- Existing Endpoints (Signup, Activate, Login, OTP) ----------------------
# ... (Keep all existing @contractor_bp routes: signup, activate, login, verify_otp, resend_otp)

# ---------------------- Fetch Company Profile ----------------------
@contractor_bp.route('/api/contractor/company_profile', methods=['POST'])
def company_profile():
    try:
        data = request.get_json()
        email = data.get('email')

        if not email:
            return jsonify({"error": "Email required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cursor.execute("""
            SELECT company_id, company_name, brn_number, billing_address, mailing_address, contact_number,tin_number,
                   alternate_contact_number, head_name, head_email, status
            FROM company_details
            WHERE head_email = %s
        """, (email,))
        company = cursor.fetchone()
        company_id=company['company_id']

        if not company:
            return jsonify({"error": "Company not found"}), 404

        cursor.execute("""
            SELECT service_name, service_rate, service_location
            FROM company_services
            WHERE company_id = %s
        """, (company['company_id'],))
        services = cursor.fetchall()

        company['services'] = services if services else []

        cursor.execute("SELECT * FROM company_bank_details WHERE company_id = %s", (company_id,))
        bank = cursor.fetchone()
        if bank:
            company['bank_details'] = dict(bank)

        # --- Fix memoryview issue ---
        def convert_memoryview(obj):
            if isinstance(obj, memoryview):
                return obj.tobytes().decode('utf-8', errors='ignore')
            elif isinstance(obj, dict):
                return {k: convert_memoryview(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_memoryview(i) for i in obj]
            return obj

        company = convert_memoryview(company)
        return jsonify(company), 200

    except Exception as e:
        print("Error in /api/company_profile:", str(e))
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


# --- update company profile (expects services as array-of-objects) ---
@contractor_bp.route('/api/contractor/update_company_profile', methods=['POST'])
def update_company_profile():
    conn = None
    cursor = None
    try:
        data = request.form
        email = data.get('email')
        if not email:
            return jsonify({"error": "Email required"}), 400

        company_name = data.get('company_name')
        brn_number = data.get('brn_number')
        tin_number = data.get('tin_number')
        mailing_address = data.get('mailing_address')
        billing_address = data.get('billing_address')
        contact_number = data.get('contact_number')
        alternate_contact = data.get('alternate_contact')
        contact_person = data.get('contact_person')

        # Services as JSON array of objects: {service_name, service_location, service_rate}
        services_json = data.get('services', '[]')
        try:
            services = json.loads(services_json)
            if not isinstance(services, list):
                services = []
        except Exception:
            services = []

        # Files
        logo_bytes = None
        cert_bytes = None
        if 'company_logo' in request.files:
            f = request.files['company_logo']
            if f and f.filename:
                logo_bytes = f.read()
        if 'certificate' in request.files:
            f = request.files['certificate']
            if f and f.filename:
                cert_bytes = f.read()

        conn = get_db_connection()
        cursor = conn.cursor()

        # Update logo/certificate binary if provided
        if logo_bytes or cert_bytes:
            cursor.execute("""
                UPDATE company_details
                SET logo_path = COALESCE(%s, logo_path),
                    certificate_path = COALESCE(%s, certificate_path)
                WHERE head_email = %s
            """, (psycopg2.Binary(logo_bytes) if logo_bytes else None,
                  psycopg2.Binary(cert_bytes) if cert_bytes else None,
                  email))

        # Ensure company exists and get company_id
        cursor.execute("SELECT company_id FROM company_details WHERE head_email = %s", (email,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "Company not found"}), 404
        company_id = row[0]

        # Update details (set status pending for admin review)
        cursor.execute("""
            UPDATE company_details
            SET company_name = %s,
                brn_number = %s,
                tin_number = %s,
                mailing_address = %s,
                billing_address = %s,
                contact_number = %s,
                alternate_contact_number = %s,
                head_name = %s,
                status = 'pending',
                updated_at = %s
            WHERE head_email = %s
        """, (company_name, brn_number, tin_number, mailing_address,billing_address, contact_number,
              alternate_contact, contact_person, datetime.now(), email))

        # Refresh company_services rows: delete previous and insert new
        cursor.execute("DELETE FROM company_services WHERE company_id = %s", (company_id,))
        for svc in services:
            svc_name = svc.get('service_name')
            svc_rate = svc.get('service_rate', 0)
            svc_loc = svc.get('service_location')
            svc_region=svc.get('service_region')
            cursor.execute("""
                INSERT INTO company_services ( company_id, service_name, service_rate, service_location,service_region)
                VALUES ( %s, %s, %s, %s,%s)
            """, ( company_id, svc_name, svc_rate, svc_loc,svc_region))

        conn.commit()

        # Optionally notify admin (use send_email function you already have)
        send_email(ADMIN_EMAIL, "Company profile submitted", f"Company {company_name} ({email}) updated profile and is pending approval.")

        return jsonify({"message": "Company profile updated", "status": "pending"}), 200

    except psycopg2.Error as err:
        print("DB Error:", err)
        if conn:
            conn.rollback()
        return jsonify({"error": str(err)}), 500
    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# --- update company bank (no CVV) ---
@contractor_bp.route('/api/contractor/update_company_bank', methods=['POST'])
def update_company_bank():
    """
    Accepts multipart/form-data:
      - email
      - swift
      - bank_name
      - holder_name
      - account_number
      - bank_statement (file)
    Stores account_number encrypted and bank_statement as bytea in company_bank_details.
    """
    conn = None
    cursor = None
    try:
        email = request.form.get('email')
        swift = (request.form.get('swift') or '').upper()
        bankname = request.form.get('bank_name')
        holder_name = request.form.get('holder_name')
        account_number = request.form.get('account_number')
        bank_statement_file = request.files.get('bank_statement')

        if not all([swift, bankname, holder_name, account_number, bank_statement_file]):
            return jsonify({"error": "All bank fields and statement file are required"}), 400

        # basic validations (server-side)
        swift_regex = re.compile(r'^[A-Z]{4}MY[A-Z0-9]{2}([A-Z0-9]{3})?$')
        acct_regex = re.compile(r'^[0-9]{6,20}$')
        if not swift_regex.match(swift):
            return jsonify({"error": "Invalid SWIFT code"}), 400
        if not acct_regex.match(account_number):
            return jsonify({"error": "Invalid account number (6-20 digits)"}), 400

        # read statement bytes
        statement_bytes = bank_statement_file.read()
        # optional: check mimetype via python-magic if installed
        # store encrypted account (use cipher from module)
        encrypted_acc = cipher.encrypt(account_number.encode()).decode()
        swift_enc = cipher.encrypt(swift.encode()).decode()

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cursor.execute("SELECT company_id FROM company_details WHERE head_email=%s", (email,))
        company = cursor.fetchone()

        # Upsert into company_bank_details table (email_id primary key)
        cursor.execute("""
            INSERT INTO company_bank_details (company_id, swift_code, holder_name, account_number,bank_name, created_at)
            VALUES (%s, %s, %s, %s,%s, NOW())
            ON CONFLICT (company_id) DO UPDATE SET
              swift_code = EXCLUDED.swift_code,
              holder_name = EXCLUDED.holder_name,
              account_number = EXCLUDED.account_number,
              updated_at = NOW()
        """, (company['company_id'], swift, holder_name, encrypted_acc,bankname))

        # store bank_statement separately in table company_bank_statements or attach into company_bank_details
        # if company_bank_details has a column for statement (bytea), update it.
        # You provided company_bank_details earlier without bank_statement; if you want to store file:
        try:
            # Try update bank_statement column if exists:
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='company_bank_details' AND column_name='bank_statement'")
            if cursor.fetchone():
                cursor.execute("""
                    UPDATE company_bank_details SET bank_statement = %s WHERE company_id = %s
                """, (psycopg2.Binary(statement_bytes), company['company_id']))
            else:
                # If not present, save file to uploads folder (contractor uploads)
                safe_email = email.replace('@', '_').replace('.', '_')
                uploads_dir = os.path.join(UPLOAD_FOLDER, 'contractors_bank_statements')
                os.makedirs(uploads_dir, exist_ok=True)
                file_path = os.path.join(uploads_dir, f"{safe_email}_bank_statement")
                with open(file_path, 'wb') as fh:
                    fh.write(statement_bytes)
                # Optionally save path in a separate column if you have it. Skip otherwise.
        except Exception as ex:
            print("Error storing statement:", ex)

        conn.commit()

        # Optionally send confirmation email to company
        send_email(email, "Bank details submitted", "Your bank details have been received and are stored securely.")

        return jsonify({"message": "Bank details updated successfully"}), 200

    except psycopg2.Error as err:
        print("DB Error:", err)
        if conn:
            conn.rollback()
        return jsonify({"error": str(err)}), 500
    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# ---------------------- Admin Endpoints (Parallel to admin.py) ----------------------
@contractor_bp.route('/api/contractor_admin/companies', methods=['GET'])
def get_companies():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cursor.execute("""
            SELECT company_id, company_name, email_id, contact_number, status
            FROM company_details ORDER BY created_at DESC
        """)
        companies = [dict(row) for row in cursor.fetchall()]

        company_ids = [c['company_id'] for c in companies]
        services_map = {}
        if company_ids:
            cursor.execute("""
                SELECT company_id, service_name, service_rate, service_location
                FROM company_services WHERE company_id = ANY(%s)
            """, (company_ids,))
            rows = cursor.fetchall()
            for row in rows:
                cid = row['company_id']
                services_map.setdefault(cid, {}).setdefault(row['service_name'], {})[row['service_location']] = float(row['service_rate'])

        for company in companies:
            cid = company['company_id']
            company['services'] = services_map.get(cid, {})
            all_locs = [loc for svc in company['services'].values() for loc in svc.keys()]
            company['service_locations'] = ", ".join(sorted(set(all_locs))) if all_locs else "N/A"

        return jsonify(companies), 200
    except psycopg2.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

# ---------------------- NOTIFICATION ENDPOINTS ----------------------
@contractor_bp.route('/api/contractor/contractor_notifications', methods=['GET'])
def get_contractor_notifications():
    email = request.args.get('email')
    if not email:
        return jsonify({"error": "Email required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cursor.execute("""
            SELECT message_id, message, sent_at, is_read, notification_type
            FROM admin_messages 
            WHERE email_id = %s 
            ORDER BY sent_at DESC
        """, (email,))
        notifications = [dict(row) for row in cursor.fetchall()]
        return jsonify(notifications), 200
    except psycopg2.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@contractor_bp.route('/api/contractor/contractor_unread_count', methods=['GET'])
def contractor_unread_count():
    email = request.args.get('email')
    if not email:
        return jsonify({"error": "Email required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT COUNT(*) FROM admin_messages 
            WHERE email_id = %s AND is_read = FALSE
        """, (email,))
        count = cursor.fetchone()[0]
        return jsonify({"count": int(count)}), 200
    except psycopg2.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

@contractor_bp.route('/api/contractor/contractor_mark_read', methods=['POST'])
def contractor_mark_read():
    data = request.get_json()
    message_id = data.get('message_id')
    if not message_id:
        return jsonify({"error": "Message ID required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE admin_messages 
            SET is_read = TRUE 
            WHERE message_id = %s
        """, (message_id,))
        conn.commit()
        if cursor.rowcount > 0:
            return jsonify({"success": True}), 200
        else:
            return jsonify({"error": "Notification not found"}), 404
    except psycopg2.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()

# ---------------------- Register Blueprint ----------------------
app.register_blueprint(contractor_bp)