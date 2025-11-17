from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import psycopg2
import psycopg2.extras
import bcrypt
import random
import string
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from fpdf import FPDF
from cryptography.fernet import Fernet
import uuid
import os
from PIL import Image
import io
import base64
import json
import magic
from datetime import datetime, timedelta
from dotenv import load_dotenv   # ✅ new
import os                        # ✅ new

# ---------------------- Load .env ----------------------
load_dotenv()

# ---------------------- Configuration ----------------------
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

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": os.getenv('ALLOWED_ORIGINS', 'http://localhost:5173')}})

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ENCRYPTION_KEY = b'cvI_hj-yDtPL1Z2lFlRBTBzTE72Hw1U0DTKw2U5uh3s='
cipher = Fernet(ENCRYPTION_KEY)

ADMIN_EMAIL = EMAIL_CONFIG['sender_email']

# ---------- Database Connection ----------
def get_db_connection():
    return psycopg2.connect(
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=DB_CONFIG['database']
    )


#--------------------------------Mail's--------------------------------------

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

def send_activation_email(email, token):
    link = f"http://localhost:5173/activate?token={token}"
    subject = "Activate Your Provider Account"
    body = f"""
    Dear Provider,

    Please activate your Ontract account by clicking this link:
    {link}
    
    Thank you for choosing Ontract.

    Regards,
    Ontract Team
    """
    return send_email(email, subject, body.strip())

def send_otp_email(email, otp):
    subject = "Your Ontract OTP Code"
    body = f"""
    Dear User,

    Your One-Time Password (OTP) for logging in to your Ontract account is {otp}.

    Please enter this code to complete your login process.
    This OTP is valid for 5 minutes. For your security, do not share this code with anyone.

    Thank you,
    Ontract
    """
    return send_email(email, subject, body.strip())

def send_reset_otp_email(email, otp):
    subject = "Your Ontract Password Reset OTP"
    body = f"""
    Dear User,

    Your One-Time Password (OTP) for resetting your Ontract account password is {otp}.

    Please enter this code to proceed with password reset.
    This OTP is valid for 5 minutes. For your security, do not share this code with anyone.

    Thank you,
    Ontract
    """
    return send_email(email, subject, body.strip())

# ---------------------- AUTH ROUTES ----------------------

