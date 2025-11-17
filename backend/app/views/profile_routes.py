from flask import Blueprint, request, jsonify
from app.controllers.profile_controller import ProfileController
from app.utils.encrypt_utils import cipher

profile_bp = Blueprint('profile_bp', __name__)

# ---------------- Get Profile ----------------
@profile_bp.route('/profile', methods=['POST'])
def get_profile():
    data = request.get_json()
    email = data.get('email')
    if not email:
        return jsonify({"error": "Email required"}), 400

    result, status = ProfileController.get_profile(email)
    return jsonify(result), status


# ---------------- Update Profile ----------------
@profile_bp.route('/update_profile', methods=['POST'])
def update_profile():
    try:
        form = request.form
        email = form.get('email')
        if not email:
            return jsonify({"error": "Email required"}), 400

        result, status = ProfileController.update_profile(form, request.files)
        return jsonify(result), status
    except Exception as e:
        return jsonify({"error": str(e)}), 500
