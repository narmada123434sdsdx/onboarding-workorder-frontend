# app/controllers/admin_controller.py
import os, bcrypt, random, string
from app.models.admin_model import AdminModel
from app.utils.email_utils import send_email, send_admin_otp_email
from app.utils.pdf_utils import generate_certificate_pdf

class AdminController:

    # ===== Auth =====
    @staticmethod
    def login(email, password):
        if not email or not password:
            return {"error": "Email and password required"}, 400

        admin = AdminModel.get_admin_by_email(email)
        if not admin or not bcrypt.checkpw(password.encode(), admin['password_hash'].encode()):
            return {"error": "Invalid credentials"}, 401

        otp = ''.join(random.choices(string.digits, k=6))
        AdminModel.save_otp(email, otp)
        send_admin_otp_email(email, otp)
        return {"message": "OTP sent to email"}, 200

    @staticmethod
    def verify_otp(email, otp):
        if not email or not otp:
            return {"error": "Email and OTP required"}, 400
        ok = AdminModel.verify_otp(email, otp)
        if ok:
            AdminModel.delete_otp(email)
            return {"message": "OTP verified successfully", "admin_email": email}, 200
        return {"error": "Invalid or expired OTP"}, 401

    # ===== Providers =====
    @staticmethod
    def list_providers():
        providers = AdminModel.list_providers()
        provider_ids = [p['provider_id'] for p in providers]
        services = AdminModel.get_provider_services(provider_ids)

        # group services per provider
        svc_map = {}
        for s in services:
            pid = s['provider_id']
            svc_map.setdefault(pid, []).append({
                "service_name": s['service_name'],
                "service_rate": float(s['service_rate']),
                "region": s.get('region') or '',
                "state": s.get('state') or '',
                "city": s.get('city') or '',
                "service_location": ", ".join([v for v in [s.get('city'), s.get('state'), s.get('region')] if v])
            })

        for p in providers:
            arr = svc_map.get(p['provider_id'], [])
            p['services'] = arr
            p['service_locations'] = ", ".join(sorted({x['service_location'] for x in arr})) if arr else "N/A"
        return providers, 200

    @staticmethod
    def approve_provider(email):
        core = AdminModel.approve_provider(email)
        if not core:
            return {"error": "Provider not found or not pending"}, 404

        # fetch services for PDF
        services = AdminModel.get_provider_services([core['provider_id']])
        # compose details
        details = {
            "Provider ID": core['provider_id'],
            "Full Name": core['full_name'],
            "Email": email,
            "Phone Number": core['contact_number'],
            "Services": [{
                "Service Name": s['service_name'],
                "Service Rate": s['service_rate'],
                "Service Location": (s.get('state') or s.get('city') or 'N/A')
            } for s in services]
        }

        pdf_path = generate_certificate_pdf(details, email)
        msg = "Your provider profile has been approved. You can now submit your bank details."
        AdminModel.insert_admin_message(email, msg, "approval")

        try:
            send_email(email, "Profile Approved", msg, pdf_path)
            return {"message": "Provider approved"}, 200
        finally:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)

    @staticmethod
    def reject_provider(email):
        if not AdminModel.reject_provider(email):
            return {"error": "Provider not found or not pending"}, 404
        msg = "Your provider profile has been rejected. Please contact admin for more details."
        AdminModel.insert_admin_message(email, msg, "rejection")
        send_email(email, "Profile Rejected", msg)
        return {"message": "Provider rejected"}, 200

    @staticmethod
    def send_message_provider(email, message):
        if not email or not message:
            return {"error": "Email and message required"}, 400
        AdminModel.insert_admin_message(email, message, "message")
        send_email(email, "Message from Ontract Admin", message)
        return {"message": "Message sent and saved"}, 200

    # ===== Contractors =====
    @staticmethod
    def list_contractors():
        contractors = AdminModel.list_contractors()
        ids = [c['company_id'] for c in contractors]
        svcs = AdminModel.get_contractor_services_by_company_ids(ids)

        svc_map = {}
        for s in svcs:
            svc_map.setdefault(s['company_id'], []).append({
                "service_name": s['service_name'],
                "service_location": s['service_location'],
                "service_rate": float(s['service_rate'])
            })

        for c in contractors:
            c['services'] = svc_map.get(c['company_id'], [])
        return contractors, 200

    @staticmethod
    def approve_contractor(email):
        if not AdminModel.approve_contractor(email):
            return {"error": "Company not found or not pending"}, 404

        company = AdminModel.get_contractor_by_email(email)
        services = AdminModel.get_contractor_services(company['company_id'])
        details = {
            "Company ID": company['brn_number'],
            "Company Name": company['company_name'],
            "Name": company['head_name'],
            "Email": company['head_email'],
            "Contact Number": company['contact_number'],
            "Services": [{
                "Service Name": s['service_name'],
                "Service Rate": s['service_rate'],
                "Service Location": s['service_location']
            } for s in services]
        }

        pdf_path = generate_certificate_pdf(details, email)
        msg = "Your company has been approved. You can now proceed to submit bank details."
        AdminModel.insert_admin_message(email, msg, "approval")

        try:
            send_email(email, "Company Approved", msg, pdf_path)
            return {"message": "Contractor approved"}, 200
        finally:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)

    @staticmethod
    def reject_contractor(email):
        if not AdminModel.reject_contractor(email):
            return {"error": "Not found or already processed"}, 404
        msg = "Your company registration has been rejected. Contact admin for details."
        AdminModel.insert_admin_message(email, msg, "rejection")
        send_email(email, "Company Rejected", msg)
        return {"message": "Contractor rejected"}, 200

    @staticmethod
    def send_message_contractor(email, message):
        if not email or not message:
            return {"error": "Email and message required"}, 400
        AdminModel.insert_admin_message(email, message, "message")
        send_email(email, "Message from Admin", message)
        return {"message": "Message sent"}, 200

    # ===== Standard Rates =====
    @staticmethod
    def upload_excel(file_storage):
        if not file_storage or not file_storage.filename.lower().endswith(('.xlsx', '.xls')):
            return {"error": "Only Excel files are allowed"}, 400
        os.makedirs("uploads", exist_ok=True)
        path = os.path.join("uploads", file_storage.filename)
        file_storage.save(path)
        try:
            AdminModel.upload_standard_rate_excel(path)
            return {"message": "File uploaded and data saved"}, 200
        finally:
            if os.path.exists(path):
                os.remove(path)

    @staticmethod
    def list_standard_rates():
        return AdminModel.list_standard_rates(), 200

    @staticmethod
    def add_standard_rate(payload):
        AdminModel.add_or_upsert_standard_rate(
            payload['service_name'],
            payload['service_location'],
            payload['service_rate'],
            payload['client']
        )
        return {"message": "Rate added"}, 201

    @staticmethod
    def update_standard_rate(rate_id, payload):
        AdminModel.update_standard_rate_by_id(
            rate_id,
            payload['service_name'],
            payload['service_location'],
            payload['service_rate'],
            payload['client']
        )
        return {"message": "Rate updated"}, 200

    @staticmethod
    def delete_standard_rate(rate_id):
        AdminModel.delete_standard_rate_by_id(rate_id)
        return {"message": "Rate deleted"}, 200

    @staticmethod
    def list_rates_compact():
        return AdminModel.list_rates_compact(), 200
