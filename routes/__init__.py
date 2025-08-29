from .auth import auth_bp
from .events import events_bp
from .staff import staff_bp
from .user import user_bp

def register_blueprints(app):
    """Register all blueprints with the Flask app"""
    app.register_blueprint(auth_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(user_bp)
    