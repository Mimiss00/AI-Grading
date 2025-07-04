# Use a lightweight Python base image
FROM python:3.10-slim

# Install system dependencies including Poppler
RUN apt-get update && apt-get install -y \
    poppler-utils \
    gcc \
    build-essential \
    libpoppler-cpp-dev \
    && apt-get clean

# Set working directory inside the container
WORKDIR /app

# Copy your local project files into the container
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Start your app (change this if you use Flask, FastAPI, etc.)
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8080"]
