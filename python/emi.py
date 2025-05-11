import pandas as pd
import numpy as np
from datetime import datetime
import os
import snowflake.connector
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def connect_to_snowflake():
    """Create a connection to Snowflake using environment variables"""
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
        print(f"Error connecting to Snowflake: {str(e)}")
        return None

def get_depreciation_rate(manufacturer='mercedes-benz'):
    """Calculate the monthly depreciation rate for a specific car manufacturer"""
    try:
        conn = connect_to_snowflake()
        if not conn:
            # Default depreciation rate if connection fails
            return 0.5  # 0.5% monthly depreciation as default
            
        cursor = conn.cursor()
        query = "SELECT * FROM DriveArabia_All_uae_updated"
        cursor.execute(query)
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=[x[0] for x in cursor.description])
        
        # Clean and filter data
        df['MANUFACTURER'] = df['MANUFACTURER'].str.strip().str.lower()
        df = df[df['MANUFACTURER'] == manufacturer]
        df = df.dropna(subset=['APPROXCOST', 'MODELYEAR', 'OVERVIEW'])
        
        # Clean price data
        df['APPROXCOST'] = df['APPROXCOST'].str.replace(r'[^\d.]', '', regex=True)
        df = df[df['APPROXCOST'].str.strip() != '']
        df['APPROXCOST'] = df['APPROXCOST'].astype(float)
        
        # Calculate depreciation
        depreciations = []
        for model, group in df.groupby('OVERVIEW'):
            group = group.sort_values('MODELYEAR')
            if len(group) < 2:
                continue
                
            for i in range(1, len(group)):
                prev = group.iloc[i - 1]
                curr = group.iloc[i]
                year_diff = curr['MODELYEAR'] - prev['MODELYEAR']
                if year_diff <= 0:
                    continue
                    
                month_diff = year_diff * 12
                price_diff = prev['APPROXCOST'] - curr['APPROXCOST']
                if price_diff <= 0:
                    continue
                    
                monthly_depreciation = price_diff / month_diff
                monthly_pct = (monthly_depreciation / prev['APPROXCOST']) * 100
                depreciations.append(monthly_pct)
        
        # Return average monthly depreciation rate
        return np.mean(depreciations) if depreciations else 0.5
        
    except Exception as e:
        print(f"Error calculating depreciation: {str(e)}")
        return 0.5  # Default value on error
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def calculate_emi_plan(goal_data):
    """
    Calculate EMI plan based on user input
    
    Args:
        goal_data: Dictionary containing user inputs:
            - model: Car model
            - year: Model year
            - car_price: Car price
            - max_emi: Maximum EMI amount
            - down_payment: Down payment amount
            - max_term: Maximum financing term in months
            
    Returns:
        Dictionary with EMI plan details
    """
    try:
        # Get financial data
        conn = connect_to_snowflake()
        if conn:
            cursor = conn.cursor()
            query = "SELECT * FROM monthly_NET_TRANSACTIONS_CATEGORIZED"
            cursor.execute(query)
            rows = cursor.fetchall()
            df = pd.DataFrame(rows, columns=[x[0] for x in cursor.description])
            
            # Clean data
            df = df[df['AMOUNT'].notna()]
            
            # Calculate monthly net and expenses
            monthly_net = df.groupby(['YEAR', 'MONTH'])['AMOUNT'].sum().reset_index()
            monthly_net['Date'] = pd.to_datetime(monthly_net[['YEAR', 'MONTH']].assign(day=1))
            monthly_net = monthly_net.sort_values('Date')
            
            df_expenses = df[df['AMOUNT'] < 0]
            monthly_expenses = df_expenses.groupby(['YEAR', 'MONTH'])['AMOUNT'].sum().reset_index()
            avg_monthly_expense = -monthly_expenses['AMOUNT'].mean()
            avg_monthly_savings = monthly_net['AMOUNT'].mean()
            initial_savings = monthly_net['AMOUNT'].cumsum().iloc[-1]
        else:
            # Default values if connection fails
            avg_monthly_expense = 5000
            avg_monthly_savings = 3000
            initial_savings = 10000
    except Exception as e:
        print(f"Error getting financial data: {str(e)}")
        # Default values on error
        avg_monthly_expense = 5000
        avg_monthly_savings = 3000
        initial_savings = 10000
    finally:
        if 'conn' in locals() and conn:
            conn.close()
    
    # Car settings
    car_model = goal_data.get('model', 'Mercedes C200')
    base_price = goal_data.get('car_price', 100000)
    
    # Finance parameters
    emi = goal_data.get('max_emi', 5000)
    interest_rate = 0.10  # 10% annual interest rate
    monthly_depr_rate = get_depreciation_rate() / 100  # Convert % to decimal
    
    # Initialize calculation
    current_price = base_price
    current_savings = initial_savings
    months_to_purchase = 0
    buffer = 2 * avg_monthly_expense  # Safety buffer
    
    # Calculate months until purchase
    while True:
        # Add savings for the month
        current_savings += avg_monthly_savings
        months_to_purchase += 1
        
        # Depreciate price monthly
        current_price *= (1 - monthly_depr_rate)
        total_price_with_interest = current_price * (1 + interest_rate)
        down_payment = 0.2 * total_price_with_interest  # 20% down payment
        required_savings = down_payment + buffer
        
        if current_savings >= required_savings:
            break
    
    # Calculate payment plan after purchase
    current_savings -= down_payment
    loan = total_price_with_interest - down_payment
    months_after_purchase = 0
    
    while loan > 0:
        current_savings += avg_monthly_savings - emi
        loan -= emi
        months_after_purchase += 1
    
    # Create timeline data
    today = datetime.now()
    purchase_date = today + pd.DateOffset(months=months_to_purchase)
    payoff_date = purchase_date + pd.DateOffset(months=months_after_purchase)
    
    # Create time chart data
    time_chart = []
    for i in range(months_to_purchase + 1):
        date = today + pd.DateOffset(months=i)
        savings = initial_savings + (avg_monthly_savings * i)
        time_chart.append({
            'date': date.strftime('%Y-%m-%d'),
            'savings': savings
        })
    
    # Continue chart data for payment period
    initial_post_purchase = initial_savings + (avg_monthly_savings * months_to_purchase) - down_payment
    for i in range(1, months_after_purchase + 1):
        date = purchase_date + pd.DateOffset(months=i)
        savings = initial_post_purchase + (avg_monthly_savings - emi) * i
        time_chart.append({
            'date': date.strftime('%Y-%m-%d'),
            'savings': savings
        })
    
    return {
        'time_chart': pd.DataFrame(time_chart),
        'estimated_date': purchase_date.strftime('%B %d, %Y'),
        'down_payment': down_payment,
        'car_price': current_price,
        'monthly_payment': emi,
        'payment_period': months_after_purchase,
        'total_cost': down_payment + (emi * months_after_purchase)
    }