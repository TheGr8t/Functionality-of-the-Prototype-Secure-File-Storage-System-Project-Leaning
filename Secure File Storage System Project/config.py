import pymysql
import stripe
from authlib.integrations.flask_client import OAuth

# Use Local MySQL Database
def get_db_connection():
    try:
        db.ping(reconnect=True)  # Reconnect if connection is lost
    except:
        db = pymysql.connect(
            host="localhost",     
            user="root",          
            password="1234567",      
            database="secure_file_storage",  
            port=3306,              
            cursorclass=pymysql.cursors.DictCursor
        )
    return db

# Initialize MySQL Connection
db = get_db_connection()

# Google OAuth Configuration
oauth = OAuth()
google = oauth.register(
    name='google',
    client_id='your_google_client_id',
    client_secret='your_google_client_secret',
    access_token_url='https://oauth2.googleapis.com/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    client_kwargs={'scope': 'openid email profile'}
)

# Stripe Payment Configuration
stripe.api_key = "your_stripe_secret_key"
