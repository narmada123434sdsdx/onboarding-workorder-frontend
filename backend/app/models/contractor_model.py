from sqlalchemy.sql import text
from datetime import datetime
from app.models.database import db


class ContractorModel:

    # ---------------- CREATE COMPANY ----------------
    @staticmethod
    def create_company(company_name, brn, hashed_password, phone, email, activation_token):
        sql = text("""
            INSERT INTO company_details_t (
                company_name, brn_number, password_hash, mailing_address, billing_address, contact_number,
                head_name, head_email, tin_number, active_status, status, activation_token, created_at
            ) VALUES (
                :company_name, :brn, :pw, '-', '-', :phone, '-', :email, '-', FALSE, 
                'registered', :token, :created_at
            )
        """)

        db.session.execute(sql, {
            "company_name": company_name,
            "brn": brn,
            "pw": hashed_password,
            "phone": phone,
            "email": email,
            "token": activation_token,
            "created_at": datetime.now(),
        })
        db.session.commit()
        return True

    # ---------------- GET COMPANY VIA TOKEN ----------------
    @staticmethod
    def get_company_by_token(token):
        sql = text("SELECT head_email FROM company_details_t WHERE activation_token = :token")
        row = db.session.execute(sql, {"token": token}).fetchone()
        return dict(row._mapping) if row else None

    # ---------------- ACTIVATE COMPANY ----------------
    @staticmethod
    def activate_company(token):
        sql = text("""
            UPDATE company_details_t
            SET active_status = TRUE, status = 'pending'
            WHERE activation_token = :token
        """)
        result = db.session.execute(sql, {"token": token})
        db.session.commit()
        return result.rowcount > 0

    # ---------------- LOGIN ----------------
    @staticmethod
    def get_contractor_by_email(email):
        sql = text("""
            SELECT password_hash, active_status 
            FROM company_details_t 
            WHERE head_email = :email
        """)
        row = db.session.execute(sql, {"email": email}).fetchone()
        return dict(row._mapping) if row else None

    # ---------------- OTP ----------------
    @staticmethod
    def save_otp(email, otp):
        sql = text("""
            INSERT INTO otp_codes_t (email_id, otp_code) 
            VALUES (:email, :otp)
        """)
        db.session.execute(sql, {"email": email, "otp": otp})
        db.session.commit()

    @staticmethod
    def validate_otp(email):
        sql = text("""
            SELECT otp_code FROM otp_codes_t
            WHERE email_id = :email
              AND created_at > NOW() - INTERVAL '5 minutes'
        """)
        row = db.session.execute(sql, {"email": email}).fetchone()
        return dict(row._mapping) if row else None

    @staticmethod
    def delete_otp(email):
        sql = text("DELETE FROM otp_codes_t WHERE email_id = :email")
        db.session.execute(sql, {"email": email})
        db.session.commit()

    # ---------------- BASIC INFO ----------------
    @staticmethod
    def get_basic_info(email):
        sql = text("""
            SELECT company_id, head_email, contact_number, company_name, status
            FROM company_details_t
            WHERE head_email = :email
        """)
        row = db.session.execute(sql, {"email": email}).fetchone()
        return dict(row._mapping) if row else None

    # ---------------- FULL PROFILE WITH SERVICES & BANK ----------------
    @staticmethod
    def get_company_profile(email):
        # Step 1: Get main company info
        sql = text("""
            SELECT company_id, company_name, brn_number, billing_address, mailing_address,
                contact_number, tin_number, alternate_contact_number, head_name, 
                head_email, status
            FROM company_details_t 
            WHERE head_email = :email
        """)

        row = db.session.execute(sql, {"email": email}).fetchone()
        if not row:
            return None

        company = dict(row._mapping)
        company_id = company["company_id"]

        # Step 2: Get services
        sql_services = text("""
            SELECT service_name, service_rate, service_location 
            FROM company_services_t 
            WHERE company_id = :id
        """)
        services = db.session.execute(sql_services, {"id": company_id}).fetchall()
        company["services"] = [dict(s._mapping) for s in services]

        # Step 3: Get bank details
        sql_bank = text("SELECT * FROM company_bank_details_t WHERE company_id = :id")
        bank_row = db.session.execute(sql_bank, {"id": company_id}).fetchone()

        if bank_row:
            bank = dict(bank_row._mapping)

            # convert memoryview fields to bytes
            for k, v in bank.items():
                if isinstance(v, memoryview):
                    bank[k] = v.tobytes()

            company["bank_details"] = bank
        
        return company

    # ---------------- UPDATE PROFILE ----------------
    @staticmethod
    def update_company_profile(email, company_data, services, logo_bytes, cert_bytes):
        try:
            # Step 1: Update logo & certificate
            sql_update_files = text("""
                UPDATE company_details_t
                SET 
                    logo_path = COALESCE(:logo, logo_path),
                    certificate_path = COALESCE(:cert, certificate_path)
                WHERE head_email = :email
            """)
            db.session.execute(sql_update_files, {
                "logo": logo_bytes,
                "cert": cert_bytes,
                "email": email,
            })

            # Step 2: Get company_id
            sql_get_id = text("SELECT company_id FROM company_details_t WHERE head_email = :email")
            row = db.session.execute(sql_get_id, {"email": email}).fetchone()
            if not row:
                return False

            company_id = row._mapping["company_id"]     # FIXED 🔥

            # Step 3: Update main company profile
            sql_update_main = text("""
                UPDATE company_details_t
                SET company_name = :name,
                    brn_number = :brn,
                    tin_number = :tin,
                    mailing_address = :mailing,
                    billing_address = :billing,
                    contact_number = :contact,
                    alternate_contact_number = :alternate,
                    head_name = :head,
                    status = 'pending',
                    updated_at = :updated
                WHERE head_email = :email
            """)
            db.session.execute(sql_update_main, {
                "name": company_data["company_name"],
                "brn": company_data["brn_number"],
                "tin": company_data["tin_number"],
                "mailing": company_data["mailing_address"],
                "billing": company_data["billing_address"],
                "contact": company_data["contact_number"],
                "alternate": company_data["alternate_contact"],
                "head": company_data["contact_person"],
                "updated": datetime.now(),
                "email": email
            })

            # Step 4: Remove old services
            db.session.execute(
                text("DELETE FROM company_services_t WHERE company_id = :id"),
                {"id": company_id}
            )

            # Step 5: Insert new services
            sql_insert_svc = text("""
                INSERT INTO company_services_t (
                    company_id, service_name, service_rate, service_location, service_region
                ) VALUES (:id, :name, :rate, :loc, :region)
            """)

            for svc in services:
                db.session.execute(sql_insert_svc, {
                    "id": company_id,
                    "name": svc["service_name"],
                    "rate": svc["service_rate"],
                    "loc": svc["service_location"],
                    "region": svc.get("service_region", "")
                })

            db.session.commit()
            return True

        except Exception as e:
            print("Profile update error:", e)
            db.session.rollback()
            return False

    # ---------------- UPDATE BANK ----------------
    @staticmethod
    def update_company_bank(email, bank_details, statement_bytes):
        try:
            # Step 1: Get company_id
            sql_id = text("SELECT company_id FROM company_details_t WHERE head_email = :email")
            row = db.session.execute(sql_id, {"email": email}).fetchone()
            if not row:
                return False

            company_id = row["company_id"]

            # Step 2: Insert/update bank info
            sql_upsert = text("""
                INSERT INTO company_bank_details_t 
                    (company_id, swift_code, holder_name, account_number, bank_name, created_at)
                VALUES (:id, :swift, :holder, :acc, :bank, NOW())
                ON CONFLICT (company_id) DO UPDATE SET
                    swift_code = EXCLUDED.swift_code,
                    holder_name = EXCLUDED.holder_name,
                    account_number = EXCLUDED.account_number,
                    updated_at = NOW()
            """)
            db.session.execute(sql_upsert, {
                "id": company_id,
                "swift": bank_details["swift_enc"],
                "holder": bank_details["holder_name"],
                "acc": bank_details["account_number_enc"],
                "bank": bank_details["bank_name"]
            })

            # Step 3: Update bank statement if column exists
            if statement_bytes:
                sql_update_stmt = text("""
                    UPDATE company_bank_details_t 
                    SET bank_statement = :statement
                    WHERE company_id = :id
                """)
                db.session.execute(sql_update_stmt, {
                    "statement": statement_bytes,
                    "id": company_id
                })

            db.session.commit()
            return True

        except Exception as e:
            print("Bank update error:", e)
            db.session.rollback()
            return False

    # ---------------- NOTIFICATIONS ----------------
    @staticmethod
    def fetch_notifications(email):
        sql = text("""
            SELECT message_id, message, sent_at, is_read, notification_type
            FROM admin_messages_t
            WHERE email_id = :email
            ORDER BY sent_at DESC
        """)
        rows = db.session.execute(sql, {"email": email}).fetchall()
        return [dict(r._mapping) for r in rows]

    @staticmethod
    def fetch_unread_count(email):
        sql = text("""
            SELECT COUNT(*) AS count
            FROM admin_messages_t
            WHERE email_id = :email AND is_read = FALSE
        """)
        row = db.session.execute(sql, {"email": email}).fetchone()
        return row._mapping["count"] if row else 0

    @staticmethod
    def mark_notification_read(message_id):
        sql = text("""
            UPDATE admin_messages_t 
            SET is_read = TRUE 
            WHERE message_id = :id
        """)
        result = db.session.execute(sql, {"id": message_id})
        db.session.commit()
        return result.rowcount > 0
