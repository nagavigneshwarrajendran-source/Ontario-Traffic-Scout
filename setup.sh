#!/bin/bash
# Setup script for Ontario Traffic Scout

echo "Setting up Ontario Traffic Scout..."

# Create directories
mkdir -p models data/samples output

# Download YOLOv8n model if not exists
if [ ! -f "models/yolov8n.pt" ]; then
    echo "Downloading YOLOv8n model..."
    pip install -q ultralytics
    python -c "from ultralytics import YOLO; YOLO('yolov8n.pt').export(); import shutil; shutil.move('yolov8n.pt', 'models/')"
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

echo "Setup complete!"
echo ""
echo "To run analysis:"
echo "  python src/analyze.py --source data/sample.mp4"
echo ""
echo "To use webcam:"
echo "  python src/analyze.py --source 0"
