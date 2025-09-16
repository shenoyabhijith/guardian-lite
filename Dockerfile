FROM python:3.11-slim-bullseye

WORKDIR /app

# Install Docker CLI
RUN apt-get update && \
    apt-get install -y curl && \
    curl -fsSL https://get.docker.com | sh && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy everything
COPY . .

# Allow access to host Docker
VOLUME ["/var/run/docker.sock"]

# Expose GUI on port 8080
EXPOSE 8080

# Start GUI server
CMD ["python", "web.py"]
