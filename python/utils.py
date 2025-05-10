import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from python.models import MockSnowflake

def calculate_goal_progress(goal_data):
    # Mock financial projection
    car_price = goal_data.get('car_price', 100000)
    down_payment = goal_data.get('down_payment', 20000)
    monthly_saving = goal_data.get('monthly_saving', 1000)
    
    months_needed = (car_price - down_payment) / monthly_saving
    estimated_date = datetime.now() + timedelta(days=months_needed * 30)
    
    # Time chart data
    months = np.arange(0, int(months_needed) + 1)
    savings = down_payment + months * monthly_saving
    df = pd.DataFrame({'Month': months, 'Savings': savings})
    
    return {
        'time_chart': df,
        'estimated_date': estimated_date.strftime('%Y-%m-%d'),
        'down_payment': down_payment,
        'car_price': car_price
    }

def check_promotions(car_model):
    # Mock promotion check
    mock_snowflake = MockSnowflake()
    df = mock_snowflake.query_cars(True, car_model, 2025, 0)
    return any(df['promotion']) if not df.empty else False