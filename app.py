from flask import Flask
from flask_session import Session
from config import Config
from routes import register_blueprints
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize Flask-Session
    Session(app)
    
    # Register all blueprints
    register_blueprints(app)
    
    @app.after_request
    def after_request(response):
        """Ensure responses aren't cached"""
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
