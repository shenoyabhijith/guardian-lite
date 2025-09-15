FROM python:3.11-slim-bullseye

WORKDIR /app

# Install only essentials
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
