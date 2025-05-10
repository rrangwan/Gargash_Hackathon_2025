#!/bin/bash

# Start Scala service in the background
cd /app/scala
sbt "runMain com.example.SnowflakeMock" &

# Start Flask app
cd /app/python
export FLASK_APP=app.py
export FLASK_ENV=development
flask run --host=0.0.0.0 --port=5000