@app.route('/api/profile', methods=['POST'])
def get_profile():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({"error": "Email is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        # 1. Fetch provider details
        cursor.execute("""
            SELECT provider_id, full_name, id_type, id_number, mailing_address, billing_address,
                   contact_number, alternate_contact_number, tin_number,
                   profile_pic, authorized_certificate, status
            FROM providers
            WHERE email_id = %s
        """, (email,))
        provider = cursor.fetchone()

        if not provider:
            return jsonify({"error": "Provider not found"}), 404

        provider_id = provider['provider_id']

        # 2. Fetch all services with region/state/city and rate
        cursor.execute("""
            SELECT service_name, service_rate, region, state, city
            FROM provider_services
            WHERE provider_id = %s
            ORDER BY created_at
        """, (provider_id,))
        services_rows = cursor.fetchall()

        # Build list of services (array of objects)
        services_list = []
        for s in services_rows:
            services_list.append({
                "service_name": s['service_name'],
                "service_rate": float(s['service_rate']) if s['service_rate'] else 0.0,
                "region": s.get('region') or '',
                "state": s.get('state') or '',
                "city": s.get('city') or ''
            })

        # 3. Fetch bank details
        cursor.execute("""
            SELECT bank_name, swift_code, bank_account_number, account_holder_name, bank_statement
            FROM providers_bank_details
            WHERE provider_id = %s
            LIMIT 1
        """, (provider_id,))
        bank_row = cursor.fetchone()

        bank_details = None
        if bank_row:
            def try_decrypt(val):
                if not val:
                    return val
                try:
                    decrypted = cipher.decrypt(val.encode()).decode()
                    return decrypted
                except Exception:
                    return val

            bank_statement_b64 = (
                base64.b64encode(bank_row['bank_statement']).decode('utf-8')
                if bank_row.get('bank_statement') else None
            )

            bank_details = {
                "bank_name": bank_row.get('bank_name'),
                "swift": try_decrypt(bank_row.get('swift_code')),
                "bank_account_number": try_decrypt(bank_row.get('bank_account_number')),
                "holder_name": try_decrypt(bank_row.get('account_holder_name')),
                "bank_statement": bank_statement_b64
            }

        # 4. Convert images to base64
        profile_pic_b64 = (
            base64.b64encode(provider['profile_pic']).decode('utf-8')
            if provider.get('profile_pic') else None
        )
        cert_b64 = (
            base64.b64encode(provider['authorized_certificate']).decode('utf-8')
            if provider.get('authorized_certificate') else None
        )

        # 5. Final JSON response
        response = {
            "provider_id": provider_id,
            "full_name": provider.get('full_name'),
            "id_type": provider.get('id_type'),
            "id_number": provider.get('id_number'),
            "mailing_address": provider.get('mailing_address'),
            "billing_address": provider.get('billing_address'),
            "contact_number": provider.get('contact_number'),
            "alternate_contact_number": provider.get('alternate_contact_number'),
            "tin_number": provider.get('tin_number'),
            "phone_number": provider.get('contact_number'),  # Legacy alias
            "status": provider.get('status'),
            "profile_pic": profile_pic_b64,
            "authorized_certificate": cert_b64,
            "services": services_list,          # ARRAY OF OBJECTS
            "bank_details": bank_details
        }

        return jsonify(response), 200

    except psycopg2.Error as err:
        print("PostgreSQL Error:", err)
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data['email']
    password = data['password']
    phone_number = data.get('phone_number')
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    activation_token = str(uuid.uuid4())

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO providers (email_id, password_hash, contact_number, active_status, status, activation_token)
            VALUES ( %s, %s, %s, %s, %s, %s)
        """, (email, hashed_password, phone_number, False, 'registered', activation_token))
        conn.commit()

        send_activation_email(email, activation_token)
        return jsonify({"message": "Signup successful. Check email for activation link."}), 200
    except psycopg2.Error as err:
        return jsonify({"error": str(err)}), 400
    finally:
        cursor.close()
        conn.close()


@app.route('/api/activate', methods=['POST'])
def activate_account():
    data = request.get_json()
    token = data.get('token')

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("SELECT email_id FROM providers WHERE activation_token = %s", (token,))
    user = cursor.fetchone()
    try:
        cursor.execute("UPDATE providers SET active_status = %s WHERE activation_token = %s", (True, token))
        conn.commit()
        if cursor.rowcount > 0:
            return jsonify({"message": "Account activated successfully", "email": user["email_id"]}), 200
        else:
            return jsonify({"error": "Invalid token"}), 400
    finally:
        cursor.close()
        conn.close()


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data['email']
    password = data['password']

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cursor.execute("SELECT password_hash, active_status FROM providers WHERE email_id = %s", (email,))
        provider = cursor.fetchone()

        if provider and bcrypt.checkpw(password.encode(), provider['password_hash'].encode()):
            if provider['active_status'] == True:
                otp = ''.join(random.choices(string.digits, k=6))

                cursor.execute(
                    "INSERT INTO otp_codes ( email_id, otp_code) VALUES (%s, %s)",
                    (email, otp)
                )
                conn.commit()
                send_otp_email(email, otp)
                return jsonify({"message": "OTP sent to email"}), 200
            else:
                return jsonify({"error": "Account not activated"}), 401
        else:
            return jsonify({"error": "Invalid credentials"}), 401
    finally:
        cursor.close()
        conn.close()


@app.route('/api/verify_otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    email = data['email']
    otp = data['otp']

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
            return jsonify({"message": "OTP verified", "email": email}), 200
        else:
            return jsonify({"error": "Invalid or expired OTP"}), 401
    finally:
        cursor.close()
        conn.close()


@app.route('/api/resend_otp', methods=['POST'])
def resend_otp():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({"error": "Email is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cursor.execute("DELETE FROM otp_codes WHERE email_id = %s", (email,))
        otp = ''.join(random.choices(string.digits, k=6))
        cursor.execute(
            "INSERT INTO otp_codes ( email_id, otp_code) VALUES (%s, %s)",
            ( email, otp)
        )
        conn.commit()
        send_otp_email(email, otp)
        return jsonify({"message": "OTP resent successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/forgot_send_otp', methods=['POST'])
def forgot_send_otp():
    data = request.get_json()
    email = data.get('email')
    if not email:
        return jsonify({"error": "Email is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cursor.execute("SELECT active_status FROM providers WHERE email_id = %s", (email,))
        provider = cursor.fetchone()

        if not provider or provider['active_status'] != True:
            return jsonify({"error": "Account not found or not activated"}), 404

        otp = ''.join(random.choices(string.digits, k=6))
        cursor.execute(
            "INSERT INTO otp_codes ( email_id, otp_code) VALUES ( %s, %s)",
            (email, otp)
        )
        conn.commit()

        if send_reset_otp_email(email, otp):
            return jsonify({"message": "Reset OTP sent to email"}), 200
        else:
            return jsonify({"error": "Failed to send OTP"}), 500
    except psycopg2.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/verify_reset_otp', methods=['POST'])
def verify_reset_otp():
    data = request.get_json()
    email = data.get('email')
    otp = data.get('otp')
    if not email or not otp:
        return jsonify({"error": "Email and OTP are required"}), 400

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
            reset_token = str(uuid.uuid4())
            expiry = datetime.now() + timedelta(minutes=10)
            cursor.execute("""
                UPDATE providers 
                SET reset_token = %s, reset_expiry = %s 
                WHERE email_id = %s
            """, (reset_token, expiry, email))
            conn.commit()
            return jsonify({"message": "OTP verified successfully", "reset_token": reset_token}), 200
        else:
            return jsonify({"error": "Invalid or expired OTP"}), 401
    except psycopg2.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/reset_password', methods=['POST'])
def reset_password():
    data = request.get_json()
    email = data.get('email')
    reset_token = data.get('reset_token')
    password = data.get('password')
    if not all([email, reset_token, password]):
        return jsonify({"error": "Email, token, and password are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cursor.execute("""
            SELECT reset_token, reset_expiry FROM providers 
            WHERE email_id = %s
        """, (email,))
        provider = cursor.fetchone()

        if not provider:
            return jsonify({"error": "Provider not found"}), 404

        now = datetime.now()
        if (provider['reset_token'] != reset_token or 
            not provider['reset_expiry'] or 
            provider['reset_expiry'] < now):
            return jsonify({"error": "Invalid or expired reset token"}), 400

        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        cursor.execute("""
            UPDATE providers 
            SET password_hash = %s, reset_token = NULL, reset_expiry = NULL 
            WHERE email_id = %s
        """, (hashed_password, email))
        conn.commit()

        return jsonify({"message": "Password reset successfully"}), 200
    except psycopg2.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/update_profile', methods=['POST'])
def update_profile():
    try:
        email = request.form['email']
        full_name = request.form['full_name']
        id_type = request.form.get('id_type', '')
        id_number = request.form.get('id_number', '')
        mailing_address = request.form.get('mailing_address', '')
        billing_address = request.form.get('billing_address', '')
        contact_number = request.form['contact_number']
        alternate_contact_number = request.form.get('alternate_contact_number', '')
        tin_number = request.form.get('tin_number', '')
        services_json = request.form.get('services', '[]')

        profile_pic = request.files['profile_image'].read() if 'profile_image' in request.files else None
        cert_file = request.files['certificate'].read() if 'certificate' in request.files else None

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cursor.execute("SELECT provider_id, profile_pic, authorized_certificate FROM providers WHERE email_id=%s", (email,))
        provider = cursor.fetchone()
        if not provider:
            return jsonify({"error": "Provider not found"}), 404
        provider_id = provider['provider_id']

        update_profile_pic = profile_pic if profile_pic else provider['profile_pic']
        update_cert = cert_file if cert_file else provider['authorized_certificate']

        cursor.close()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE providers
            SET full_name=%s, id_type=%s, id_number=%s, mailing_address=%s, billing_address=%s,
                contact_number=%s, alternate_contact_number=%s, tin_number=%s,
                profile_pic=%s, authorized_certificate=%s, status='pending'
            WHERE email_id=%s
        """, (full_name, id_type, id_number, mailing_address, billing_address, contact_number, alternate_contact_number, tin_number, update_profile_pic, update_cert, email))
        conn.commit()

        cursor.execute("DELETE FROM provider_services WHERE provider_id=%s", (provider_id,))
        conn.commit()

        bulk_data = []
        try:
            services_parsed = json.loads(services_json)
        except Exception:
            services_parsed = []

        if isinstance(services_parsed, list):
            for item in services_parsed:
                region = item.get('region') or ''
                state = item.get('state') or ''
                city = item.get('city') or ''
                service_name = item.get('service') or item.get('service_name') or ''
                price = item.get('price') or item.get('service_rate') or 0
                try:
                    price_val = float(price)
                except Exception:
                    price_val = 0.0
                bulk_data.append((provider_id, service_name, price_val, region, state, city))
        elif isinstance(services_parsed, dict):
            for service_name, locs in services_parsed.items():
                for location_key, price in locs.items():
                    region = ''
                    state = ''
                    city = location_key
                    try:
                        price_val = float(price)
                    except Exception:
                        price_val = 0.0
                    bulk_data.append((provider_id, service_name, price_val, region, state, city))

        if bulk_data:
            cursor.executemany("""
                INSERT INTO provider_services (provider_id, service_name, service_rate, region, state, city)
                VALUES ( %s, %s, %s, %s, %s, %s)
            """, bulk_data)
            conn.commit()

        send_email(ADMIN_EMAIL, "New Provider for Approval", f"A new provider has submitted their profile.\n\nProvider Email: {email}\nPlease review and approve their details.")
        send_email(email, "Profile Submitted", "Your profile has been submitted and is pending admin approval.")

        return jsonify({"message": "Profile submitted for approval", "status": "pending"}), 200

    except psycopg2.Error as err:
        print("Postgres error:", err)
        return jsonify({"error": str(err)}), 500
    except Exception as err:
        print("General error:", err)
        return jsonify({"error": str(err)}), 500
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass

@app.route('/api/update_bank', methods=['POST'])
def update_bank():
    try:
        email = request.form['email']
        bank_name = request.form['bank_name']
        holder_name = request.form['holder_name']
        account_number = request.form['account_number']
        swift = request.form['swift'].upper()
        bank_statement_file = request.files['bank_statement'].read() if 'bank_statement' in request.files else None

        if not all([email, bank_name, holder_name, account_number, swift, bank_statement_file]):
            return jsonify({"error": "All bank details and statement are required"}), 400

        mime = magic.Magic(mime=True)
        mimetype = mime.from_buffer(bank_statement_file[:2048])
        if not mimetype.startswith('application/pdf') and not mimetype.startswith('image/'):
            return jsonify({"error": "Bank statement must be a PDF or image file"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            cursor.execute("SELECT provider_id FROM providers WHERE email_id=%s", (email,))
            provider = cursor.fetchone()
            if not provider:
                return jsonify({"error": "Provider not found"}), 404

            provider_id = provider['provider_id']

            def encrypt_field(val):
                if val:
                    return cipher.encrypt(val.encode()).decode()
                return val

            swift_enc = encrypt_field(swift)
            acc_enc = encrypt_field(account_number)
            holder_enc = encrypt_field(holder_name)

            cursor.execute("SELECT * FROM providers_bank_details WHERE provider_id=%s", (provider_id,))
            existing = cursor.fetchone()

            if existing:
                cursor.execute("""
                    UPDATE providers_bank_details 
                    SET bank_name=%s, swift_code=%s, bank_account_number=%s, account_holder_name=%s, bank_statement=%s
                    WHERE provider_id=%s
                """, (bank_name, swift_enc, acc_enc, holder_name, bank_statement_file, provider_id))
            else:
                cursor.execute("""
                    INSERT INTO providers_bank_details (provider_id, bank_name, swift_code, bank_account_number, account_holder_name, bank_statement)
                    VALUES ( %s, %s, %s, %s, %s, %s)
                """, ( provider_id, bank_name, swift_enc, acc_enc, holder_name, bank_statement_file))
            conn.commit()

            # Add notification for bank submission
            cursor.execute("""
                INSERT INTO admin_messages (email_id, message, sent_at, is_read, notification_type)
                VALUES ( %s, %s, NOW(), %s, %s)
            """, ( email, "Your bank details have been submitted successfully. Await admin approval if required.", False, 'bank_submitted'))

            conn.commit()

            send_email(email, "Bank Details Updated", "Your bank details were successfully added/updated.")
            return jsonify({"message": "Bank details updated"}), 200
        except psycopg2.Error as err:
            return jsonify({"error": str(err)}), 500
        finally:
            cursor.close()
            conn.close()
    except Exception as err:
        return jsonify({"error": str(err)}), 500

@app.route('/api/get_image/<email>/<file_type>', methods=['GET'])
def get_image(email, file_type):
    # Provider images from DB
    conn = get_db_connection()
    cursor = conn.cursor()
    if file_type == "profile":
        column = "profile_pic"
        table = "providers"
        cursor.execute(f"SELECT {column} FROM {table} WHERE email_id = %s", (email,))
    elif file_type == "certificate":
        column = "authorized_certificate"
        table = "providers"
        cursor.execute(f"SELECT {column} FROM {table} WHERE email_id = %s", (email,))
    elif file_type == "bank_statement":
        column = "bank_statement"
        table = "providers_bank_details"
        cursor.execute(f"SELECT {column} FROM {table} WHERE provider_id IN (SELECT provider_id FROM providers WHERE email_id = %s)", (email,))
    elif file_type == "contractor_certificate":
        column = "certificate_path"
        table = "company_details"
        cursor.execute(f"SELECT {column} FROM {table} WHERE  head_email = %s", (email,))
    elif file_type == "contractor_logo":
        column = "logo_path"
        table = "company_details"
        cursor.execute(f"SELECT {column} FROM {table} WHERE  head_email = %s", (email,))
    else:
        return jsonify({"error": "Invalid file type"}), 400

    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row or not row[0]:
        return jsonify({"error": "File not found"}), 404

    file_data = row[0]
    if isinstance(file_data, memoryview):
        file_data = file_data.tobytes()

    mime = magic.Magic(mime=True)
    mimetype = mime.from_buffer(file_data[:2048])

    if mimetype == "application/pdf":
        return send_file(io.BytesIO(file_data), mimetype=mimetype, as_attachment=False)

    try:
        img = Image.open(io.BytesIO(file_data))
        mimetype = f"image/{img.format.lower()}"
    except Exception:
        return jsonify({"error": "Invalid or corrupted file format"}), 400

    return send_file(io.BytesIO(file_data), mimetype=mimetype, as_attachment=False)

# ===============================================================
# MALAYSIA LOCATION API
# ===============================================================
_FLAT_CACHE = {}
_CITY_CACHE = {}
_POSTCODE_CACHE = {}

def _load_flat_malaysia_data():
    url = "https://raw.githubusercontent.com/AsyrafHussin/malaysia-postcodes/main/all.json"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        flat = {}
        for state in data.get('state', []):
            flat[state['name']] = [c['name'] for c in state.get('city', [])]
        return flat
    except Exception as e:
        print("Flat location load error:", e)
        return {}

def _load_postcode_malaysia_data():
    global _POSTCODE_CACHE
    if _POSTCODE_CACHE:
        return _POSTCODE_CACHE
    try:
        url = "https://raw.githubusercontent.com/AsyrafHussin/malaysia-postcodes/main/all.json"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        cache = {}
        for state_obj in data.get('state', []):
            state_name = state_obj['name']
            for city_obj in state_obj.get('city', []):
                city_name = city_obj['name']
                for postcode in city_obj.get('postcode', []):
                    cache[postcode] = {'state': state_name, 'city': city_name}
        _POSTCODE_CACHE = cache
        return cache
    except Exception as e:
        print("Postcode load error:", e)
        return {}

def fetch_malaysia_locations():
    if not _FLAT_CACHE:
        _FLAT_CACHE.update(_load_flat_malaysia_data())
    return _FLAT_CACHE.copy()

def fetch_malaysia_postcode(postcode):
    _load_postcode_malaysia_data()
    return _POSTCODE_CACHE.get(postcode)

def get_malaysia_regions():
    return {
        "Northern Region": ["Perlis", "Kedah", "Penang", "Perak"],
        "Central Region": ["Selangor", "Kuala Lumpur", "Putrajaya"],
        "Southern Region": ["Negeri Sembilan", "Melaka", "Johor"],
        "Eastern Region": ["Pahang", "Terengganu", "Kelantan"],
        "East Malaysia Region (Sabah/Sarawak)": ["Sabah", "Sarawak", "Labuan"]
    }

def fetch_malaysia_states(region_name):
    regions = get_malaysia_regions()
    return regions.get(region_name, [])

def fetch_malaysia_cities(state_name):
    url = "https://raw.githubusercontent.com/AsyrafHussin/malaysia-postcodes/main/all.json"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        for state in data['state']:
            if state['name'] == state_name:
                return [city['name'] for city in state['city']]
        return []
    except Exception as e:
        print(f"Location API error: {e}")
        return []

def get_cached_cities(state_name):
    if state_name not in _CITY_CACHE:
        _CITY_CACHE[state_name] = fetch_malaysia_cities(state_name)
    return _CITY_CACHE[state_name]

@app.route('/api/malaysia_regions', methods=['GET'])
def malaysia_regions():
    regions = get_malaysia_regions()
    return jsonify(regions), 200

@app.route('/api/malaysia_states', methods=['GET'])
def malaysia_states():
    region = request.args.get('region')
    if not region:
        return jsonify({"error": "Region parameter required"}), 400
    states = fetch_malaysia_states(region)
    return jsonify(states), 200

@app.route('/api/malaysia_cities', methods=['GET'])
def malaysia_cities():
    state = request.args.get('state')
    if not state:
        return jsonify({"error": "State parameter required"}), 400
    cities = get_cached_cities(state)
    return jsonify(cities), 200

@app.route('/api/malaysia_postcode', methods=['GET'])
def malaysia_postcode():
    postcode = request.args.get('postcode')
    if not postcode:
        return jsonify({"error": "Postcode required"}), 400
    if len(postcode) != 5 or not postcode.isdigit():
        return jsonify({"error": "Invalid postcode format"}), 400
    loc = fetch_malaysia_postcode(postcode)
    if not loc:
        return jsonify({"error": "Postcode not found"}), 404
    return jsonify(loc), 200

@app.route('/api/malaysia_locations', methods=['GET'])
def malaysia_locations():
    locations = fetch_malaysia_locations()
    return jsonify(locations), 200

# ===============================================================


# ---------------------- NOTIFICATION ENDPOINTS ----------------------
@app.route('/api/notifications', methods=['GET'])
def get_notifications():
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

@app.route('/api/unread_count', methods=['GET'])
def unread_notification_count():
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

@app.route('/api/mark_read', methods=['POST'])
def mark_notification_read():
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



from contractor import contractor_bp
app.register_blueprint(contractor_bp)

if __name__ == '__main__':
    app.run(debug=True, port=5000)