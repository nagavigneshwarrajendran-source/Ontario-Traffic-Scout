FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for OpenCV
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download YOLOv8 model during build
RUN python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"

# Copy application
COPY src/api.py ./

# Create uploads directory
RUN mkdir -p uploads

EXPOSE 5000

ENV YOLO_MODEL=yolov8n.pt
ENV PORT=5000
ENV FLASK_ENV=production

CMD ["python", "api.py"]
