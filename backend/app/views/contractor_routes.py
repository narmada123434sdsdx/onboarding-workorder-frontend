from flask import Blueprint, request, jsonify
from app.controllers.contractor_controller import ContractorController

contractor_bp = Blueprint('contractor_bp', __name__)

@contractor_bp.route('/contractor_signup', methods=['POST'])
def signup():
    data = request.get_json()
    result, status = ContractorController.signup(data)
    return jsonify(result), status

@contractor_bp.route('/contractor_activate', methods=['POST'])
def activate():
    token = request.get_json().get('token')
    result, status = ContractorController.activate(token)
    return jsonify(result), status

@contractor_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    result, status = ContractorController.login(data)
    return jsonify(result), status

@contractor_bp.route('/verify_otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    result, status = ContractorController.verify_otp(data)
    return jsonify(result), status

@contractor_bp.route('/resend_otp', methods=['POST'])
def resend_otp():
    data = request.get_json()
    result, status = ContractorController.resend_otp(data)
    return jsonify(result), status

@contractor_bp.route('/company_profile', methods=['POST'])
def profile():
    data = request.get_json()
    result, status = ContractorController.get_profile(data)
    return jsonify(result), status

@contractor_bp.route('/update_company_profile', methods=['POST'])
def update_company_profile():
    result, status = ContractorController.update_company_profile(request.form, request.files)
    return jsonify(result), status

@contractor_bp.route('/update_company_bank', methods=['POST'])
def update_company_bank():
    result, status = ContractorController.update_company_bank(request.form, request.files)
    return jsonify(result), status

# ---------- Notifications ----------
@contractor_bp.route('/contractor_notifications', methods=['GET'])
def get_notifications():
    email = request.args.get('email')
    result, status = ContractorController.get_notifications(email)
    return jsonify(result), status

@contractor_bp.route('/contractor_unread_count', methods=['GET'])
def unread_count():
    email = request.args.get('email')
    result, status = ContractorController.unread_count(email)
    return jsonify(result), status

@contractor_bp.route('/contractor_mark_read', methods=['POST'])
def mark_read():
    data = request.get_json()
    result, status = ContractorController.mark_as_read(data)
    return jsonify(result), status
