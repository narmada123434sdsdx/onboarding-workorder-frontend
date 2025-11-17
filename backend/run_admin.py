from app import create_app
from app.views.admin_routes import admin_bp

app = create_app(include_admin=True)
# app.register_blueprint(admin_bp, url_prefix="/api/admin")

if __name__ == "__main__":
    """app.run(port=5001, debug=True)"""
app.run(host="0.0.0.0", port=5000, debug=True)    
