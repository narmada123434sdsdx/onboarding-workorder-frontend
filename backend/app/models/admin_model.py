from sqlalchemy.sql import text
from app.models.database import db
import pandas as pd


class AdminModel:

    # =======================
    # ADMIN AUTH
    # =======================
    @staticmethod
    def get_admin_by_email(email):
        sql = text("SELECT * FROM admins_t WHERE email = :email")
        row = db.session.execute(sql, {"email": email}).fetchone()
        return dict(row._mapping) if row else None

    @staticmethod
    def save_otp(email, otp):
        sql = text("""
            INSERT INTO otp_codes_t (email_id, otp_code, created_at)
            VALUES (:email, :otp, NOW())
        """)
        db.session.execute(sql, {"email": email, "otp": otp})
        db.session.commit()

    @staticmethod
    def verify_otp(email, otp):
        sql = text("""
            SELECT otp_code FROM otp_codes_t
            WHERE email_id = :email 
              AND created_at > NOW() - INTERVAL '5 minutes'
            ORDER BY created_at DESC 
            LIMIT 1
        """)
        row = db.session.execute(sql, {"email": email}).fetchone()
        return bool(row and row._mapping["otp_code"] == otp)

    @staticmethod
    def delete_otp(email):
        sql = text("DELETE FROM otp_codes_t WHERE email_id = :email")
        db.session.execute(sql, {"email": email})
        db.session.commit()

    # =======================
    # PROVIDERS
    # =======================
    @staticmethod
    def list_providers():
        sql = text("""
            SELECT provider_id, full_name, email_id, contact_number, status,
                   id_type, id_number, mailing_address, billing_address,
                   alternate_contact_number, tin_number, created_at
            FROM providers_t
            ORDER BY created_at DESC
        """)
        rows = db.session.execute(sql).fetchall()
        return [dict(r._mapping) for r in rows]

    @staticmethod
    def get_provider_services(provider_ids):
        if not provider_ids:
            return []
        sql = text("""
            SELECT provider_id, service_name, service_rate, region, state, city
            FROM provider_services_t
            WHERE provider_id = ANY(:ids)
            ORDER BY provider_id, service_name
        """)
        rows = db.session.execute(sql, {"ids": provider_ids}).fetchall()
        return [dict(r._mapping) for r in rows]

    @staticmethod
    def approve_provider(email):
        sql = text("""
            UPDATE providers_t 
            SET status = 'approved'
            WHERE email_id = :email AND status = 'pending'
            RETURNING provider_id, full_name, contact_number
        """)
        row = db.session.execute(sql, {"email": email}).fetchone()
        db.session.commit()
        return dict(row._mapping) if row else None  # FIXED

    @staticmethod
    def reject_provider(email):
        sql = text("""
            UPDATE providers_t 
            SET status = 'rejected'
            WHERE email_id = :email AND status = 'pending'
        """)
        result = db.session.execute(sql, {"email": email})
        db.session.commit()
        return result.rowcount > 0

    # =======================
    # CONTRACTORS
    # =======================
    @staticmethod
    def list_contractors():
        sql = text("""
            SELECT company_id, company_name, head_email, contact_number, status, created_at
            FROM company_details_t
            ORDER BY created_at DESC
        """)
        rows = db.session.execute(sql).fetchall()
        return [dict(r._mapping) for r in rows]

    @staticmethod
    def get_contractor_services_by_company_ids(company_ids):
        if not company_ids:
            return []
        sql = text("""
            SELECT company_id, service_name, service_rate, service_location
            FROM company_services_t
            WHERE company_id = ANY(:ids)
        """)
        rows = db.session.execute(sql, {"ids": company_ids}).fetchall()
        return [dict(r._mapping) for r in rows]

    @staticmethod
    def get_contractor_by_email(email):
        sql = text("""
            SELECT company_id, company_name, head_email, contact_number, 
                   status, brn_number, head_name
            FROM company_details_t
            WHERE head_email = :email
        """)
        row = db.session.execute(sql, {"email": email}).fetchone()
        return dict(row._mapping) if row else None  # FIXED

    @staticmethod
    def approve_contractor(email):
        sql = text("""
            UPDATE company_details_t 
            SET status='approved'
            WHERE head_email=:email AND status='pending'
        """)
        result = db.session.execute(sql, {"email": email})
        db.session.commit()
        return result.rowcount > 0

    @staticmethod
    def reject_contractor(email):
        sql = text("""
            UPDATE company_details_t 
            SET status='rejected'
            WHERE head_email=:email AND status='pending'
        """)
        result = db.session.execute(sql, {"email": email})
        db.session.commit()
        return result.rowcount > 0

    @staticmethod
    def get_contractor_services(company_id):
        sql = text("""
            SELECT service_name, service_rate, service_location
            FROM company_services_t
            WHERE company_id = :id
        """)
        rows = db.session.execute(sql, {"id": company_id}).fetchall()
        return [dict(r._mapping) for r in rows]

    # =======================
    # ADMIN MESSAGES / NOTIFICATIONS
    # =======================
    @staticmethod
    def insert_admin_message(email, message, notification_type):
        sql = text("""
            INSERT INTO admin_messages_t (email_id, message, sent_at, is_read, notification_type)
            VALUES (:email, :msg, NOW(), :read, :ntype)
        """)
        db.session.execute(sql, {
            "email": email,
            "msg": message,
            "read": False,
            "ntype": notification_type
        })
        db.session.commit()

    # =======================
    # STANDARD RATES
    # =======================
    @staticmethod
    def upload_standard_rate_excel(saved_path):
        df = pd.read_excel(saved_path)
        required = {'service_name', 'service_location', 'service_rate', 'client'}

        if not required.issubset(df.columns):
            raise ValueError("Missing required columns")

        sql = text("""
            INSERT INTO standard_rates_t 
                (service_name, service_location, service_rate, client)
            VALUES 
                (:name, :loc, :rate, :client)
            ON CONFLICT (service_name, service_location)
            DO UPDATE SET 
                service_rate = EXCLUDED.service_rate,
                client = EXCLUDED.client
        """)

        for _, row in df.iterrows():
            db.session.execute(sql, {
                "name": row["service_name"],
                "loc": row["service_location"],
                "rate": row["service_rate"],
                "client": row["client"]
            })

        db.session.commit()

    @staticmethod
    def list_standard_rates():
        sql = text("SELECT * FROM standard_rates_t ORDER BY service_name, service_location")
        rows = db.session.execute(sql).fetchall()
        return [dict(r._mapping) for r in rows]

    @staticmethod
    def add_or_upsert_standard_rate(service_name, service_location, service_rate, client):
        sql = text("""
            INSERT INTO standard_rates_t (service_name, service_location, service_rate, client)
            VALUES (:name, :loc, :rate, :client)
            ON CONFLICT (service_name, service_location)
            DO UPDATE SET 
                service_rate = EXCLUDED.service_rate,
                client = EXCLUDED.client
        """)
        db.session.execute(sql, {
            "name": service_name,
            "loc": service_location,
            "rate": service_rate,
            "client": client
        })
        db.session.commit()

    @staticmethod
    def update_standard_rate_by_id(rate_id, service_name, service_location, service_rate, client):
        sql = text("""
            UPDATE standard_rates_t
            SET service_name=:name, service_location=:loc, 
                service_rate=:rate, client=:client
            WHERE id=:id
        """)
        db.session.execute(sql, {
            "id": rate_id,
            "name": service_name,
            "loc": service_location,
            "rate": service_rate,
            "client": client
        })
        db.session.commit()

    @staticmethod
    def delete_standard_rate_by_id(rate_id):
        sql = text("DELETE FROM standard_rates_t WHERE id = :id")
        db.session.execute(sql, {"id": rate_id})
        db.session.commit()

    @staticmethod
    def list_rates_compact():
        sql = text("""
            SELECT id, service_name, service_location, service_rate, client
            FROM standard_rates_t
            ORDER BY service_name, service_location
        """)
        rows = db.session.execute(sql).fetchall()
        return [dict(r._mapping) for r in rows]
