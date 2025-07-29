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
ENV CONFIG_FILE="/app/config.yml"

# Copy the requirements file, install dependencies, and remove the requirements file
COPY ./app/requirements.txt /app/requirements.txt
RUN python3 -m venv /app/venv && \
    /app/venv/bin/pip install -r /app/requirements.txt && \
    rm /app/requirements.txt

# Copy the application source code
COPY ./app/agenda.py /app/agenda.py
COPY ./app/setup_cronjobs.sh /app/setup_cronjobs.sh
RUN chmod +x /app/setup_cronjobs.sh

# Create configs directory
RUN mkdir -p /app/configs

# Set working directory
WORKDIR /app

# Setup cron and start
CMD ["/app/setup_cronjobs.sh"]
