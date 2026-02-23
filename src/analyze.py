#!/usr/bin/env python3
"""
Ontario Traffic Scout - Video Analysis Engine
Uses YOLOv8 for vehicle detection and traffic density analysis.
"""

import cv2
import json
import argparse
from pathlib import Path
from collections import defaultdict, deque
from datetime import datetime
import time

# Try to import ultralytics, fallback to basic implementation if not available
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("Warning: ultralytics not installed. Using mock detection.")
    print("Install with: pip install ultralytics")


class TrafficAnalyzer:
    """Analyzes video streams for vehicle detection and traffic metrics."""
    
    def __init__(self, model_path="models/yolov8n.pt", conf_threshold=0.3):
        self.conf_threshold = conf_threshold
        self.model = None
        
        if YOLO_AVAILABLE and Path(model_path).exists():
            self.model = YOLO(model_path)
            print(f"Loaded YOLOv8 model: {model_path}")
        else:
            print("Running in DEMO mode (no model loaded)")
        
        # Traffic metrics
        self.vehicle_counts = defaultdict(int)
        self.vehicle_history = deque(maxlen=1000)
        self.frame_count = 0
        self.start_time = time.time()
        
    def detect_vehicles(self, frame):
        """Detect vehicles in a frame using YOLOv8."""
        if self.model is None:
            # Mock detection for demo
            return self._mock_detection(frame)
        
        results = self.model(frame, conf=self.conf_threshold, classes=[2, 3, 5, 7])
        detections = []
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                
                # COCO class names for vehicles
                class_names = {2: 'car', 3: 'motorcycle', 5: 'bus', 7: 'truck'}
                label = class_names.get(cls, 'vehicle')
                
                detections.append({
                    'bbox': [int(x1), int(y1), int(x2), int(y2)],
                    'confidence': conf,
                    'class': label
                })
                
        return detections
    
    def _mock_detection(self, frame):
        """Generate mock detections for demo purposes."""
        import random
        h, w = frame.shape[:2]
        
        # Random detections
        n_detections = random.randint(3, 8)
        detections = []
        
        classes = ['car', 'truck', 'bus', 'motorcycle']
        
        for _ in range(n_detections):
            x1 = random.randint(0, w - 100)
            y1 = random.randint(0, h - 100)
            x2 = x1 + random.randint(50, 150)
            y2 = y1 + random.randint(50, 150)
            
            detections.append({
                'bbox': [x1, y1, min(x2, w), min(y2, h)],
                'confidence': random.uniform(0.4, 0.9),
                'class': random.choice(classes)
            })
            
        return detections
    
    def analyze_frame(self, frame):
        """Analyze a single frame and return annotated frame + metrics."""
        detections = self.detect_vehicles(frame)
        
        # Update counts
        for det in detections:
            self.vehicle_counts[det['class']] += 1
            self.vehicle_history.append({
                'timestamp': time.time(),
                'class': det['class'],
                'confidence': det['confidence']
            })
        
        # Draw bounding boxes
        annotated = self._annotate_frame(frame, detections)
        
        # Calculate metrics
        metrics = self._calculate_metrics()
        
        self.frame_count += 1
        return annotated, metrics, len(detections)
    
    def _annotate_frame(self, frame, detections):
        """Draw bounding boxes and labels on frame."""
        annotated = frame.copy()
        
        colors = {
            'car': (0, 255, 0),
            'truck': (0, 0, 255),
            'bus': (255, 0, 0),
            'motorcycle': (255, 255, 0)
        }
        
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            label = det['class']
            conf = det['confidence']
            color = colors.get(label, (128, 128, 128))
            
            # Draw box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            
            # Draw label
            text = f"{label} {conf:.2f}"
            (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(annotated, (x1, y1 - th - 8), (x1 + tw, y1), color, -1)
            cv2.putText(annotated, text, (x1, y1 - 4), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        
        return annotated
    
    def _calculate_metrics(self):
        """Calculate traffic metrics."""
        elapsed = time.time() - self.start_time
        
        # Vehicles per minute
        vehicles_per_minute = (sum(self.vehicle_counts.values()) / elapsed) * 60 if elapsed > 0 else 0
        
        # Recent window (last 30 seconds)
        recent_cutoff = time.time() - 30
        recent_vehicles = [v for v in self.vehicle_history if v['timestamp'] > recent_cutoff]
        
        # Density calculation
        density = len(recent_vehicles) / 30 if recent_vehicles else 0
        
        return {
            'total_vehicles': sum(self.vehicle_counts.values()),
            'vehicles_per_minute': round(vehicles_per_minute, 1),
            'density': round(density, 2),
            'breakdown': dict(self.vehicle_counts),
            'elapsed_time': round(elapsed, 1)
        }
    
    def process_video(self, source, output_path=None, display=True):
        """Process video file or stream."""
        # Open video source
        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            print(f"Error: Could not open video source: {source}")
            return
        
        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"Processing: {width}x{height} @ {fps}fps")
        
        # Setup output video
        writer = None
        if output_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        frame_skip = max(1, fps // 5)  # Process 5 FPS max
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Skip frames for performance
                if self.frame_count % frame_skip != 0:
                    self.frame_count += 1
                    continue
                
                # Analyze frame
                annotated, metrics, count = self.analyze_frame(frame)
                
                # Add metrics overlay
                self._draw_metrics(annotated, metrics)
                
                # Write output
                if writer:
                    writer.write(annotated)
                
                # Display
                if display:
                    cv2.imshow('Traffic Scout', annotated)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                
                # Print progress
                if self.frame_count % 30 == 0:
                    print(f"Frame {self.frame_count}: {metrics['vehicles_per_minute']} veh/min, "
                          f"Density: {metrics['density']}")
                
        finally:
            cap.release()
            if writer:
                writer.release()
            cv2.destroyAllWindows()
            
            # Save final report
            self._save_report()
    
    def _draw_metrics(self, frame, metrics):
        """Draw metrics overlay on frame."""
        h, w = frame.shape[:2]
        
        # Background panel
        panel_h = 120
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (300, panel_h), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # Text
        y_offset = 30
        cv2.putText(frame, f"Vehicles/min: {metrics['vehicles_per_minute']}", 
                   (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        y_offset += 25
        cv2.putText(frame, f"Density: {metrics['density']}", 
                   (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        y_offset += 25
        cv2.putText(frame, f"Total: {metrics['total_vehicles']}", 
                   (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Density indicator
        density_color = (0, 255, 0) if metrics['density'] < 0.5 else (0, 165, 255) if metrics['density'] < 1.0 else (0, 0, 255)
        cv2.circle(frame, (270, 35), 10, density_color, -1)
    
    def _save_report(self):
        """Save analysis report to JSON."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_frames': self.frame_count,
            'vehicle_counts': dict(self.vehicle_counts),
            'analysis_duration': time.time() - self.start_time
        }
        
        output_file = f"output/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        Path(output_file).parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nReport saved: {output_file}")
        print(f"Summary: {report}")


def main():
    parser = argparse.ArgumentParser(description='Ontario Traffic Scout - Video Analysis')
    parser.add_argument('--source', '-s', default='0', 
                       help='Video source (file path, URL, or 0 for webcam)')
    parser.add_argument('--output', '-o', help='Output video path')
    parser.add_argument('--model', '-m', default='models/yolov8n.pt',
                       help='YOLOv8 model path')
    parser.add_argument('--conf', '-c', type=float, default=0.3,
                       help='Confidence threshold')
    parser.add_argument('--no-display', action='store_true',
                       help='Run without display (headless mode)')
    
    args = parser.parse_args()
    
    # Convert source to int if it's a webcam index
    if args.source.isdigit():
        args.source = int(args.source)
    
    # Initialize analyzer
    analyzer = TrafficAnalyzer(model_path=args.model, conf_threshold=args.conf)
    
    # Process video
    analyzer.process_video(
        source=args.source,
        output_path=args.output,
        display=not args.no_display
    )


if __name__ == '__main__':
    main()
