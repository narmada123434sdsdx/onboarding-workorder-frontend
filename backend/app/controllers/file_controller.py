from io import BytesIO
from PIL import Image
import magic
from flask import send_file, jsonify
from sqlalchemy.sql import text
from app.models.database import db

class FileController:

    @staticmethod
    def get_image(email, file_type):
        try:
            # ---------- Determine SQL based on file_type ----------
            if file_type == "profile":
                sql = text("SELECT profile_pic AS file FROM providers_t WHERE email_id = :email")

            elif file_type == "certificate":
                sql = text("SELECT authorized_certificate AS file FROM providers_t WHERE email_id = :email")

            elif file_type == "bank_statement":
                sql = text("""
                    SELECT bank_statement AS file
                    FROM providers_bank_details_t
                    WHERE provider_id = (
                        SELECT provider_id FROM providers_t WHERE email_id = :email
                    )
                """)

            elif file_type == "contractor_certificate":
                sql = text("SELECT certificate_path AS file FROM company_details_t WHERE head_email = :email")

            elif file_type == "contractor_logo":
                sql = text("SELECT logo_path AS file FROM company_details_t WHERE head_email = :email")

            else:
                return jsonify({"error": "Invalid file type"}), 400

            # ---------- Execute SQL ----------
            row = db.session.execute(sql, {"email": email}).fetchone()

            if not row or not row._mapping["file"]:
                return jsonify({"error": "File not found"}), 404

            file_data = row._mapping["file"]

            # Convert memoryview → bytes
            if isinstance(file_data, memoryview):
                file_data = file_data.tobytes()

            # ---------- Detect MIME type ----------
            mime = magic.Magic(mime=True)
            mimetype = mime.from_buffer(file_data[:2048])

            # PDF handling
            if mimetype == "application/pdf":
                return send_file(BytesIO(file_data), mimetype="application/pdf", as_attachment=False)

            # Image detection using Pillow
            try:
                img = Image.open(BytesIO(file_data))
                mimetype = f"image/{img.format.lower()}"
            except Exception:
                return jsonify({"error": "Invalid or corrupted file format"}), 400

            return send_file(BytesIO(file_data), mimetype=mimetype, as_attachment=False)

        except Exception as err:
            print("File fetch error:", err)
            return jsonify({"error": str(err)}), 500
