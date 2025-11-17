from sqlalchemy.sql import text
from app.models.database import db


class BankModel:

    @staticmethod
    def get_provider_id(email):
        sql = text("""
            SELECT provider_id 
            FROM providers_t 
            WHERE email_id = :email
        """)
        row = db.session.execute(sql, {"email": email}).fetchone()
        return dict(row._mapping) if row else None   # FIXED

    @staticmethod
    def get_bank_details(provider_id):
        sql = text("""
            SELECT *
            FROM providers_bank_details_t
            WHERE provider_id = :provider_id
        """)
        row = db.session.execute(sql, {"provider_id": provider_id}).fetchone()
        return dict(row._mapping) if row else None   # FIXED

    @staticmethod
    def update_bank(provider_id, bank_name, swift, acc, holder, statement):
        sql = text("""
            UPDATE providers_bank_details_t
            SET 
                bank_name = :bank_name,
                swift_code = :swift,
                bank_account_number = :acc,
                account_holder_name = :holder,
                bank_statement = :statement
            WHERE provider_id = :provider_id
        """)
        db.session.execute(sql, {
            "provider_id": provider_id,
            "bank_name": bank_name,
            "swift": swift,
            "acc": acc,
            "holder": holder,
            "statement": statement
        })
        db.session.commit()

    @staticmethod
    def insert_bank(provider_id, bank_name, swift, acc, holder, statement):
        sql = text("""
            INSERT INTO providers_bank_details_t 
                (provider_id, bank_name, swift_code, bank_account_number, account_holder_name, bank_statement)
            VALUES 
                (:provider_id, :bank_name, :swift, :acc, :holder, :statement)
        """)
        db.session.execute(sql, {
            "provider_id": provider_id,
            "bank_name": bank_name,
            "swift": swift,
            "acc": acc,
            "holder": holder,
            "statement": statement
        })
        db.session.commit()
