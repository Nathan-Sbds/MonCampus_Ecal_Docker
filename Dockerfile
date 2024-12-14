FROM debian:12-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    cron \
    bash \
    --no-install-recommends && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PATH="/app/venv/bin:$PATH"

# Copy the requirements file, install dependencies, and remove the requirements file
COPY ./app/requirements.txt /app/requirements.txt
RUN python3 -m venv /app/venv && \
    /app/venv/bin/pip install -r /app/requirements.txt && \
    rm /app/requirements.txt

# Convert line endings, set permissions for cronjob, and configure cron
COPY ./app/cronjob /app/cronjob
RUN chmod 0644 /app/cronjob && \
    crontab /app/cronjob && \
    rm /app/cronjob

# Copy the application source code and configuration file
COPY ./app/agenda.py /app/agenda.py
COPY ./config.yml /app/config.yml

# Set working directory
WORKDIR /app

# Start cron
CMD ["cron", "-f"]
