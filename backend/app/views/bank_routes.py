from flask import Blueprint, request, jsonify
from app.controllers.bank_controller import BankController

bank_bp = Blueprint('bank_bp', __name__)

@bank_bp.route('/update_bank', methods=['POST'])
def update_bank():
    try:
        email = request.form.get('email')
        bank_name = request.form.get('bank_name')
        holder_name = request.form.get('holder_name')
        account_number = request.form.get('account_number')
        swift = request.form.get('swift', '').upper()
        bank_statement = request.files.get('bank_statement').read() if 'bank_statement' in request.files else None

        # Validation
        if not all([email, bank_name, holder_name, account_number, swift, bank_statement]):
            return jsonify({"error": "All bank details and statement are required"}), 400

        result, status = BankController.update_bank(email, bank_name, holder_name, account_number, swift, bank_statement)
        return jsonify(result), status

    except Exception as e:
        return jsonify({"error": str(e)}), 500
