FROM python:3.9-slim AS python_base

# Install Python dependencies
WORKDIR /app/python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Scala/SBT environment
FROM hseeberger/scala-sbt:11.0.14.1_1.6.2_2.13.8 AS scala_base
WORKDIR /app/scala

# Copy Scala/SBT project files
COPY scala/build.sbt .
COPY scala/project/ ./project/
# Download dependencies (will be cached if no changes)
RUN sbt update

# Final stage: Combine Python and Scala environments
FROM python:3.9-slim

# Install OpenJDK and curl
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

# Install OpenJDK, curl and CA certificates
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        default-jre \
        curl \
        gnupg \
        ca-certificates && \
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
RUN mkdir -p /app/python /app/scala /app/config

# Copy application code and .env
COPY python/ /app/python/
COPY scala/ /app/scala/
COPY .env /app/config/.env
COPY entrypoint.sh /app/entrypoint.sh

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Expose ports for Flask (5000) and Scala (8080)
EXPOSE 5000
EXPOSE 8080

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]