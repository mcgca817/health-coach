FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    rsync \
    libpq-dev \
    gcc \
    openjdk-21-jre-headless \
    rclone \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY config/ ./config/
COPY sql/ ./sql/
COPY tests/ ./tests/

# Install Garmin FitCSVTool
RUN mkdir -p /app/bin && \
    curl -L https://github.com/garmin/fit-sdk-tools/raw/main/FitCSVTool/FitCSVTool.jar -o /app/bin/FitCSVTool.jar

# Set up rclone config directory
RUN mkdir -p /root/.config/rclone

# Environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Default entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
