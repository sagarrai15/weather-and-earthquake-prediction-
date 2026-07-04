# Weather and Earthquake Prediction

## Earthquake Detail and Analysis

A Flask web application that fetches real-time earthquake data from the **USGS Earthquake Catalog API** and provides detailed event information, interactive maps, and analysis dashboards.

### Features

- **Live dashboard** – lists recent earthquakes with magnitude, location, depth, and alert level
- **Interactive map** – plots every event as a scaled, colour-coded circle marker on an OpenStreetMap base layer
- **Statistical summary** – total events, average/max magnitude, average depth, tsunami alerts, significant events
- **Magnitude distribution chart** – bar chart of events grouped by category (Micro → Great)
- **Daily event count chart** – line chart showing activity over time
- **Earthquake detail page** – deep-dive view for each event including:
  - Full seismic parameters (CDI, MMI, NST, gap, RMS …)
  - Epicentre map with estimated impact radius
  - Magnitude interpretation and depth classification
  - PAGER alert badge and tsunami flag
- **JSON API** – `/api/earthquakes` endpoint for programmatic access

### Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app
python app.py

# 3. Open http://127.0.0.1:5000 in your browser
```

### Project Structure

```
.
├── app.py                   # Flask application & routes
├── earthquake_analyzer.py   # USGS API client and analysis utilities
├── requirements.txt
├── static/
│   ├── css/style.css
│   └── js/main.js           # Leaflet map + Chart.js logic
└── templates/
    ├── index.html            # Dashboard
    └── detail.html           # Single-event detail & analysis
```

### Data Source

Earthquake data is fetched from the freely available
[USGS Earthquake Catalog API](https://earthquake.usgs.gov/fdsnws/event/1/) –
no API key required.
