from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from dotenv import load_dotenv
import os
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import json

# Import our modules
from python.models import MockSnowflake, User
from python.utils import calculate_goal_progress, check_promotions
from python.emi import calculate_emi_plan

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='/app/python/templates')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-dev-key')

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
        
        # Get mock car data
        mock_snowflake = MockSnowflake()
        df = mock_snowflake.query_cars(
            is_new=goal_data.get('is_new', True),
            model=goal_data.get('model', ''),
            year=goal_data.get('year', 2025),
            max_mileage=goal_data.get('max_mileage', 50000)
        )
        
        if df.empty:
            logger.warning("No matching cars found")
            return jsonify({'error': 'No matching cars found'}), 404
            
        # Get car price from database
        car_price = float(df.iloc[0]['price'])
        goal_data['car_price'] = car_price
        
        # Use EMI calculation when financing is selected
        if goal_data.get('payment_method') == 'financing':
            result = calculate_emi_plan(goal_data)
        else:
            # Use simple goal progress for cash payment
            result = calculate_goal_progress(goal_data)
        
        # Check for promotions
        promotion = check_promotions(goal_data.get('model', ''))
        
        # Save data
        user = User()
        user.save_goal(current_user.id, goal_data)
        
        # Convert time_chart DataFrame to list of dicts for JSON
        time_chart_data = json.loads(result['time_chart'].to_json(orient='records'))
        
        logger.debug(f"Returning result")
        return jsonify({
            'time_chart': time_chart_data,
            'estimated_date': result['estimated_date'],
            'down_payment': result['down_payment'],
            'car_price': result['car_price'],
            'promotion': promotion
        })
        
    except Exception as e:
        logger.error(f"Error in submit_goal: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

# Scheduler job to check promotions
def check_promotion_job():
    logger.debug("Checking promotions for all users")
    # We could implement real notification logic here

scheduler.add_job(check_promotion_job, 'interval', minutes=60)

if __name__ == '__main__':
    # Use environment variables for production settings
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=debug_mode)