"""
earthquake_analyzer.py
Fetches earthquake data from the USGS Earthquake Catalog API and provides
analysis utilities used by the Flask application.
"""

import requests
from datetime import datetime, timedelta, timezone
from dateutil import parser as dateparser
import statistics


USGS_BASE = "https://earthquake.usgs.gov/fdsnws/event/1"


# ---------------------------------------------------------------------------
# Data Fetching
# ---------------------------------------------------------------------------

def fetch_earthquakes(
    starttime=None,
    endtime=None,
    minmagnitude=0,
    maxmagnitude=None,
    limit=100,
    orderby="time",
):
    """Return a list of earthquake dicts from the USGS GeoJSON feed."""
    if endtime is None:
        endtime = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if starttime is None:
        starttime = (datetime.now(timezone.utc) - timedelta(days=30)).strftime(
            "%Y-%m-%d"
        )

    params = {
        "format": "geojson",
        "starttime": starttime,
        "endtime": endtime,
        "minmagnitude": minmagnitude,
        "limit": limit,
        "orderby": orderby,
    }
    if maxmagnitude is not None:
        params["maxmagnitude"] = maxmagnitude

    resp = requests.get(f"{USGS_BASE}/query", params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return [_parse_feature(f) for f in data.get("features", [])]


def fetch_earthquake_by_id(event_id):
    """Return a single earthquake dict for the given USGS event ID."""
    resp = requests.get(f"{USGS_BASE}/query", params={"format": "geojson", "eventid": event_id}, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    features = data.get("features", [])
    if features:
        return _parse_feature(features[0])
    return None


def _parse_feature(feature):
    """Convert a GeoJSON feature into a flat dict."""
    props = feature.get("properties", {})
    geom = feature.get("geometry", {})
    coords = geom.get("coordinates", [None, None, None])

    # Timestamp is milliseconds since epoch
    time_ms = props.get("time")
    time_dt = (
        datetime.fromtimestamp(time_ms / 1000, tz=timezone.utc) if time_ms else None
    )

    updated_ms = props.get("updated")
    updated_dt = (
        datetime.fromtimestamp(updated_ms / 1000, tz=timezone.utc)
        if updated_ms
        else None
    )

    return {
        "id": feature.get("id", ""),
        "magnitude": props.get("mag"),
        "place": props.get("place", "Unknown"),
        "time": time_dt.strftime("%Y-%m-%d %H:%M:%S UTC") if time_dt else "N/A",
        "time_iso": time_dt.isoformat() if time_dt else None,
        "updated": updated_dt.strftime("%Y-%m-%d %H:%M:%S UTC") if updated_dt else "N/A",
        "longitude": coords[0],
        "latitude": coords[1],
        "depth_km": coords[2],
        "status": props.get("status", ""),
        "tsunami": props.get("tsunami", 0),
        "sig": props.get("sig", 0),
        "net": props.get("net", ""),
        "type": props.get("type", "earthquake"),
        "url": props.get("url", ""),
        "felt": props.get("felt"),
        "cdi": props.get("cdi"),
        "mmi": props.get("mmi"),
        "alert": props.get("alert"),
        "nst": props.get("nst"),
        "dmin": props.get("dmin"),
        "rms": props.get("rms"),
        "gap": props.get("gap"),
        "mag_type": props.get("magType", ""),
        "detail_url": props.get("detail", ""),
    }


# ---------------------------------------------------------------------------
# Analysis Utilities
# ---------------------------------------------------------------------------

def magnitude_category(mag):
    """Return a human-readable magnitude category string."""
    if mag is None:
        return "Unknown"
    if mag < 2.0:
        return "Micro"
    if mag < 4.0:
        return "Minor"
    if mag < 5.0:
        return "Light"
    if mag < 6.0:
        return "Moderate"
    if mag < 7.0:
        return "Strong"
    if mag < 8.0:
        return "Major"
    return "Great"


def alert_label(alert):
    """Return a Bootstrap colour class for a PAGER alert level."""
    mapping = {
        "green": "success",
        "yellow": "warning",
        "orange": "orange",
        "red": "danger",
    }
    return mapping.get(alert, "secondary") if alert else "secondary"


def analyze_earthquakes(earthquakes):
    """
    Return an analysis summary dict for a list of earthquake dicts.

    Keys returned:
        total, avg_magnitude, max_magnitude, min_magnitude,
        avg_depth, max_depth, min_depth,
        magnitude_distribution (dict: category -> count),
        daily_counts (dict: date_str -> count),
        tsunami_count, significant_count,
        top_locations (list of (place, count) tuples)
    """
    if not earthquakes:
        return {
            "total": 0,
            "avg_magnitude": 0,
            "max_magnitude": 0,
            "min_magnitude": 0,
            "avg_depth": 0,
            "max_depth": 0,
            "min_depth": 0,
            "magnitude_distribution": {},
            "daily_counts": {},
            "tsunami_count": 0,
            "significant_count": 0,
            "top_locations": [],
        }

    magnitudes = [e["magnitude"] for e in earthquakes if e["magnitude"] is not None]
    depths = [e["depth_km"] for e in earthquakes if e["depth_km"] is not None]

    # Magnitude distribution
    dist = {}
    for m in magnitudes:
        cat = magnitude_category(m)
        dist[cat] = dist.get(cat, 0) + 1

    # Daily counts
    daily = {}
    for e in earthquakes:
        if e["time_iso"]:
            try:
                day = dateparser.parse(e["time_iso"]).strftime("%Y-%m-%d")
                daily[day] = daily.get(day, 0) + 1
            except Exception:
                pass

    # Top locations (extract region from "X km N of City, Country" style)
    location_counts = {}
    for e in earthquakes:
        place = e.get("place") or "Unknown"
        # Use the part after " of " if present, else the whole string
        region = place.split(" of ")[-1].strip() if " of " in place else place
        location_counts[region] = location_counts.get(region, 0) + 1
    top_locations = sorted(location_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "total": len(earthquakes),
        "avg_magnitude": round(statistics.mean(magnitudes), 2) if magnitudes else 0,
        "max_magnitude": max(magnitudes) if magnitudes else 0,
        "min_magnitude": min(magnitudes) if magnitudes else 0,
        "avg_depth": round(statistics.mean(depths), 2) if depths else 0,
        "max_depth": round(max(depths), 2) if depths else 0,
        "min_depth": round(min(depths), 2) if depths else 0,
        "magnitude_distribution": dist,
        "daily_counts": dict(sorted(daily.items())),
        "tsunami_count": sum(1 for e in earthquakes if e.get("tsunami")),
        "significant_count": sum(1 for e in earthquakes if (e.get("sig") or 0) >= 600),
        "top_locations": top_locations,
    }
