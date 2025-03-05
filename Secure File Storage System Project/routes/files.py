import os
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
from flask_jwt_extended import jwt_required, get_jwt_identity
from config import get_db_connection  # Ensure we use the correct DB connection
from utils.logging import log_activity  # Import log function

files = Blueprint('files', __name__)

UPLOAD_FOLDER = 'D:/Secure File Storage System Project/uploads/'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'png', 'jpg', 'txt'}
ENCRYPTION_KEY = b'my_super_secret_key_1234'  # Must be 16, 24, or 32 bytes

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@files.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    """Handles secure file upload"""
    user_id = int(get_jwt_identity())  # Convert JWT string ID to integer

    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']

    if not file or file.filename == '':
        return jsonify({"error": "Invalid file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type"}), 400

    filename = secure_filename(file.filename)
    user_folder = os.path.join(UPLOAD_FOLDER, str(user_id))  # Ensure user_id is converted to string
    os.makedirs(user_folder, exist_ok=True)

    file_path = os.path.join(user_folder, filename)
    file.save(file_path)

    # Store file details in the database
    db = get_db_connection()
    with db.cursor() as cursor:
        sql = """INSERT INTO files (user_id, filename, encrypted_path, file_size, file_type) 
                 VALUES (%s, %s, %s, %s, %s)"""
        cursor.execute(sql, (user_id, filename, file_path, os.path.getsize(file_path), filename.split('.')[-1]))
        db.commit()

    log_activity(user_id, "Uploaded file")

    return jsonify({"message": "File uploaded successfully!"}), 201

@files.route('/download/<int:file_id>', methods=['GET'])
@jwt_required()
def download_file(file_id):
    """Allows users to download files they have access to"""
    user_id = int(get_jwt_identity())  # Convert JWT string ID to integer
    db = get_db_connection()

    with db.cursor() as cursor:
        cursor.execute("SELECT encrypted_path FROM files WHERE id = %s AND user_id = %s", (file_id, user_id))
        file = cursor.fetchone()

    if not file:
        return jsonify({"error": "Access denied or file not found"}), 403

    log_activity(user_id, f"Downloaded file {file_id}")  # Log download activity

    return send_file(file['encrypted_path'], as_attachment=True)