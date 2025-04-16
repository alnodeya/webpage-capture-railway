
FROM python:3.11-slim

# Install required system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libc6 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libgdk-pixbuf2.0-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome
RUN curl -sSL https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb -o chrome.deb && \
    apt-get update && apt-get install -y ./chrome.deb && \
    rm chrome.deb

# Set environment variables
ENV CHROME_BIN=/usr/bin/google-chrome

# Set working directory
WORKDIR /app

# Copy files
COPY requirements.txt requirements.txt
COPY app.py app.py
COPY templates/ templates/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 8000

# Run the app
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
