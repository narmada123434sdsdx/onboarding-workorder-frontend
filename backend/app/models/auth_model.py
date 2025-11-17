from datetime import datetime, timedelta
from app.models.database import db
from sqlalchemy.sql import text

class AuthModel:

    @staticmethod
    def insert_provider(email, hashed_pw, phone, token):
        sql = text("""
            INSERT INTO providers_t 
            (email_id, password_hash, contact_number, active_status, status, activation_token)
            VALUES (:email, :pw, :phone, :active, :status, :token)
        """)
        db.session.execute(sql, {
            "email": email,
            "pw": hashed_pw,
            "phone": phone,
            "active": False,
            "status": "registered",
            "token": token
        })
        db.session.commit()

    @staticmethod
    def get_provider_by_token(token):
        sql = text("SELECT email_id FROM providers_t WHERE activation_token = :token")
        row = db.session.execute(sql, {"token": token}).fetchone()
        return dict(row._mapping) if row else None   # FIXED

    @staticmethod
    def activate_account(token):
        sql = text("UPDATE providers_t SET active_status = TRUE WHERE activation_token = :token")
        db.session.execute(sql, {"token": token})
        db.session.commit()

    @staticmethod
    def get_provider_login(email):
        sql = text("""
            SELECT password_hash, active_status 
            FROM providers_t 
            WHERE email_id = :email
        """)
        row = db.session.execute(sql, {"email": email}).fetchone()
        return dict(row._mapping) if row else None   # FIXED

    @staticmethod
    def insert_otp(email, otp):
        sql = text("INSERT INTO otp_codes_t (email_id, otp_code) VALUES (:email, :otp)")
        db.session.execute(sql, {"email": email, "otp": otp})
        db.session.commit()

    @staticmethod
    def get_otp(email):
        sql = text("""
            SELECT otp_code 
            FROM otp_codes_t
            WHERE email_id = :email
              AND created_at > (NOW() - INTERVAL '5 minutes')
        """)
        row = db.session.execute(sql, {"email": email}).fetchone()
        return dict(row._mapping) if row else None   # FIXED

    @staticmethod
    def delete_otp(email):
        sql = text("DELETE FROM otp_codes_t WHERE email_id = :email")
        db.session.execute(sql, {"email": email})
        db.session.commit()

    @staticmethod
    def get_active_provider(email):
        sql = text("SELECT active_status FROM providers_t WHERE email_id = :email")
        row = db.session.execute(sql, {"email": email}).fetchone()
        return dict(row._mapping) if row else None   # FIXED

    @staticmethod
    def set_reset_token(email, token):
        expiry = datetime.now() + timedelta(minutes=10)
        sql = text("""
            UPDATE providers_t 
            SET reset_token = :token, reset_expiry = :expiry
            WHERE email_id = :email
        """)
        db.session.execute(sql, {"token": token, "expiry": expiry, "email": email})
        db.session.commit()

    @staticmethod
    def get_reset_info(email):
        sql = text("""
            SELECT reset_token, reset_expiry 
            FROM providers_t 
            WHERE email_id = :email
        """)
        row = db.session.execute(sql, {"email": email}).fetchone()
        return dict(row._mapping) if row else None   # FIXED

    @staticmethod
    def update_password(email, hashed):
        sql = text("""
            UPDATE providers_t 
            SET password_hash = :pw, reset_token = NULL, reset_expiry = NULL 
            WHERE email_id = :email
        """)
        db.session.execute(sql, {"pw": hashed, "email": email})
        db.session.commit()
