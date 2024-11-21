FROM debian:12

# Install dependencies including git, curl, cron, python3, python3-venv, bash, and dos2unix
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
    --no-install-recommends

# Create a symlink for chromium to ensure it can be used in the path
RUN ln -s /usr/bin/chromium /usr/bin/chromium-browser

# Copy the content of the local 'app' directory to the container's /app directory
COPY ./app /app

# Copy the config.json file to the app folder (assuming it's also next to the Dockerfile)
COPY config.json /app/config.json

# Check the contents of the app directory to ensure entrypoint.sh is present
RUN ls -l /app

# Convert line endings of entrypoint.sh to Unix format to avoid issues on Windows systems
RUN dos2unix /app/entrypoint.sh

# Set permissions for the cron job and the entrypoint script
RUN chmod +x /app/entrypoint.sh && chmod 0644 /app/cronjob

# Install Python dependencies
RUN python3 -m venv /app/venv && \
    /app/venv/bin/pip install --upgrade pip && \
    /app/venv/bin/pip install -r /app/requirements.txt

# Set working directory
WORKDIR /app

# Set the cron job
RUN crontab /app/cronjob

# Start cron service in the foreground so it keeps running
CMD cron -f
