from flask import Flask, send_from_directory
from flask_cors import CORS
from .models.database import db
from app.config import Config

def create_app(include_admin=False):
    # Initialize Flask app
    app = Flask(__name__)
    app.config.from_object(Config)

    @app.route('/backend/uploads/<path:filename>')
    def uploaded_files(filename):
        return send_from_directory(Config.UPLOAD_FOLDER, filename)

    # Enable CORS for frontend (e.g., React on Vite)
    CORS(app,
     resources={r"/api/*": {"origins": Config.ALLOWED_ORIGINS}},
     supports_credentials=True)


        # Initialize database
    db.init_app(app)

    # ---------------- Register Blueprints ----------------
    # Import all Blueprints from the views package

    from app.views.auth_routes import auth_bp
    from app.views.profile_routes import profile_bp
    from app.views.bank_routes import bank_bp
    from app.views.file_routes import file_bp
    from app.views.notification_routes import notification_bp
    from app.views.location_routes import location_bp
    from app.views.contractor_routes import contractor_bp

    from .controllers.workorder_controller import workorder_bp
    from .controllers.testdb_controller import testdb_bp
    from .views.workorder_area_view import workorder_area_view
    from .views.workorder_type_view import workorder_type_view
    from app.controllers.workorder_mapping_controller import workorder_mapping_bp
    from .routes.workorder_mail_bp import workorder_mail_bp
    from .views.workorder_mail_view import workorder_mail_bp


    # ---------------- Register Each Blueprint ----------------
    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(profile_bp, url_prefix="/api")
    app.register_blueprint(bank_bp, url_prefix="/api")
    app.register_blueprint(file_bp, url_prefix="/api")
    app.register_blueprint(notification_bp, url_prefix="/api")
    app.register_blueprint(location_bp, url_prefix="/api")
    app.register_blueprint(contractor_bp, url_prefix="/api/contractor")

    app.register_blueprint(workorder_bp, url_prefix="/api/workorders")
    app.register_blueprint(testdb_bp, url_prefix="/api/testdb")
    app.register_blueprint(workorder_area_view, url_prefix="/api")
    app.register_blueprint(workorder_type_view, url_prefix="/api/workorder-type")
    app.register_blueprint(workorder_mapping_bp, url_prefix="/api/mapping")
        # ✅ Mail route blueprint — correct prefix
    app.register_blueprint(workorder_mail_bp, url_prefix="/api/workorders")
    
    # Optionally include admin blueprint (for run_admin only)
    if include_admin:
        from app.views.admin_routes import admin_bp
        app.register_blueprint(admin_bp, url_prefix="/api/admin")
    # --------------------------------------------------------
    # You can add more blueprints later, like admin or reports:
    # from app.views.admin_routes import admin_bp
    # app.register_blueprint(admin_bp, url_prefix="/api/admin")
    # --------------------------------------------------------

    return app
