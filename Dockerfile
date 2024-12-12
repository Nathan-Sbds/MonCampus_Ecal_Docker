FROM debian:12

# Install dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    cron \
    curl \
    git \
    bash \
    dos2unix \
    chromium \
    fonts-liberation \
    libasound2 \
    libdbus-1-3 \
    libgdk-pixbuf2.0-0 \
    libnspr4 \
    libnss3 \
    --no-install-recommends && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PATH="/app/venv/bin:$PATH"

# Copy the requirements file and install dependencies
COPY ./app/requirements.txt /app/requirements.txt
RUN python3 -m venv /app/venv && \
    /app/venv/bin/pip install -r /app/requirements.txt

# Convert line endings and set permissions for entrypoint and cronjob
COPY ./app/entrypoint.sh /app/entrypoint.sh
COPY ./app/cronjob /app/cronjob
RUN dos2unix /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh && \
    chmod 0644 /app/cronjob

# Copy the application source code
COPY ./app/agenda.py /app/agenda.py

# Copy the config file (assuming it is updated less frequently)
COPY config.json /app/config.json

# Set working directory
WORKDIR /app

# Configure cron
RUN crontab /app/cronjob

# Start cron in the foreground
CMD ["cron", "-f"]
