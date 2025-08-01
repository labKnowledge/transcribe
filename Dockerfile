FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    portaudio19-dev \
    python3-tk \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY transcriber_core.py .
COPY web_app.py .
COPY templates/ ./templates/

# Create a non-root user for security
RUN useradd -m -u 1000 transcriber && \
    chown -R transcriber:transcriber /app
USER transcriber

# Expose port for potential web interface (future enhancement)
EXPOSE 8081

# Set the default command
CMD ["python", "web_app.py"] 