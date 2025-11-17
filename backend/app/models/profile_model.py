from sqlalchemy.sql import text
from app.models.database import db


class ProfileModel:

    # ---------------- FETCH PROVIDER ----------------
    @staticmethod
    def get_provider(email):
        sql = text("""
            SELECT provider_id, full_name, id_type, id_number, mailing_address, billing_address,
                   contact_number, alternate_contact_number, tin_number,
                   profile_pic, authorized_certificate, status
            FROM providers_t
            WHERE email_id = :email
        """)
        row = db.session.execute(sql, {"email": email}).fetchone()
        return dict(row._mapping) if row else None   # FIXED

    # ---------------- UPDATE PROVIDER ----------------
    @staticmethod
    def update_provider(email, data):
        sql = text("""
            UPDATE providers_t
            SET full_name = :full_name,
                id_type = :id_type,
                id_number = :id_number,
                mailing_address = :mailing_address,
                billing_address = :billing_address,
                contact_number = :contact_number,
                alternate_contact_number = :alternate_contact,
                tin_number = :tin_number,
                profile_pic = :profile_pic,
                authorized_certificate = :certificate,
                status = 'pending'
            WHERE email_id = :email
        """)

        db.session.execute(sql, {
            "full_name": data["full_name"],
            "id_type": data["id_type"],
            "id_number": data["id_number"],
            "mailing_address": data["mailing_address"],
            "billing_address": data["billing_address"],
            "contact_number": data["contact_number"],
            "alternate_contact": data["alternate_contact_number"],
            "tin_number": data["tin_number"],
            "profile_pic": data["profile_pic"],            # bytes or None
            "certificate": data["authorized_certificate"], # bytes or None
            "email": email
        })

        db.session.commit()

    # ---------------- DELETE ALL SERVICES ----------------
    @staticmethod
    def delete_services(provider_id):
        sql = text("DELETE FROM provider_services_t WHERE provider_id = :id")
        db.session.execute(sql, {"id": provider_id})
        db.session.commit()

    # ---------------- BULK INSERT SERVICES ----------------
    @staticmethod
    def insert_services(bulk_data):
        """
        bulk_data must be a list of tuples:
        [(provider_id, service_name, service_rate, region, state, city), ...]
        """

        sql = text("""
            INSERT INTO provider_services_t 
                (provider_id, service_name, service_rate, region, state, city)
            VALUES (:provider_id, :service_name, :service_rate, :region, :state, :city)
        """)

        converted = []
        for row in bulk_data:
            converted.append({
                "provider_id": row[0],
                "service_name": row[1],
                "service_rate": row[2],
                "region": row[3],
                "state": row[4],
                "city": row[5]
            })

        db.session.execute(sql, converted)
        db.session.commit()

    # ---------------- FETCH SERVICES ----------------
    @staticmethod
    def get_services(provider_id):
        sql = text("""
            SELECT service_name, service_rate, region, state, city
            FROM provider_services_t
            WHERE provider_id = :id
            ORDER BY created_at
        """)
        rows = db.session.execute(sql, {"id": provider_id}).fetchall()
        return [dict(r._mapping) for r in rows]   # FIXED

    # ---------------- FETCH BANK ----------------
    @staticmethod
    def get_bank(provider_id):
        sql = text("""
            SELECT bank_name, swift_code, bank_account_number, 
                   account_holder_name, bank_statement
            FROM providers_bank_details_t
            WHERE provider_id = :id
            LIMIT 1
        """)
        row = db.session.execute(sql, {"id": provider_id}).fetchone()

        if not row:
            return None

        bank = dict(row._mapping)   # FIXED

        # Convert memoryview → bytes
        for k, v in bank.items():
            if isinstance(v, memoryview):
                bank[k] = v.tobytes()

        return bank
