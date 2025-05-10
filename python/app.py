from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from dotenv import load_dotenv
import os
from apscheduler.schedulers.background import BackgroundScheduler
import bcrypt
from python.models import MockSnowflake, User
from python.utils import calculate_goal_progress, check_promotions

# Load environment variables
load_dotenv('/app/config/.env')

app = Flask(__name__)
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

# Routes
@app.route('/')
@login_required
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User()
        if user.authenticate(username, password):
            login_user(FlaskUser(username))
            return redirect(url_for('home'))
        return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/submit_goal', methods=['POST'])
@login_required
def submit_goal():
    goal_data = request.json
    mock_snowflake = MockSnowflake()

    # Query car data
    df = mock_snowflake.query_cars(
        is_new=goal_data['is_new'],
        model=goal_data['model'],
        year=goal_data['year'],
        max_mileage=goal_data['max_mileage']
    )

    if df.empty:
        return jsonify({'error': 'No matching cars found'}), 404

    car_price = df.iloc[0]['price']
    goal_data['car_price'] = car_price

    # Calculate progress
    result = calculate_goal_progress(goal_data)

    # Check promotions
    promotion = check_promotions(goal_data['model'])

    # Save data
    user = User()
    user.save_goal(current_user.id, goal_data)

    return jsonify({
        'time_chart': result['time_chart'].to_dict(orient='records'),
        'estimated_date': result['estimated_date'],
        'down_payment': result['down_payment'],
        'car_price': result['car_price'],
        'promotion': promotion
    })

# Scheduler job to check promotions (mocked)
def check_promotion_job():
    # Mock: Check promotions for all users
    print("Mock: Checking promotions for all users")
    # Real implementation would query Snowflake and send notifications
    # conn = connect_to_snowflake()
    # if conn:
    #     cursor = conn.cursor()
    #     cursor.execute("SELECT user_id, goal_data FROM user_goals")
    #     for user_id, goal_data in cursor:
    #         if check_promotions(goal_data['model']):
    #             print(f"Promotion available for {user_id}")
    #     cursor.close()
    #     conn.close()

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
        print(f"Error connecting to Snowflake: {e}")
        return None

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)