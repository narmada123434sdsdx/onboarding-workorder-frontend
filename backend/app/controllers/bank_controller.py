from app.models.bank_model import BankModel
import os
from werkzeug.utils import secure_filename
from app.utils.encrypt_utils import encrypt_value
from app.utils.email_utils import send_email
from app.config import Config

class BankController:
    @staticmethod
    def update_bank(email, bank_name, holder_name, account_number, swift, bank_statement):
        provider = BankModel.get_provider_id(email)
        if not provider:
            return {"error": "Provider not found"}, 404

        pid = provider['provider_id']
        swift_enc = encrypt_value(swift)
        acc_enc = encrypt_value(account_number)
        holder_enc = encrypt_value(holder_name)

        # filename = None
        # if bank_statement:
        #     filename = secure_filename(bank_statement.filename)
        #     save_path = os.path.join(Config.UPLOAD_FOLDER, filename)

        #     # Create folder if not exists
        #     os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

        existing = BankModel.get_bank_details(pid)
        if existing:
            BankModel.update_bank(pid, bank_name, swift_enc, acc_enc, holder_name, bank_statement)
        else:
            BankModel.insert_bank(pid, bank_name, swift_enc, acc_enc, holder_name, bank_statement)

        send_email(email, "Bank Details Updated", "Your bank details were successfully updated.")
        return {"message": "Bank details updated"}, 200
