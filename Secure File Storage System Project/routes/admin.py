from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from config import db

admin = Blueprint('admin', __name__)

@admin.route('/dashboard', methods=['GET'])
@jwt_required()
def admin_dashboard():
    """Displays key system metrics for admins only"""
    user = get_jwt_identity()

    if user['role'] != 'admin':
        return jsonify({"error": "Access denied"}), 403

    with db.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) AS total_users FROM users")
        total_users = cursor.fetchone()['total_users']

        cursor.execute("SELECT COUNT(*) AS total_files FROM files")
        total_files = cursor.fetchone()['total_files']

        cursor.execute("SELECT COUNT(DISTINCT user_id) AS active_users FROM access_logs WHERE timestamp >= NOW() - INTERVAL 7 DAY")
        active_users = cursor.fetchone()['active_users']

        cursor.execute("SELECT SUM(storage_used) AS total_storage FROM users")
        total_storage = cursor.fetchone()['total_storage']

        cursor.execute("SELECT * FROM access_logs ORDER BY timestamp DESC LIMIT 10")
        recent_logs = cursor.fetchall()

    return jsonify({
        "total_users": total_users,
        "total_files": total_files,
        "active_users": active_users,
        "total_storage": total_storage,
        "recent_logs": recent_logs
    })
