FROM debian:12-slim

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
    fonts-liberation \
    libasound2 \
    libdbus-1-3 \
    libgdk-pixbuf2.0-0 \
    libnspr4 \
    libnss3 \
    xvfb \
    wget \
    firefox-esr=128.5.0esr-1~deb12u1 \
    --no-install-recommends && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Geckodriver version 0.35.0
RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.35.0/geckodriver-v0.35.0-linux64.tar.gz -O /tmp/geckodriver.tar.gz && \
    tar -xvzf /tmp/geckodriver.tar.gz -C /usr/local/bin && \
    rm /tmp/geckodriver.tar.gz

# Set environment variables
ENV PATH="/app/venv/bin:$PATH"
ENV DISPLAY=:99

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
COPY config.ini /app/config.ini

# Set working directory
WORKDIR /app

# Configure cron
RUN crontab /app/cronjob

# Start Xvfb for display forwarding
CMD ["Xvfb", ":99", "-ac", "-screen", "0", "1024x768x24", "-nolisten", "tcp", "-extension", "RANDR"]
CMD ["cron", "-f"]
