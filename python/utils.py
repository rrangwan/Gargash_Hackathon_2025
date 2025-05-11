import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from python.models import MockSnowflake
import logging

logger = logging.getLogger(__name__)

def calculate_goal_progress(goal_data):
    try:
        car_price = goal_data.get('car_price', 100000)
        payment_method = goal_data.get('payment_method', 'cash')
        
        if payment_method == 'financing':
            # Mock data for financing
            down_payment_required = 50000  # Mock Down Payment Required
            monthly_saving = 10000         # Mock Monthly Savings
        else:
            # Use form inputs for cash
            down_payment_required = goal_data.get('down_payment', 20000)
            monthly_saving = goal_data.get('monthly_saving', 1000)
        
        # Calculate months needed to reach down payment
        if monthly_saving <= 0:
            logger.error("Monthly saving must be positive")
            raise ValueError("Monthly saving must be positive")
        
        months_needed = down_payment_required / monthly_saving
        months_needed = int(months_needed) + 1  # Round up and add 1 month
        estimated_date = datetime.now() + timedelta(days=months_needed * 30)
        
        # Time chart data
        months = np.arange(0, months_needed + 1)
        savings = months * monthly_saving
        df = pd.DataFrame({'Month': months, 'Savings': savings})
        
        logger.debug(f"Calculated progress: months_needed={months_needed}, down_payment={down_payment_required}")
        return {
            'time_chart': df,
            'estimated_date': estimated_date.strftime('%Y-%m-%d'),
            'down_payment': down_payment_required,
            'car_price': car_price
        }
    except Exception as e:
        logger.error(f"Error in calculate_goal_progress: {str(e)}", exc_info=True)
        raise

def check_promotions(car_model):
    try:
        mock_snowflake = MockSnowflake()
        df = mock_snowflake.query_cars(True, car_model, 2025, 0)
        return any(df['promotion']) if not df.empty else False
    except Exception as e:
        logger.error(f"Error in check_promotions: {str(e)}")
        return False