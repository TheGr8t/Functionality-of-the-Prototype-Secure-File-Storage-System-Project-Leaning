from config import db

def log_activity(user_id, action, file_id=None):
    """Logs user activities in the database"""
    with db.cursor() as cursor:
        sql = "INSERT INTO access_logs (user_id, action, file_id) VALUES (%s, %s, %s)"
        cursor.execute(sql, (user_id, action, file_id if file_id else None))
        db.commit()
