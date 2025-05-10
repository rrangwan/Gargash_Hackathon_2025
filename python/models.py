import pandas as pd
import numpy as np
import os
import bcrypt

class MockSnowflake:
    def __init__(self):
        # Mock data for cars
        self.car_data = pd.DataFrame({
            'model': ['Mercedes S-Class', 'Mercedes E-Class', 'Maybach S-Class'],
            'year': [2025, 2024, 2023],
            'price': [120000, 80000, 200000],
            'mileage': [0, 15000, 5000],
            'promotion': [False, True, False]
        })

    def query_cars(self, is_new, model, year, max_mileage):
        # Mock filter
        # Real Snowflake code (commented out):
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

        df = self.car_data[
            (self.car_data['year'] == year) &
            (self.car_data['model'] == model) &
            (self.car_data['mileage'] <= max_mileage)
        ]
        return df

    def save_user_data(self, user_id, goal_data):
        # Mock save
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