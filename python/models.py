import pandas as pd
import numpy as np
import requests
import os
import bcrypt

class MockSnowflake:
    def __init__(self):
        # Mock data for cars (fallback if Scala service is unavailable)
        self.car_data = pd.DataFrame({
            'model': ['Mercedes S-Class', 'Mercedes E-Class', 'Maybach S-Class'],
            'year': [2025, 2024, 2023],
            'price': [120000, 80000, 200000],
            'mileage': [0, 15000, 5000],
            'promotion': [False, True, False]
        })

    def query_cars(self, is_new, model, year, max_mileage):
        # Try calling Scala service
        try:
            response = requests.post('http://localhost:8080/query', json={
                'is_new': is_new,
                'model': model,
                'year': year,
                'max_mileage': max_mileage
            })
            if response.status_code == 200:
                return pd.DataFrame(response.json())
        except requests.RequestException:
            print("Scala service unavailable, using mock data")

        # Fallback to mock data
        # from app import connect_to_snowflake
        # conn = connect_to_snowflake()
        # if conn:
        #     query = f"""
        #     SELECT model, year, price, mileage, promotion
        #     FROM cars
        #     WHERE is_new = {is_new} AND model = '{model}' AND year = {year} AND mileage <= {max_mileage}
        #     """
        #     df = pd.read_sql(query, conn)
        #     conn.close()
        #     return df

        # Mock filter
        df = self.car_data[
            (self.car_data['year'] == year) &
            (self.car_data['model'] == model) &
            (self.car_data['mileage'] <= max_mileage)
        ]
        return df

    def save_user_data(self, user_id, goal_data):
        # Simulate saving to Snowflake via Scala service
        try:
            response = requests.post('http://localhost:8080/save', json={
                'user_id': user_id,
                'goal_data': goal_data
            })
            if response.status_code == 200:
                print(f"Mock: Saved data via Scala service for user {user_id}")
        except requests.RequestException:
            print("Scala service unavailable, using mock save")

        # Real Snowflake code (commented out):
        # from app import connect_to_snowflake
        # conn = connect_to_snowflake()
        # if conn:
        #     cursor = conn.cursor()
        #     cursor.execute("INSERT INTO user_goals (user_id, goal_data) VALUES (%s, %s)", (user_id, str(goal_data)))
        #     conn.commit()
        #     cursor.close()
        #     conn.close()
        print(f"Mock: Saved data for user {user_id}: {goal_data}")

class User:
    def __init__(self):
        # Mock user storage with hashed passwords
        self.users = {
            'testuser': bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt())
        }

    def authenticate(self, username, password):
        hashed = self.users.get(username)
        if hashed and bcrypt.checkpw(password.encode('utf-8'), hashed):
            return True
        return False

    def save_goal(self, username, goal_data):
        mock_snowflake = MockSnowflake()
        mock_snowflake.save_user_data(username, goal_data)