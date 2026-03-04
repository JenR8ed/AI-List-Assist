from flask import Blueprint, render_template, send_from_directory, current_app

ui_bp = Blueprint('ui', __name__)

@ui_bp.route('/')
def index():
    """Main dashboard page."""
    return render_template('dashboard.html')

@ui_bp.route('/simple')
def simple_interface():
    """Simple upload interface."""
    return render_template('index.html')

@ui_bp.route('/uploads/<filename>')
def download_file(filename):
    """Serve uploaded images."""
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
