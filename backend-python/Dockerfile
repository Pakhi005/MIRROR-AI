FROM python:3.11-slim

# Install system dependencies for audio processing (ffmpeg may be needed by Whisper/pydub)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

# Use gunicorn or flask run
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
