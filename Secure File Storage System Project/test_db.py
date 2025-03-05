from config import db

try:
    with db.cursor() as cursor:
        cursor.execute("SELECT DATABASE();")
        result = cursor.fetchone()
        print("? Connected to database:", result['DATABASE()'])
except Exception as e:
    print("? Connection failed:", str(e))
