# Use official Python runtime as base image
FROM python:3.11-slim

# Install system dependencies (needed for compiling chromadb/hnswlib if necessary)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set up user with UID 1000 (required by Hugging Face Spaces)
RUN useradd -m -u 1000 user
WORKDIR /home/user/app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files and set ownership to the 'user'
COPY --chown=user . .

# Set environment variables for port and home directory
ENV PORT=7860
ENV HOME=/home/user

# Switch to the non-root user
USER user

# Expose port 7860 (Hugging Face Spaces default)
EXPOSE 7860

# Start the application using gunicorn on port 7860
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "--timeout", "120", "server:app"]
