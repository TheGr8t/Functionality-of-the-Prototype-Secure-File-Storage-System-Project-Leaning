from flask import Blueprint, request, jsonify, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from utils.db import get_db_connection
from utils.logging import log_activity

# Create Blueprint for authentication
auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['POST'])
def register():
    """Registers a new user with hashed password and role"""
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'user')  # Default role is 'user'

    if not username or not email or not password:
        return jsonify({"error": "All fields are required"}), 400

    hashed_password = generate_password_hash(password)
    db_conn = get_db_connection()

    try:
        with db_conn.cursor() as cursor:
            # Check if user already exists
            cursor.execute("SELECT id FROM users WHERE email = %s OR username = %s", (email, username))
            if cursor.fetchone():
                return jsonify({"error": "User already exists"}), 409

            # Insert new user into database
            sql = "INSERT INTO users (username, email, password_hash, role) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (username, email, hashed_password, role))
            db_conn.commit()

        return jsonify({"message": "User registered successfully!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db_conn.close()

@auth.route('/login', methods=['POST'])
def login():
    """Logs in a user and returns a JWT token"""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    db_conn = get_db_connection()
    try:
        with db_conn.cursor() as cursor:
            sql = "SELECT id, username, email, password_hash, role FROM users WHERE email = %s"
            cursor.execute(sql, (email,))
            user = cursor.fetchone()

            if user and check_password_hash(user["password_hash"], password):
                token = create_access_token(identity={"id": user["id"], "role": user["role"]})
                log_activity(user["id"], "User logged in")
                return jsonify({"access_token": token}), 200
            else:
                return jsonify({"error": "Invalid email or password"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db_conn.close()

@auth.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    """Allows only admins to view all users"""
    jwt_data = get_jwt()
    user_role = jwt_data.get("role")

    if user_role != 'admin':
        return jsonify({"error": "Access denied"}), 403

    db_conn = get_db_connection()
    try:
        with db_conn.cursor() as cursor:
            cursor.execute("SELECT id, username, email, role FROM users")
            users = cursor.fetchall()
        return jsonify(users), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db_conn.close()

@auth.route('/login/google')
def google_login():
    """Redirects user to Google OAuth login"""
    return google.authorize_redirect(url_for('auth.google_authorize', _external=True))

@auth.route('/authorize')
def google_authorize():
    """Handles Google OAuth callback and logs in the user"""
    try:
        token = google.authorize_access_token()
        user_info = google.get('userinfo').json()

        db_conn = get_db_connection()
        with db_conn.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE email = %s", (user_info['email'],))
            user = cursor.fetchone()

            if not user:
                sql = "INSERT INTO users (username, email, role) VALUES (%s, %s, 'user')"
                cursor.execute(sql, (user_info['name'], user_info['email']))
                db_conn.commit()
                user_id = cursor.lastrowid
            else:
                user_id = user['id']

        access_token = create_access_token(identity=str(user_id))
        session['jwt_token'] = access_token
        log_activity(user_id, "User logged in via Google OAuth")

        return redirect("http://localhost:3000/dashboard")
    except Exception as e:
        return jsonify({"error": str(e)}), 500
