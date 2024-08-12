"""
This module sets up and runs the LEGO Scanner Flask application.

It configures the application, registers blueprints, and loads the master lookup data.
"""

from flask import Flask
from config import Config
from routes.upload import upload_bp
from routes.label import label_bp
from routes.main import main_bp
from routes.storage import storage_bp
from routes.manual_entry import manual_entry_bp
from routes.part_lookup import part_lookup_bp
from services.lookup_service import load_master_lookup

# Initialize the Flask application
app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Set your secret key here
app.config.from_object(Config)  # Load the configuration

with app.app_context():
    # Code here can safely use current_app, g, and other context-specific functions
    master_lookup = load_master_lookup()

# Register blueprints
app.register_blueprint(upload_bp)
app.register_blueprint(label_bp)
app.register_blueprint(main_bp)
app.register_blueprint(storage_bp)
app.register_blueprint(manual_entry_bp)
app.register_blueprint(part_lookup_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)