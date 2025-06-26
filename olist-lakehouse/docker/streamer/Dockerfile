FROM python:3.9-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir boto3 watchdog

# Copy the streamer script
COPY local_to_minio_streamer.py .

# Set the command to run the script
CMD ["python", "local_to_minio_streamer.py"]