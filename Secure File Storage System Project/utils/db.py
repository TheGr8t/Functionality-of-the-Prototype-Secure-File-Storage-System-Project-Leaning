import pymysql
from flask import current_app

# Function to establish and return a database connection
def get_db_connection():
    """Returns a database connection."""
    try:
        # Check if the connection is still alive, and reconnect if necessary
        if not hasattr(current_app, 'db') or current_app.db.open is False:
            current_app.db = pymysql.connect(
                host="localhost",                 # Localhost for local MySQL server
                user="root",                      # MySQL root user
                password="1234567",               # Your MySQL root password
                database="secure_file_storage",   # Your local database name
                port=3306,                        # MySQL default port
                cursorclass=pymysql.cursors.DictCursor  # Returns rows as dictionaries
            )
    except pymysql.MySQLError as e:
        # Log the error or handle it as needed
        print(f"❌ Database connection failed: {e}")
        raise

    return current_app.db

# Function to execute a query and fetch results
def query_db(query, args=(), one=False):
    """Executes a query on the database and returns results."""
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute(query, args)
    rv = cursor.fetchall()
    cursor.close()
    return (rv[0] if rv else None) if one else rv

# Function to commit a change to the database (e.g., insert, update)
def commit_db(query, args=()):
    """Executes a query to modify the database (INSERT, UPDATE, DELETE)."""
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute(query, args)
    db.commit()
    cursor.close()

# Optionally, close the connection manually if needed (usually not required in Flask)
def close_db():
    """Closes the current database connection."""
    db = getattr(current_app, 'db', None)
    if db is not None:
        db.close()
