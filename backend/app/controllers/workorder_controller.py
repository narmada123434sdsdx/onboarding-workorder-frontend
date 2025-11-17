from flask import Blueprint, request, jsonify, current_app
from ..models.workorder import WorkOrder
from ..models.contractor import Contractor
from ..views.workorder_view import WorkOrderView
from datetime import datetime, timedelta
import base64
import json
import os
from werkzeug.utils import secure_filename

workorder_bp = Blueprint("workorder", __name__)
view = WorkOrderView()

# Allowed image extensions
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

# ------------------------------
# Upload Settings
# ------------------------------
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "jfif"}


os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    """Check allowed file extensions."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# def allowed_file(filename):
#     return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ------------------------------
# Create WorkOrder
# ------------------------------
@workorder_bp.route("/", methods=["POST"])
def create_workorder():
    print("===== DEBUG CREATE WORKORDER =====")
    print("Content-Type:", request.content_type)
    print("Form keys:", list(request.form.keys()))
    print("Files keys:", list(request.files.keys()))
    for key in request.files:
        print(f"Files for key {key}:", request.files.getlist(key))

    try:
        # 1️⃣ Check Content-Type
        if not request.content_type.startswith("multipart/form-data"):
            return jsonify({"error": "Content-Type must be multipart/form-data"}), 400

        data = request.form.to_dict()
        # ✅ Add CLIENT from form data
        data["CLIENT"] = request.form.get("CLIENT", "").strip()
        data["ticket_assignment_type"] = request.form.get("ticket_assignment_type", "").strip()


        images = request.files
        image_dict = {}

        # 2️⃣ Validate required fields
        required = ["WORKORDER", "WORKORDER_TYPE", "WORKORDER_AREA", "REQUESTED_TIME_CLOSING"]
        missing = [f for f in required if f not in data or not data[f]]
        if missing:
            return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

        # 3️⃣ Parse RATE JSON
        try:
            data["RATE"] = json.loads(data.get("RATE", "{}"))
        except json.JSONDecodeError:
            data["RATE"] = {"type_rates": {}, "total_rate": 0}

        # 4️⃣ Parse datetime
        try:
            data["REQUESTED_TIME_CLOSING"] = datetime.fromisoformat(data["REQUESTED_TIME_CLOSING"])
        except Exception:
            return jsonify({"error": "REQUESTED_TIME_CLOSING must be a valid ISO datetime"}), 400

        # 5️⃣ Handle images
        for key in images.keys():
            if key.startswith("images[") and key.endswith("][]"):
                type_name = key[len("images["):-len("][]")]
                files = request.files.getlist(key)

                image_dict[type_name] = []
                for file in files:
                    if file and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        unique_name = f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}_{filename}"
                        save_path = os.path.join(UPLOAD_FOLDER, unique_name)
                        file.save(save_path)
                        print(f"[DEBUG] Saved file: {save_path}")

                        # relative path for DB
                        rel_path = f"/uploads/{unique_name}"
                        image_dict[type_name].append(rel_path)
                    else:
                        print(f"[DEBUG] File skipped (extension not allowed): {file.filename}")

        data["image"] = image_dict

        # 6️⃣ Debug final data
        debug_data = data.copy()
        debug_data["REQUESTED_TIME_CLOSING"] = debug_data["REQUESTED_TIME_CLOSING"].isoformat()
        print("===== DEBUG DATA BEFORE DB =====")
        print(json.dumps(debug_data, indent=2))

        # 7️⃣ Save workorder in DB
        workorder, error = WorkOrder.create(data)
        if error:
            return jsonify({"error": error}), 400

        # 8️⃣ Serialize datetimes for JSON response
        def serialize_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return obj

        serialized_workorder = {k: serialize_datetime(v) for k, v in workorder.items()}
        serialized_workorder["image"] = workorder.get("image", {})
        serialized_workorder["closing_images"] = workorder.get("closing_images", [])

        return jsonify({
            "message": "Workorder created successfully",
            "workorder": serialized_workorder
        }), 201

    except Exception as e:
        print(f"[ERROR] Exception in create_workorder: {str(e)}")
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

@workorder_bp.route("/", methods=["GET"])
def get_all():
    workorders, error = WorkOrder.get_all()
    if error:
        return view.error(error, 400)
    return view.list(workorders, 200)


# @workorder_bp.route("/<int:id>", methods=["GET"])
# def get_one(id):
#     workorder = WorkOrder.get_by_id(id)
#     if not workorder:
#         return view.error("Work order not found", 404)
#     return view.success(workorder, 200)

@workorder_bp.route("/<id>", methods=["GET"])
def get_workorder(id):
    record = WorkOrder.get_by_id(id)

    if not record:
        return jsonify({"error": "Workorder not found"}), 404

    return jsonify(record.to_dict()), 200



@workorder_bp.route("/search", methods=["GET"])
def search_workorders():
    query = request.args.get("query", "").strip()
    if not query:
        return jsonify([]), 200

    print(f"[DEBUG] API called with query: {query}")

    workorders, error = WorkOrder.search_by_workorder_raw(query)
    if error:
        print(f"[ERROR] search API error: {error}")
        return jsonify({"error": error}), 500

    print(f"[DEBUG] API returning {len(workorders)} rows")
    return jsonify(workorders), 200

@workorder_bp.route("/<int:id>", methods=["PUT"])
def update(id):
    workorder = WorkOrder.get_by_id(id)
    if not workorder:
        return view.error("Work order not found", 404)

    data = {}

    # Handle multipart form-data (closing workorder with images)
    if request.content_type and request.content_type.startswith("multipart/form-data"):
        data["STATUS"] = request.form.get("STATUS")

        # ------------------------------
        # Handle multiple closing images
        # ------------------------------
        closing_files = request.files.getlist("closing_images[]")
        saved_closing_images = []

        for file in closing_files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_name = f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}_{filename}"
                save_path = os.path.join(UPLOAD_FOLDER, unique_name)
                file.save(save_path)

                print(f"[DEBUG] Saved closing image: {save_path}")
                rel_path = f"/uploads/{unique_name}"
                saved_closing_images.append(rel_path)
            else:
                print(f"[DEBUG] Skipped invalid closing file: {file.filename}")

        # Merge newly uploaded closing images with existing ones (if any)
        if saved_closing_images:
            existing = workorder.closing_images or []
            workorder.closing_images = existing + saved_closing_images

    else:
        # JSON payload fallback
        json_data = request.get_json()
        if not json_data:
            return view.error("No data provided", 400)
        data = json_data

    # Prevent closing parent if any child still open
    if data.get("STATUS") == "CLOSED":
        open_children = WorkOrder.query.filter(
            WorkOrder.parent_workorder == workorder.WORKORDER,
            WorkOrder.STATUS == "OPEN"
        ).all()
        if open_children:
            return view.error(
                "Cannot close parent workorder while child workorders are still open.",
                400,
            )

    # Validate RATE if exists
    if "RATE" in data and not isinstance(data["RATE"], dict):
        return view.error("RATE must be JSON format", 400)

    # Apply updates
    success, error = workorder.update(data)
    if error:
        return view.error(error, 400)

    # Final response includes closing image paths
    updated = workorder.to_dict()
    updated["closing_images"] = workorder.closing_images

    return view.success(updated, 200)



@workorder_bp.route("/<int:id>", methods=["DELETE"])
def delete(id):
    workorder = WorkOrder.get_by_id(id)
    if not workorder:
        return view.error("Work order not found", 404)

    success, error = workorder.delete()
    if error:
        return view.error(error, 400)
    return view.message("Work order deleted successfully", 200)


@workorder_bp.route("/workorder-types", methods=["GET"])
def get_workorder_types():
    types, error = WorkOrder.get_workorder_types()
    if error:
        return jsonify({"error": error}), 500
    return jsonify(types)





@workorder_bp.route("/generate", methods=["GET"])
def generate_workorder():
    try:
        workorder_type = request.args.get("workorder_type")
        if not workorder_type:
            return jsonify({"error": "workorder_type is required"}), 400

        workorder_id = WorkOrder.generate_workorder_id(workorder_type)
        return jsonify({"workorder": workorder_id}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    
@workorder_bp.route("/generates", methods=["GET"])
def generates_workorder():
    try:
        workorder_type = request.args.get("workorder_type")
        if not workorder_type:
            return jsonify({"error": "workorder_type is required"}), 400

        workorder_id = WorkOrder.generates_workorder_id(workorder_type)
        return jsonify({"workorder": workorder_id}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Contractor Routes


    
@workorder_bp.route("/childs/<string:parent_wo>", methods=["GET"])
def get_child_workorders(parent_wo):
    try:
        # Fetch all child workorders where parent_workorder = parent_wo
        childs = WorkOrder.query.filter(WorkOrder.parent_workorder == parent_wo).all()
        if not childs:
            return jsonify([]), 200
        return jsonify([c.to_dict() for c in childs]), 200
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500
    
    

# Contractor Routes

@workorder_bp.route("/contractors/by-area/<string:area>", methods=["GET"])
def get_contractors_by_area(area):
    try:
        contractors, error = Contractor.get_by_service_location(area)
        if error:
            return jsonify({"error": error}), 500
        if not contractors:
            return jsonify([]), 200
        contractors_list = [c.to_dict() for c in contractors]
        return jsonify(contractors_list), 200
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


@workorder_bp.route("/contractors", methods=["GET"])
def get_all_contractors():
    try:
        contractors, error = Contractor.get_all()
        if error:
            return jsonify({"error": error}), 500
        contractors_list = [c.to_dict() for c in contractors]
        return jsonify(contractors_list), 200
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


# ------------------------------
# New route: Filter WorkOrders
# ------------------------------



@workorder_bp.route("/filter", methods=["GET"])
def filter_workorders():
    """
    Filter workorders by status and optional date range
    Query params:
        - status: Pending, Accepted, Rejected, etc. (default: All)
        - from: YYYY-MM-DD
        - to: YYYY-MM-DD
    """
    try:
        status = request.args.get("status", "All")
        from_date = request.args.get("from")
        to_date = request.args.get("to")

        query = WorkOrder.query

        # Filter by status if not "All"
        if status.lower() != "all":
            query = query.filter(WorkOrder.STATUS == status)

        # Filter by date range if both dates provided
        if from_date and to_date:
            try:
                from_dt = datetime.strptime(from_date, "%Y-%m-%d")
                to_dt = datetime.strptime(to_date, "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1)
                query = query.filter(WorkOrder.CREATED_T.between(from_dt, to_dt))
            except ValueError:
                return jsonify({"error": "Invalid date format, use YYYY-MM-DD"}), 400

        workorders = query.all()
        results = [wo.to_dict() for wo in workorders]
        return jsonify(results), 200

    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500  




@workorder_bp.route("/standard-rates", methods=["GET"])
def get_standard_rates():
    try:
        data = WorkOrder.get_standard_rates()
        return jsonify(data), 200
    except Exception as e:
        print("[ERROR] get_standard_rates:", e)
        return jsonify({"error": str(e)}), 500