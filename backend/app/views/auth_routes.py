from flask import Blueprint, request, jsonify
from app.controllers.auth_controller import AuthController

auth_bp = Blueprint('auth_bp', __name__)

# ---------------- Signup ----------------
@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    result, status = AuthController.signup(data)
    return jsonify(result), status

# ---------------- Activate Account ----------------
@auth_bp.route('/activate', methods=['POST'])
def activate_account():
    data = request.get_json()
    token = data.get('token')
    if not token:
        return jsonify({"error": "Token required"}), 400

    result, status = AuthController.activate_account(token)
    return jsonify(result), status


# ---------------- Login ----------------
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    result, status = AuthController.login(email, password)
    return jsonify(result), status


# ---------------- Verify OTP ----------------
@auth_bp.route('/verify_otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    email = data.get('email')
    otp = data.get('otp')

    if not email or not otp:
        return jsonify({"error": "Email and OTP required"}), 400

    result, status = AuthController.verify_otp(email, otp)
    return jsonify(result), status


# ---------------- Resend OTP ----------------
@auth_bp.route('/resend_otp', methods=['POST'])
def resend_otp():
    data = request.get_json()
    email = data.get('email')
    if not email:
        return jsonify({"error": "Email required"}), 400

    result, status = AuthController.resend_otp(email)
    return jsonify(result), status


# ---------------- Forgot Password OTP ----------------
@auth_bp.route('/forgot_send_otp', methods=['POST'])
def forgot_send_otp():
    data = request.get_json()
    email = data.get('email')
    if not email:
        return jsonify({"error": "Email required"}), 400

    result, status = AuthController.forgot_send_otp(email)
    return jsonify(result), status


# ---------------- Verify Reset OTP ----------------
@auth_bp.route('/verify_reset_otp', methods=['POST'])
def verify_reset_otp():
    data = request.get_json()
    email = data.get('email')
    otp = data.get('otp')

    if not email or not otp:
        return jsonify({"error": "Email and OTP required"}), 400

    result, status = AuthController.verify_reset_otp(email, otp)
    return jsonify(result), status


# ---------------- Reset Password ----------------
@auth_bp.route('/reset_password', methods=['POST'])
def reset_password():
    data = request.get_json()
    email = data.get('email')
    token = data.get('reset_token')
    password = data.get('password')

    if not all([email, token, password]):
        return jsonify({"error": "Email, token, and password required"}), 400

    result, status = AuthController.reset_password(email, token, password)
    return jsonify(result), status
