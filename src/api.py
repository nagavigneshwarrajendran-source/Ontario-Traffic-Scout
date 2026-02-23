#!/usr/bin/env python3
"""
Traffic Scout API - Real YOLOv8 Object Detection
Flask API for video processing with YOLOv8
"""

import os
import io
import base64
import tempfile
from pathlib import Path
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import cv2
import numpy as np
from PIL import Image

# Try to import YOLO
try:
    from ultralytics import YOLO
    MODEL_AVAILABLE = True
except ImportError:
    MODEL_AVAILABLE = False
    print("WARNING: ultralytics not installed. Run: pip install ultralytics")

app = Flask(__name__)
CORS(app)

# Load model
model = None
def get_model():
    global model
    if model is None and MODEL_AVAILABLE:
        model_path = os.environ.get('YOLO_MODEL', 'yolov8n.pt')
        if Path(model_path).exists():
            model = YOLO(model_path)
            print(f"Loaded YOLOv8 model: {model_path}")
        else:
            print(f"Model not found: {model_path}, downloading...")
            model = YOLO('yolov8n.pt')
    return model

# HTML Interface
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Ontario Traffic Scout - Live Analysis</title>
    <style>
        body { font-family: sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #0a0e17; color: #e4e4ef; }
        h1 { color: #00ffc8; }
        .upload-box { border: 2px dashed #00ffc8; padding: 40px; text-align: center; margin: 20px 0; border-radius: 10px; }
        .upload-box:hover { background: rgba(0,255,200,0.05); }
        button { background: #00ffc8; color: #000; padding: 12px 30px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
        button:hover { opacity: 0.9; }
        #results { margin-top: 30px; }
        .detection { background: #1a1d2e; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 3px solid #00ffc8; }
        .video-container { margin: 20px 0; }
        video, img { max-width: 100%; border-radius: 8px; }
        .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 20px 0; }
        .stat-box { background: #1a1d2e; padding: 20px; border-radius: 8px; text-align: center; }
        .stat-value { font-size: 2rem; font-weight: bold; color: #00ffc8; }
        .stat-label { color: #7a7d95; font-size: 0.9rem; margin-top: 5px; }
        .loading { display: none; text-align: center; padding: 40px; }
        .loading.active { display: block; }
        .error { background: #ef4444; color: white; padding: 15px; border-radius: 8px; margin: 20px 0; }
    </style>
</head>
<body>
    <h1>Ontario Traffic Scout - YOLOv8 Analysis</h1>
    <p>Upload a video to detect and count vehicles in real-time.</p>
    
    <div class="upload-box">
        <form id="uploadForm" enctype="multipart/form-data">
            <input type="file" name="video" accept="video/*" required style="margin: 20px 0;">
            <br>
            <button type="submit">Analyze Video</button>
        </form>
    </div>
    
    <div class="loading" id="loading">
        <p>Processing video with YOLOv8...</p>
        <p>This may take a minute depending on video length.</p>
    </div>
    
    <div id="results"></div>
    
    <script>
        document.getElementById('uploadForm').onsubmit = async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const loading = document.getElementById('loading');
            const results = document.getElementById('results');
            
            loading.classList.add('active');
            results.innerHTML = '';
            
            try {
                const response = await fetch('/api/analyze', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                loading.classList.remove('active');
                
                if (data.error) {
                    results.innerHTML = '<div class="error">Error: ' + data.error + '</div>';
                    return;
                }
                
                // Display results
                let html = '<h2>Analysis Results</h2>';
                
                // Stats
                html += '<div class="stats">';
                html += '<div class="stat-box"><div class="stat-value">' + data.total_vehicles + '</div><div class="stat-label">Total Vehicles</div></div>';
                html += '<div class="stat-box"><div class="stat-value">' + data.vehicles_per_minute + '</div><div class="stat-label">Vehicles/Min</div></div>';
                html += '<div class="stat-box"><div class="stat-value">' + data.processing_time + 's</div><div class="stat-label">Processing Time</div></div>';
                html += '<div class="stat-box"><div class="stat-value">' + data.frames_analyzed + '</div><div class="stat-label">Frames</div></div>';
                html += '</div>';
                
                // Breakdown
                html += '<h3>Vehicle Breakdown</h3>';
                for (const [type, count] of Object.entries(data.breakdown)) {
                    html += '<div class="detection"><strong>' + type.charAt(0).toUpperCase() + type.slice(1) + ':</strong> ' + count + '</div>';
                }
                
                // Output video
                if (data.output_video) {
                    html += '<h3>Annotated Video</h3>';
                    html += '<div class="video-container">';
                    html += '<video controls><source src="data:video/mp4;base64,' + data.output_video + '" type="video/mp4"></video>';
                    html += '</div>';
                }
                
                results.innerHTML = html;
                
            } catch (err) {
                loading.classList.remove('active');
                results.innerHTML = '<div class="error">Error: ' + err.message + '</div>';
            }
        };
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/analyze', methods=['POST'])
def analyze_video():
    """Process uploaded video with YOLOv8."""
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
    
    video_file = request.files['video']
    if video_file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Save uploaded file
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
        video_file.save(tmp.name)
        input_path = tmp.name
    
    try:
        # Process video
        results = process_video_real(input_path)
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        # Cleanup
        if os.path.exists(input_path):
            os.unlink(input_path)

def process_video_real(video_path):
    """Real YOLOv8 video processing."""
    model = get_model()
    
    if model is None:
        # Fallback to mock data if model not available
        return {
            'total_vehicles': 42,
            'vehicles_per_minute': 35,
            'frames_analyzed': 150,
            'processing_time': 2.5,
            'breakdown': {'car': 30, 'truck': 8, 'bus': 2, 'motorcycle': 2},
            'note': 'Running in DEMO mode - YOLOv8 model not loaded'
        }
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("Could not open video file")
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Process every Nth frame for speed
    frame_skip = max(1, int(fps / 2))  # 2 FPS
    
    detections = []
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_count % frame_skip == 0:
            # Run YOLO inference
            results = model(frame, verbose=False)
            
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    
                    # COCO class IDs for vehicles
                    # 2=car, 3=motorcycle, 5=bus, 7=truck
                    if cls in [2, 3, 5, 7] and conf > 0.3:
                        class_names = {2: 'car', 3: 'motorcycle', 5: 'bus', 7: 'truck'}
                        detections.append({
                            'class': class_names[cls],
                            'confidence': conf,
                            'frame': frame_count
                        })
        
        frame_count += 1
    
    cap.release()
    
    # Calculate metrics
    duration_minutes = (total_frames / fps) / 60 if fps > 0 else 1
    total = len(detections)
    vpm = total / duration_minutes if duration_minutes > 0 else 0
    
    # Breakdown by type
    breakdown = {}
    for d in detections:
        t = d['class']
        breakdown[t] = breakdown.get(t, 0) + 1
    
    return {
        'total_vehicles': total,
        'vehicles_per_minute': round(vpm, 1),
        'frames_analyzed': frame_count // frame_skip,
        'processing_time': round(duration_minutes * 60, 1),
        'breakdown': breakdown,
        'fps': round(fps, 1),
        'model': 'YOLOv8n'
    }

@app.route('/api/health')
def health():
    return jsonify({
        'status': 'ok',
        'model_loaded': model is not None,
        'model_available': MODEL_AVAILABLE
    })

if __name__ == '__main__':
    # Preload model
    get_model()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
