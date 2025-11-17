import bcrypt, uuid, random, string
from app.models.auth_model import AuthModel
from app.utils.email_utils import send_activation_email, send_otp_email, send_reset_otp_email

class AuthController:
    @staticmethod
    def signup(data):
        email = data['email']
        password = data['password']
        phone = data.get('phone_number')
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        token = str(uuid.uuid4())

        AuthModel.insert_provider(email, hashed, phone, token)
        send_activation_email(email, token)
        return {"message": "Signup successful, check your email."}, 200

    @staticmethod
    def activate_account(token):
        user = AuthModel.get_provider_by_token(token)
        if not user:
            return {"error": "Invalid token"}, 400
        AuthModel.activate_account(token)
        return {"message": "Account activated successfully", "email": user['email_id']}, 200

    @staticmethod
    def login(email, password):
        provider = AuthModel.get_provider_login(email)
        if not provider or not bcrypt.checkpw(password.encode(), provider['password_hash'].encode()):
            return {"error": "Invalid credentials"}, 401
        if not provider['active_status']:
            return {"error": "Account not activated"}, 401

        otp = ''.join(random.choices(string.digits, k=6))
        AuthModel.insert_otp(email, otp)
        send_otp_email(email, otp)
        return {"message": "OTP sent to email"}, 200

    @staticmethod
    def verify_otp(email, otp):
        record = AuthModel.get_otp(email)
        if record and record['otp_code'] == otp:
            AuthModel.delete_otp(email)
            return {"message": "OTP verified", "email": email}, 200
        return {"error": "Invalid or expired OTP"}, 401

    @staticmethod
    def resend_otp(email):
        AuthModel.delete_otp(email)
        otp = ''.join(random.choices(string.digits, k=6))
        AuthModel.insert_otp(email, otp)
        send_otp_email(email, otp)
        return {"message": "OTP resent successfully"}, 200

    @staticmethod
    def forgot_send_otp(email):
        provider = AuthModel.get_active_provider(email)
        if not provider or not provider['active_status']:
            return {"error": "Account not found or not activated"}, 404

        otp = ''.join(random.choices(string.digits, k=6))
        AuthModel.insert_otp(email, otp)
        send_reset_otp_email(email, otp)
        return {"message": "Reset OTP sent to email"}, 200

    @staticmethod
    def verify_reset_otp(email, otp):
        record = AuthModel.get_otp(email)
        if record and record['otp_code'] == otp:
            AuthModel.delete_otp(email)
            reset_token = str(uuid.uuid4())
            AuthModel.set_reset_token(email, reset_token)
            return {"message": "OTP verified successfully", "reset_token": reset_token}, 200
        return {"error": "Invalid or expired OTP"}, 401

    @staticmethod
    def reset_password(email, reset_token, password):
        info = AuthModel.get_reset_info(email)
        if not info:
            return {"error": "Provider not found"}, 404

        from datetime import datetime
        if (info['reset_token'] != reset_token or not info['reset_expiry'] or info['reset_expiry'] < datetime.now()):
            return {"error": "Invalid or expired reset token"}, 400

        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        AuthModel.update_password(email, hashed)
        return {"message": "Password reset successfully"}, 200
