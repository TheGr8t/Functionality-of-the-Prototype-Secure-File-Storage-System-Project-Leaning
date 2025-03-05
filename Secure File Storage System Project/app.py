import os
import uuid
import logging
from flask import Flask, request, jsonify, send_file, render_template, redirect, url_for
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from cryptography.fernet import Fernet
from flask_cors import CORS
from dotenv import load_dotenv
from routes.auth import auth  # Authentication routes
from routes.files import files  # File management routes

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, template_folder="templates")  # Enable template rendering
CORS(app)  # Allow cross-origin requests (important for frontend integration)
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'supersecretkey')  # Secure key from .env

jwt = JWTManager(app)

# Logger Setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# File Upload Configurations
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'png', 'jpg', 'txt'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
UPLOAD_FOLDER = "uploads"

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Generate AES-256 Key (Store this securely in .env or a secure vault)
encryption_key = os.getenv('ENCRYPTION_KEY', Fernet.generate_key().decode())  
cipher = Fernet(encryption_key.encode())

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Check if file type is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Encrypt file data
def encrypt_file(file_data):
    return cipher.encrypt(file_data)

# Decrypt file data
def decrypt_file(file_data):
    return cipher.decrypt(file_data)

# ✅ Home Route (Web Interface)
@app.route('/')
def home():
    return render_template('index.html')

# ✅ Login Page Route
@app.route('/login')
def login_page():
    return render_template('login.html')

# ✅ Dashboard Page Route (After Login)
@app.route('/dashboard')
@jwt_required()  # Requires user to be logged in
def dashboard():
    user_id = get_jwt_identity()["id"]
    return render_template('dashboard.html', user_id=user_id)

# ✅ Upload File Route (API)
@app.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    user_id = get_jwt_identity()["id"]  # Get user ID from JWT

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        file.seek(0, os.SEEK_END)  # Move pointer to end
        file_size = file.tell()
        file.seek(0)

        if file_size > MAX_FILE_SIZE:
            return jsonify({"error": "File size exceeds 10MB limit"}), 400

        filename = secure_filename(file.filename)
        user_folder = os.path.join(UPLOAD_FOLDER, str(user_id))

        if not os.path.exists(user_folder):
            os.makedirs(user_folder)

        file_path = os.path.join(user_folder, filename)

        try:
            encrypted_data = encrypt_file(file.read())

            with open(file_path, "wb") as encrypted_file:
                encrypted_file.write(encrypted_data)

            logging.info(f"File uploaded successfully: {filename} by user {user_id}")

            return jsonify({"message": "File uploaded successfully", "filename": filename}), 200
        except Exception as e:
            logging.error(f"Error during file upload: {str(e)}")
            return jsonify({"error": "File upload failed"}), 500

    return jsonify({"error": "Invalid file type"}), 400

# ✅ Download File Route (API)
@app.route('/download/<filename>', methods=['GET'])
@jwt_required()
def download_file(filename):
    user_id = get_jwt_identity()["id"]
    file_path = os.path.join(UPLOAD_FOLDER, str(user_id), filename)

    if not os.path.exists(file_path):
        logging.warning(f"File not found for user {user_id}: {filename}")
        return jsonify({"error": "File not found"}), 404

    try:
        with open(file_path, "rb") as encrypted_file:
            encrypted_data = encrypted_file.read()
            decrypted_data = decrypt_file(encrypted_data)

        temp_filename = f"decrypted_{uuid.uuid4().hex}_{filename}"
        temp_path = os.path.join(UPLOAD_FOLDER, temp_filename)

        with open(temp_path, "wb") as temp_file:
            temp_file.write(decrypted_data)

        logging.info(f"File downloaded successfully: {filename} by user {user_id}")

        response = send_file(temp_path, as_attachment=True)

        os.remove(temp_path)  # Delete temporary file after serving

        return response

    except Exception as e:
        logging.error(f"Error during file download: {str(e)}")
        return jsonify({"error": "File download failed"}), 500

# Register Routes
app.register_blueprint(auth, url_prefix='/api/auth')
app.register_blueprint(files, url_prefix='/api/files')

if __name__ == '__main__':
    app.run(debug=True)