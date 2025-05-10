from flask import Flask, render_template, jsonify, request, redirect, url_for, after_this_request
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from dotenv import load_dotenv
import os
from apscheduler.schedulers.background import BackgroundScheduler
import bcrypt
import logging
import snowflake.connector 
from python.models import MockSnowflake, User
from python.utils import calculate_goal_progress, check_promotions

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv('.env')  # Fixed path to .env file

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-dev-key')

@app.after_request
def add_security_headers(response):
    csp_policy = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.plot.ly https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "img-src 'self' data: blob:; "
        "connect-src 'self'; "
        "frame-src 'self'; "
        "font-src 'self' https://fonts.gstatic.com data:; "
        "object-src 'none'; "
        "base-uri 'self';"
    )
    response.headers['Content-Security-Policy'] = csp_policy
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response


# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize scheduler for promotion checks
scheduler = BackgroundScheduler()
scheduler.start()

# User class for Flask-Login
class FlaskUser(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return FlaskUser(user_id)

# Routes
@app.route('/')
@login_required
def home():
    logger.debug("Rendering home page")
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        logger.debug("User already authenticated, redirecting to home")
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User()
        if user.authenticate(username, password):
            login_user(FlaskUser(username))
            logger.debug(f"User {username} logged in")
            return redirect(url_for('home'))
        logger.warning("Invalid login attempt")
        return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logger.debug(f"User {current_user.id} logged out")
    logout_user()
    return redirect(url_for('login'))

@app.route('/submit_goal', methods=['POST'])
@login_required
def submit_goal():
    try:
        goal_data = request.json
        logger.debug(f"Received goal data: {goal_data}")
        mock_snowflake = MockSnowflake()

        # Query car data (Python mock)
        df = mock_snowflake.query_cars(
            is_new=goal_data.get('is_new', True),
            model=goal_data.get('model', ''),
            year=goal_data.get('year', 2025),
            max_mileage=goal_data.get('max_mileage', 50000)
        )

        if df.empty:
            logger.warning("No matching cars found")
            return jsonify({'error': 'No matching cars found'}), 404

        car_price = df.iloc[0]['price']
        goal_data['car_price'] = car_price

        # Calculate progress
        result = calculate_goal_progress(goal_data)

        # Check promotions
        promotion = check_promotions(goal_data.get('model', ''))

        # Save data
        user = User()
        user.save_goal(current_user.id, goal_data)

        logger.debug(f"Returning result: {result}")
        return jsonify({
            'time_chart': result['time_chart'].to_dict(orient='records'),
            'estimated_date': result['estimated_date'],
            'down_payment': result['down_payment'],
            'car_price': result['car_price'],
            'promotion': promotion
        })
    except Exception as e:
        logger.error(f"Error in submit_goal: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

# Scheduler job to check promotions (mocked)
def check_promotion_job():
    logger.debug("Checking promotions for all users")
    print("Mock: Checking promotions for all users")

scheduler.add_job(check_promotion_job, 'interval', minutes=60)

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
        logger.error(f"Error connecting to Snowflake: {str(e)}")
        return None

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)