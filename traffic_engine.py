import streamlit as st
import requests
import cv2
import numpy as np
from ultralytics import YOLO
import math
import folium
from streamlit_folium import st_folium
import polyline

# --- SYSTEM CONFIGURATION ---
model = YOLO('yolov8n.pt')
OSRM_URL = "https://router.project-osrm.org/route/v1/driving/"
API_URL = "https://511on.ca/api/v2/get/cameras"

# --- SUBSYSTEM 1: GEOSPATIAL CALCULATIONS ---
def haversine_distance(lat1, lon1, lat2, lon2):
    r = 6371 
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def get_coords(place_name):
    try:
        url = "https://nominatim.openstreetmap.org/search"
        headers = {'User-Agent': 'OntarioTrafficScout/1.0'}
        params = {'q': place_name, 'format': 'json', 'limit': 1}
        res = requests.get(url, params=params, headers=headers).json()
        if res:
            return float(res[0]['lat']), float(res[0]['lon'])
        return None
    except Exception:
        return None

# --- SUBSYSTEM 2: MULTI-VIEW COMPUTER VISION ---
def get_local_traffic(center_lat, center_lon, radius_km=20):
    """Analyzes EVERY direction (View) for each camera in the radius."""
    try:
        all_cams = requests.get(API_URL).json()
        total_vehicles = 0
        active_feeds = []

        for cam in all_cams:
            cam_lat, cam_lon = cam.get('Latitude'), cam.get('Longitude')
            if cam_lat and cam_lon:
                dist = haversine_distance(center_lat, center_lon, cam_lat, cam_lon)
                if dist <= radius_km:
                    # PROFESSIONAL UPDATE: Loop through ALL directions/views
                    views = cam.get('Views', [])
                    for view in views:
                        img_url = view.get('Url')
                        if img_url:
                            img_res = requests.get(img_url, timeout=5)
                            if len(img_res.content) < 10000: continue 

                            img_arr = np.frombuffer(img_res.content, np.uint8)
                            img = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
                            results = model.predict(img, classes=[2, 5, 7], conf=0.25, verbose=False)
                            
                            count = len(results[0].boxes)
                            total_vehicles += count
                            active_feeds.append({
                                "loc": f"{cam.get('Location')} ({view.get('Description', 'Main')})", 
                                "img": img, 
                                "count": count, 
                                "dist": round(dist, 1)
                            })

        multiplier = 1.0
        # Thresholds adjusted slightly higher because we are counting more views
        if total_vehicles > 25: multiplier = 1.4
        if total_vehicles > 50: multiplier = 1.8
        return multiplier, active_feeds
    except Exception:
        return 1.0, []

# --- SUBSYSTEM 3: MAP & ROUTE ---
def create_route_map(start_pt, end_pt, geometry_polyline):
    m = folium.Map(location=[start_pt[0], start_pt[1]], zoom_start=12)
    folium.Marker([start_pt[0], start_pt[1]], tooltip="Start", icon=folium.Icon(color='green')).add_to(m)
    folium.Marker([end_pt[0], end_pt[1]], tooltip="End", icon=folium.Icon(color='red')).add_to(m)
    if geometry_polyline:
        route_points = polyline.decode(geometry_polyline)
        folium.PolyLine(route_points, color="blue", weight=5, opacity=0.7).add_to(m)
    return m

# --- INTERFACE LAYER (STREAMLIT) ---
st.set_page_config(page_title="Traffic Scout Pro", layout="wide")
st.title("Ontario Traffic Scout: Multi-Directional Analysis")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Navigation Control")
    origin = st.text_input("Start Location", "Kitchener City Hall")
    dest = st.text_input("Destination", "Guelph Central Station")
    radius = st.slider("Camera Search Radius (KM)", 5, 50, 20)
    
    if st.button("Calculate Smart Route"):
        with st.spinner("Analyzing Every Direction..."):
            start_point = get_coords(origin)
            end_point = get_coords(dest)
            
            if start_point and end_point:
                weight, feeds = get_local_traffic(start_point[0], start_point[1], radius)
                s_fmt, e_fmt = f"{start_point[1]},{start_point[0]}", f"{end_point[1]},{end_point[0]}"
                query = f"{OSRM_URL}{s_fmt};{e_fmt}?overview=full&geometries=polyline"
                
                res = requests.get(query).json()
                if res.get('routes'):
                    base_sec = res['routes'][0]['duration']
                    geometry = res['routes'][0]['geometry']
                    minutes = round((base_sec * weight) / 60, 2)
                    st.metric("Adjusted ETA", f"{minutes} min")
                    st.metric("Total Regional Detections", len(feeds))
                    st.session_state['map_data'] = (start_point, end_point, geometry)
                    st.session_state['feeds'] = feeds
            else:
                st.error("Location lookup failed.")

with col2:
    if 'map_data' in st.session_state:
        st.subheader("Live Route Visualization")
        start_pt, end_pt, geom = st.session_state['map_data']
        st_folium(create_route_map(start_pt, end_pt, geom), width=800, height=500)

    st.subheader("Regional Perception Layer")
    if 'feeds' in st.session_state:
        sorted_feeds = sorted(st.session_state['feeds'], key=lambda x: x['dist'])
        for f in sorted_feeds:
            with st.expander(f"📍 {f['loc']} | {f['dist']} km"):
                st.write(f"Directional Vehicle Count: **{f['count']}**")
                st.image(f['img'], channels="BGR", use_container_width=True)
