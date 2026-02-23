# Ontario Traffic Scout

Real-time traffic analysis using YOLOv8 computer vision on Ontario 511 highway feeds.

## 🎯 Features

- **YOLOv8 Object Detection** — Vehicles, trucks, buses in real-time
- **Traffic Density Analysis** — Calculate congestion levels per lane
- **OSRM Integration** — Adaptive routing based on traffic weight
- **Live Dashboard** — Streamlit-based web interface

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Download YOLOv8 model
python setup.py

# Run analysis on video
python src/analyze.py --source data/sample.mp4

# Launch dashboard
streamlit run src/dashboard.py
```

## 📊 Demo

```bash
# Process Ontario 511 feed
python src/fetch_511.py --region 401
python src/analyze.py --source output/401_feed.mp4
```

## 🛠 Tech Stack

- **YOLOv8** — Ultralytics object detection
- **OpenCV** — Video processing
- **OSRM** — Open Source Routing Machine
- **Streamlit** — Dashboard UI
- **Python 3.10+**

## 📁 Structure

```
├── src/
│   ├── analyze.py       # Main analysis engine
│   ├── fetch_511.py     # Ontario 511 API scraper
│   ├── dashboard.py     # Streamlit dashboard
│   └── routing.py       # OSRM integration
├── models/
│   └── yolov8n.pt       # YOLOv8 nano model
├── data/
│   └── samples/         # Test videos
└── output/              # Analysis results
```

## 📈 Sample Output

| Metric | Value |
|--------|-------|
| Vehicles/min | 45 |
| Avg Speed | 85 km/h |
| Density | Medium |
| Congestion Score | 0.3 |

## 🔗 Links

- [Ontario 511](https://511on.ca/)
- [OSRM Documentation](http://project-osrm.org/)
- [YOLOv8 Docs](https://docs.ultralytics.com/)

## 📄 License

MIT
