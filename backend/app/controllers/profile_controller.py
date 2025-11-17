import json, base64
from app.utils.file_utils import save_uploaded_file
from app.models.profile_model import ProfileModel
from app.utils.encrypt_utils import decrypt_value
from app.utils.email_utils import send_email
from app.config import Config

ADMIN_EMAIL = Config.EMAIL_CONFIG['sender_email']


class ProfileController:

    # ---------- Fetch Profile ----------
    @staticmethod
    def get_profile(email):
        provider = ProfileModel.get_provider(email)
        if not provider:
            return {"error": "Provider not found"}, 404

        provider_id = provider['provider_id']

        # Get services
        services_rows = ProfileModel.get_services(provider_id)
        services = [
            {
                "service_name": s['service_name'],
                "service_rate": float(s['service_rate']) if s['service_rate'] else 0.0,
                "region": s.get('region') or '',
                "state": s.get('state') or '',
                "city": s.get('city') or ''
            } for s in services_rows
        ]

        # Get bank details
        bank_row = ProfileModel.get_bank(provider_id)
        bank_details = None
        if bank_row:
            bank_details = {
                "bank_name": bank_row.get('bank_name'),
                "swift": decrypt_value(bank_row.get('swift_code')),
                "bank_account_number": decrypt_value(bank_row.get('bank_account_number')),
                "holder_name": decrypt_value(bank_row.get('account_holder_name')),
                "bank_statement": base64.b64encode(bank_row['bank_statement']).decode('utf-8')
                if bank_row.get('bank_statement') else None
            }

        response = {
            **provider,
            "profile_pic": base64.b64encode(provider['profile_pic']).decode('utf-8')
            if provider.get('profile_pic') else None,
            "authorized_certificate": base64.b64encode(provider['authorized_certificate']).decode('utf-8')
            if provider.get('authorized_certificate') else None,
            "services": services,
            "bank_details": bank_details
        }

        return response, 200

    # ---------- Update Profile ----------
    @staticmethod
    def update_profile(form, files):
        email = form.get('email')
        if not email:
            return {"error": "Email is required"}, 400

        # Prepare fields
        full_name = form.get('full_name')
        id_type = form.get('id_type', '')
        id_number = form.get('id_number', '')
        mailing_address = form.get('mailing_address', '')
        billing_address = form.get('billing_address', '')
        contact_number = form.get('contact_number')
        alternate_contact_number = form.get('alternate_contact_number', '')
        tin_number = form.get('tin_number', '')
        services_json = form.get('services', '[]')

        # profile_path = save_uploaded_file(files.get('profile_image'), "profile_pics")
        # cert_path = save_uploaded_file(files.get('certificate'), "certificates")

        profile_pic = files['profile_image'].read() if 'profile_image' in files else None
        cert_file = files['certificate'].read() if 'certificate' in files else None

        provider = ProfileModel.get_provider(email)
        if not provider:
            return {"error": "Provider not found"}, 404

        provider_id = provider['provider_id']

        updated_data = {
            "full_name": full_name,
            "id_type": id_type,
            "id_number": id_number,
            "mailing_address": mailing_address,
            "billing_address": billing_address,
            "contact_number": contact_number,
            "alternate_contact_number": alternate_contact_number,
            "tin_number": tin_number,
            "profile_pic": profile_pic if profile_pic else provider['profile_pic'],
            "authorized_certificate": cert_file if cert_file else provider['authorized_certificate']
        }

        # Update provider info
        ProfileModel.update_provider(email, updated_data)

        # Update services
        ProfileModel.delete_services(provider_id)

        try:
            services_parsed = json.loads(services_json)
        except Exception:
            services_parsed = []

        bulk_data = []
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
                    region, state, city = '', '', location_key
                    try:
                        price_val = float(price)
                    except Exception:
                        price_val = 0.0
                    bulk_data.append((provider_id, service_name, price_val, region, state, city))

        if bulk_data:
            ProfileModel.insert_services(bulk_data)

        # Send emails
        send_email(
            ADMIN_EMAIL,
            "New Provider for Approval",
            f"A new provider has submitted their profile.\n\nProvider Email: {email}\nPlease review and approve their details."
        )
        send_email(email, "Profile Submitted", "Your profile has been submitted and is pending admin approval.")

        return {"message": "Profile submitted for approval", "status": "pending"}, 200
