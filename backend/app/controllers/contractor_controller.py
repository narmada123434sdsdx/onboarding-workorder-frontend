import bcrypt
import uuid
import re
import json
import random
import string
from app.utils.file_utils import save_uploaded_file
from app.models.contractor_model import ContractorModel
from app.utils.encrypt_utils import cipher 
from app.utils.email_utils import (
    send_email,
    send_contractor_activation_email,
    send_contractor_otp_email,
    send_contractor_profile_submitted_email,
    send_admin_new_contractor_notification
)
from app.config import Config

ADMIN_EMAIL = Config.FROM_EMAIL


class ContractorController:

    # ---------------- Signup ----------------
    @staticmethod
    def signup(data):
        brn = data.get('business_registration_number')
        company_name = data.get('company_name')
        email = data.get('email_id')
        phone = data.get('phone_number')
        password = data.get('password')

        if not all([brn, company_name, email, phone, password]):
            return {"error": "All fields are required"}, 400

        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        token = str(uuid.uuid4())

        ContractorModel.create_company(company_name, brn, hashed, phone, email, token)
        send_contractor_activation_email(email, token)

        return {"message": "Signup successful. Activation link sent to your email."}, 200

    # ---------------- Activate ----------------
    @staticmethod
    def activate(token):
        company = ContractorModel.get_company_by_token(token)
        if not company:
            return {"error": "Invalid activation token"}, 400

        ContractorModel.activate_company(token)
        return {"message": "Company account activated successfully.", "email_id": company['head_email']}, 200

    # ---------------- Login ----------------
    @staticmethod
    def login(data):
        email = data.get('email')
        password = data.get('password')
        if not email or not password:
            return {"error": "Email and password required"}, 400

        contractor = ContractorModel.get_contractor_by_email(email)
        if contractor and bcrypt.checkpw(password.encode(), contractor['password_hash'].encode()):
            if contractor['active_status']:
                otp = ''.join(random.choices(string.digits, k=6))
                ContractorModel.save_otp(email, otp)
                send_contractor_otp_email(email, otp)
                return {"message": "OTP sent to contractor email"}, 200
            else:
                return {"error": "Account not activated"}, 401
        return {"error": "Invalid credentials"}, 401

    # ---------------- Verify OTP ----------------
    @staticmethod
    def verify_otp(data):
        email = data.get('email')
        otp = data.get('otp')
        if not email or not otp:
            return {"error": "Email and OTP required"}, 400

        record = ContractorModel.validate_otp(email)
        if record and record['otp_code'] == otp:
            ContractorModel.delete_otp(email)

            # ✅ Fetch contractor info after OTP verification
            contractor = ContractorModel.get_basic_info(email)
            if not contractor:
                return {"error": "Contractor not found"}, 404

            return {
                "message": "OTP verified successfully",
                "contractor": contractor
            }, 200

        return {"error": "Invalid or expired OTP"}, 401

    # ---------------- Resend OTP ----------------
    @staticmethod
    def resend_otp(data):
        email = data.get('email')
        if not email:
            return {"error": "Email required"}, 400

        ContractorModel.delete_otp(email)
        otp = ''.join(random.choices(string.digits, k=6))
        ContractorModel.save_otp(email, otp)
        send_contractor_otp_email(email, otp)
        return {"message": "OTP resent successfully"}, 200

    # ---------------- Profile ----------------
    @staticmethod
    def get_profile(data):
        email = data.get('email')
        if not email:
            return {"error": "Email required"}, 400

        profile = ContractorModel.get_company_profile(email)
        if not profile:
            return {"error": "Company not found"}, 404

        return profile, 200

    # ---------------- Update Company Profile ----------------
    @staticmethod
    def update_company_profile(form_data, files):
        email = form_data.get('email')
        if not email:
            return {"error": "Email required"}, 400

        company_data = {
            "company_name": form_data.get('company_name'),
            "brn_number": form_data.get('brn_number'),
            "tin_number": form_data.get('tin_number'),
            "mailing_address": form_data.get('mailing_address'),
            "billing_address": form_data.get('billing_address'),
            "contact_number": form_data.get('contact_number'),
            "alternate_contact": form_data.get('alternate_contact'),
            "contact_person": form_data.get('contact_person')
        }

        # Parse services JSON
        try:
            services = json.loads(form_data.get('services', '[]'))
            if not isinstance(services, list):
                services = []
        except Exception:
            services = []

        # logo_path = save_uploaded_file(files.get('company_logo'), "company_logos")
        # cert_path = save_uploaded_file(files.get('certificate'), "certificates")

        logo_file = files.get('company_logo')
        cert_file = files.get('certificate')

        logo_bytes = logo_file.read() if logo_file else None
        cert_bytes = cert_file.read() if cert_file else None


        success = ContractorModel.update_company_profile(email, company_data, services, logo_bytes, cert_bytes)
        if not success:
            return {"error": "Failed to update company profile"}, 500

        # Notify admin and contractor
        send_contractor_profile_submitted_email(email, company_data['company_name'])
        send_admin_new_contractor_notification(ADMIN_EMAIL, company_data['company_name'], email)

        return {"message": "Company profile updated and submitted for approval", "status": "pending"}, 200

    # ---------------- Update Company Bank ----------------
    @staticmethod
    def update_company_bank(form_data, files):
        email = form_data.get('email')
        swift = (form_data.get('swift') or '').upper()
        bank_name = form_data.get('bank_name')
        holder_name = form_data.get('holder_name')
        account_number = form_data.get('account_number')
        statement = files.get('bank_statement')

        if not all([email, swift, bank_name, holder_name, account_number, statement]):
            return {"error": "All fields are required"}, 400

        # Validate
        if not re.match(r'^[A-Z]{4}MY[A-Z0-9]{2}([A-Z0-9]{3})?$', swift):
            return {"error": "Invalid SWIFT format"}, 400
        if not re.match(r'^[0-9]{6,20}$', account_number):
            return {"error": "Invalid account number"}, 400

        # Encrypt sensitive info
        bank_details = {
            "swift_enc": cipher.encrypt(swift.encode()).decode(),
            "account_number_enc": cipher.encrypt(account_number.encode()).decode(),
            "holder_name": holder_name,
            "bank_name": bank_name
        }
        # Save file physically
        statement_path = save_uploaded_file(statement, "bank_statements")

        statement_bytes = statement.read()

        success = ContractorModel.update_company_bank(email, bank_details, statement_bytes)
        if not success:
            return {"error": "Failed to update bank details"}, 500

        send_email(email, "Bank Details Submitted", "Your bank details have been successfully submitted and are stored securely.")
        return {"message": "Bank details updated successfully"}, 200

    # ---------------- Notifications ----------------
    @staticmethod
    def get_notifications(email):
        if not email:
            return {"error": "Email required"}, 400

        notifications = ContractorModel.fetch_notifications(email)
        return notifications, 200

    @staticmethod
    def unread_count(email):
        if not email:
            return {"error": "Email required"}, 400

        count = ContractorModel.fetch_unread_count(email)
        return {"count": count}, 200

    @staticmethod
    def mark_as_read(data):
        message_id = data.get('message_id')
        if not message_id:
            return {"error": "Message ID required"}, 400

        updated = ContractorModel.mark_notification_read(message_id)
        if updated:
            return {"success": True}, 200
        return {"error": "Notification not found"}, 404