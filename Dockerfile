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

# Install OpenJDK and curl - fixed to properly install Java
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    default-jre \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*
    
# Install SBT
RUN echo "deb https://repo.scala-sbt.org/scalasbt/debian all main" | tee /etc/apt/sources.list.d/sbt.list && \
    echo "deb https://repo.scala-sbt.org/scalasbt/debian /" | tee /etc/apt/sources.list.d/sbt_old.list && \
    curl -sL "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x2EE0EA64E40A89B84B2DF73499E82A75642AC823" | apt-key add && \
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
# Handle .env file - create an empty one if it doesn't exist
RUN touch /app/config/.env

# Expose port for Flask app
EXPOSE 5000

# Set working directory
WORKDIR /app/python

# Command to run the application
CMD ["python", "app.py"]