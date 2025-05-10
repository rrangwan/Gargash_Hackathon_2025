from flask import Flask, render_template
from flask_login import LoginManager, UserMixin
import snowflake.connector
import os
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
import bcrypt

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default-dev-key')

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.start()

# Sample user class
class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# Snowflake connection function
def connect_to_snowflake():
    try:
        conn = snowflake.connector.connect(
            user=os.getenv('SNOWFLAKE_USER'),
            password=os.getenv('SNOWFLAKE_PASSWORD'),
            account=os.getenv('SNOWFLAKE_ACCOUNT'),
            warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
            database=os.getenv('SNOWFLAKE_DATABASE'),
            schema=os.getenv('SNOWFLAKE_SCHEMA')
        )
        return conn
    except Exception as e:
        print(f"Error connecting to Snowflake: {e}")
        return None

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)