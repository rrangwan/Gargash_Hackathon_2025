FROM python:3.9-slim AS python_base

# Install Python dependencies
WORKDIR /app/python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Scala/SBT environment
FROM hseeberger/scala-sbt:11.0.14.1_1.6.2_2.13.8 AS scala_base
WORKDIR /app/scala

# Copy Scala/SBT project files
COPY build.sbt .
COPY project/ ./project/
# Download dependencies (will be cached if no changes)
RUN sbt update

# Final stage: Combine Python and Scala environments
FROM python:3.9-slim

# Install OpenJDK for Scala
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    openjdk-11-jre-headless \
    curl \
    && rm -rf /var/lib/apt/lists/*
    
# Install SBT
RUN curl -L -o sbt.deb https://repo.scala-sbt.org/scalasbt/debian/sbt-1.6.2.deb && \
    dpkg -i sbt.deb && \
    rm sbt.deb && \
    apt-get update && \
    apt-get install -y sbt && \
    rm -rf /var/lib/apt/lists/*

# Set up project structure
WORKDIR /app

# Copy Python dependencies from python_base
COPY --from=python_base /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=python_base /usr/local/bin /usr/local/bin

# Copy Scala dependencies and build artifacts
COPY --from=scala_base /root/.sbt /root/.sbt
COPY --from=scala_base /root/.cache /root/.cache

# Create necessary directories
RUN mkdir -p /app/python /app/scala

# Copy application code
COPY python/ /app/python/
COPY scala/ /app/scala/

# Create a directory for environment variables
RUN mkdir -p /app/config
COPY .env /app/config/ || echo "No .env file found, will need to be provided at runtime"

# Expose port for Flask app
EXPOSE 5000

# Set working directory
WORKDIR /app/python

# Command to run the application
CMD ["python", "app.py"]