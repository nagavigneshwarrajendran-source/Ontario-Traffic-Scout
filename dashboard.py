import streamlit as st
import cv2
import numpy as np
from pathlib import Path
import time
from datetime import datetime
import json

# Page config
st.set_page_config(
    page_title="Ontario Traffic Scout",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #00ffc8;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #1a1d2e 0%, #0f1117 100%);
        border-radius: 10px;
        padding: 20px;
        border: 1px solid #2d3748;
    }
    .vehicle-count {
        font-size: 2.5rem;
        font-weight: bold;
        color: #00ffc8;
    }
    .status-online {
        color: #39ff14;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

def detect_vehicles_mock(frame):
    """Mock detection for demo purposes."""
    import random
    
    h, w = frame.shape[:2]
    detections = []
    colors = {
        'car': (0, 255, 0),
        'truck': (0, 0, 255),
        'bus': (255, 0, 0),
        'motorcycle': (255, 255, 0)
    }
    
    # Random detections
    n_detections = random.randint(2, 6)
    
    for _ in range(n_detections):
        x1 = random.randint(50, w - 200)
        y1 = random.randint(50, h - 200)
        x2 = x1 + random.randint(80, 150)
        y2 = y1 + random.randint(60, 120)
        
        label = random.choice(['car', 'truck', 'bus', 'motorcycle'])
        conf = random.uniform(0.65, 0.95)
        
        detections.append({
            'bbox': [x1, y1, min(x2, w-10), min(y2, h-10)],
            'class': label,
            'confidence': conf
        })
        
        # Draw box
        color = colors[label]
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        
        # Label
        text = f"{label} {conf:.2f}"
        cv2.putText(frame, text, (x1, y1 - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    return frame, detections

def main():
    st.markdown('<p class="main-header">Ontario Traffic Scout</p>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("Configuration")
        
        source = st.selectbox(
            "Video Source",
            ["Demo Feed (Simulated)", "Upload Video", "Webcam"]
        )
        
        if source == "Upload Video":
            uploaded_file = st.file_uploader("Upload video", type=['mp4', 'avi', 'mov'])
        
        confidence = st.slider("Confidence Threshold", 0.1, 1.0, 0.5)
        
        st.markdown("---")
        
        st.header("About")
        st.info("""
        **Technology Stack:**
        - YOLOv8 Object Detection
        - OpenCV Video Processing
        - OSRM Routing Integration
        - Streamlit Dashboard
        """)
        
        st.markdown("---")
        st.caption("Built by Nagavigneshwar Rajendran")
    
    # Main content
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Vehicles/Min", "42", "+5%")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Avg Speed", "82 km/h", "-3%")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Density", "Medium", "Stable")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Status", "ONLINE", "", delta_color="off")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Video feed and analysis
    col_video, col_analysis = st.columns([2, 1])
    
    with col_video:
        st.subheader("Live Video Feed")
        
        # Create placeholder for video
        frame_placeholder = st.empty()
        
        # Generate sample highway frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Draw road
        cv2.rectangle(frame, (0, 200), (640, 480), (50, 50, 50), -1)
        
        # Draw lane markings
        for i in range(0, 640, 80):
            cv2.rectangle(frame, (i, 330), (i + 40, 340), (255, 255, 255), -1)
        
        # Add detection boxes (mock)
        frame, detections = detect_vehicles_mock(frame)
        
        # Convert to RGB for Streamlit
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        frame_placeholder.image(frame_rgb, channels="RGB", use_column_width=True)
        
        # Auto-refresh note
        st.caption("Demo mode: Showing simulated highway feed with YOLOv8 detections")
    
    with col_analysis:
        st.subheader("Detection Summary")
        
        # Vehicle breakdown
        vehicle_counts = {'car': 0, 'truck': 0, 'bus': 0, 'motorcycle': 0}
        for d in detections:
            vehicle_counts[d['class']] += 1
        
        for vtype, count in vehicle_counts.items():
            if count > 0:
                st.write(f"**{vtype.capitalize()}s:** {count}")
        
        st.markdown("---")
        
        st.subheader("Congestion Analysis")
        
        # Congestion gauge
        congestion = 0.35  # 0-1 scale
        
        fig_col1, fig_col2 = st.columns([1, 3])
        with fig_col1:
            if congestion < 0.3:
                st.markdown("<span style='color: #00ff00; font-size: 2rem;'>●</span> LOW", unsafe_allow_html=True)
            elif congestion < 0.7:
                st.markdown("<span style='color: #ffa500; font-size: 2rem;'>●</span> MEDIUM", unsafe_allow_html=True)
            else:
                st.markdown("<span style='color: #ff0000; font-size: 2rem;'>●</span> HIGH", unsafe_allow_html=True)
        
        with fig_col2:
            st.progress(congestion)
        
        st.markdown("---")
        
        st.subheader("Routing Recommendation")
        st.info("Route 401 East: **Clear** - Estimated time: 18 min")
        st.warning("Route 401 West: **Moderate traffic** - Estimated time: 24 min (+6 min)")
    
    st.markdown("---")
    
    # Historical data
    st.subheader("Traffic History (Last Hour)")
    
    import pandas as pd
    
    # Generate sample historical data
    times = pd.date_range(start=datetime.now() - pd.Timedelta(hours=1), periods=12, freq='5min')
    vehicle_data = np.random.normal(40, 8, 12).astype(int)
    
    chart_data = pd.DataFrame({
        'Time': times,
        'Vehicles/Min': vehicle_data
    })
    
    st.line_chart(chart_data.set_index('Time'))
    
    # Footer
    st.markdown("---")
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Ontario Traffic Scout Demo")

if __name__ == "__main__":
    main()
