# Use official Python image
FROM python:3.11

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Update package list and install system dependencies for pyAudio
RUN apt-get update && apt-get install -y \
    build-essential \
    libportaudio2 \
    portaudio19-dev \
    libsndfile1 \
    gcc \
    g++ \
    python3-dev

# Set working directory
WORKDIR /app

# Copy the entire project
COPY . .

# Upgrade pip and install requirements
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Start the app
CMD ["python", "voice.py"]
