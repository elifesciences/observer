# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy requirements file and install Python dependencies for observer
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the observer application code
COPY . /app
RUN chmod +x /app/install.sh

# Expose port (if the application runs a web server)
EXPOSE 8000

# COPY src/manage.py  /app/manage.py


# Run the application
ENTRYPOINT ["/app/manage.sh", "runserver", "0.0.0.0:8000"]