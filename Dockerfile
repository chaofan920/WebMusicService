# Use a Python 3.13 base image to match the Render environment
FROM python:3.13-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies required by Playwright's browsers.
# This is the key step to fix the build failure.
RUN apt-get update && apt-get install -y \
    libnss3 \
    libnspr4 \
    libdbus-glib-1-2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libxshmfence1 \
    libfontconfig1 \
    libxkbcommon0 \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright's browser binaries (without system dependencies, as we've already handled them)
RUN playwright install

# Copy the rest of your application code into the container
COPY . .

# Copy the start script and make it executable
COPY start.sh .
RUN chmod +x start.sh

# The Start Command will be executed by this script
CMD ["./start.sh"]
