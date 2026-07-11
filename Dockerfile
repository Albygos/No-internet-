# Use a lightweight Python base image
FROM python:3.11-slim

# Set environment variables to optimize Python in a container
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install Chromium and Chromium-driver for headless browsing
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Python script into the container
COPY loop_video.py .

# Command to run the script when the container starts
CMD ["python", "loop_video.py"]
