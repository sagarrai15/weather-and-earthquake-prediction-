"""
app.py
Flask web application for earthquake detail and analysis.
"""

import logging
import os

from flask import Flask, render_template, request, jsonify
import earthquake_analyzer as ea

app = Flask(__name__)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Template filters
# ---------------------------------------------------------------------------

@app.template_filter("mag_badge")
def mag_badge_filter(mag):
    """Return a Bootstrap colour name based on magnitude."""
    if mag is None:
        return "secondary"
    if mag >= 7:
        return "danger"
    if mag >= 5:
        return "warning"
    if mag >= 4:
        return "info"
    return "primary"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    """Dashboard – list recent earthquakes with summary statistics."""
    days = int(request.args.get("days", 7))
    minmag = float(request.args.get("minmag", 2.5))
    limit = int(request.args.get("limit", 100))

    from datetime import datetime, timedelta, timezone

    endtime = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    starttime = (datetime.now(timezone.utc) - timedelta(days=days)).strftime(
        "%Y-%m-%d"
    )

    earthquakes = []
    error = None
    analysis = {}
    try:
        earthquakes = ea.fetch_earthquakes(
            starttime=starttime,
            endtime=endtime,
            minmagnitude=minmag,
            limit=limit,
        )
        analysis = ea.analyze_earthquakes(earthquakes)
    except Exception as exc:
        logger.exception("Failed to fetch earthquake data")
        error = "Could not retrieve earthquake data. Please try again later."

    # Attach magnitude category to each event for template colouring
    for eq in earthquakes:
        eq["mag_category"] = ea.magnitude_category(eq["magnitude"])
        eq["alert_class"] = ea.alert_label(eq.get("alert"))

    return render_template(
        "index.html",
        earthquakes=earthquakes,
        analysis=analysis,
        days=days,
        minmag=minmag,
        limit=limit,
        error=error,
    )


@app.route("/earthquake/<event_id>")
def detail(event_id):
    """Detailed view for a single earthquake event."""
    earthquake = None
    error = None
    try:
        earthquake = ea.fetch_earthquake_by_id(event_id)
        if earthquake:
            earthquake["mag_category"] = ea.magnitude_category(earthquake["magnitude"])
            earthquake["alert_class"] = ea.alert_label(earthquake.get("alert"))
    except Exception:
        logger.exception("Failed to fetch earthquake detail for %s", event_id)
        error = "Could not retrieve event data. Please try again later."

    return render_template("detail.html", earthquake=earthquake, error=error)


@app.route("/api/earthquakes")
def api_earthquakes():
    """JSON endpoint for earthquake list (used by the map)."""
    days = int(request.args.get("days", 7))
    minmag = float(request.args.get("minmag", 2.5))
    limit = int(request.args.get("limit", 100))

    from datetime import datetime, timedelta, timezone

    endtime = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    starttime = (datetime.now(timezone.utc) - timedelta(days=days)).strftime(
        "%Y-%m-%d"
    )
    try:
        earthquakes = ea.fetch_earthquakes(
            starttime=starttime,
            endtime=endtime,
            minmagnitude=minmag,
            limit=limit,
        )
        return jsonify({"status": "ok", "count": len(earthquakes), "data": earthquakes})
    except Exception:
        logger.exception("Failed to fetch earthquake data for API")
        return jsonify({"status": "error", "message": "Could not retrieve data"}), 500


if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug)
